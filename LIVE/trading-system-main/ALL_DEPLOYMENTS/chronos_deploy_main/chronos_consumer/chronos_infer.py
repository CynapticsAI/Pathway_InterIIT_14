import datetime
import time
import threading
import numpy as np
import pathway as pw
import torch
from datetime import timedelta
from pathlib import Path
from chronos import Chronos2Pipeline
from transformers import AutoTokenizer, AutoModel
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import joblib
import json

FINBERT_ID = "ProsusAI/finbert"
FREQ_FMT = "%Y-%m-%d %H:%M:%S%z"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
HORIZON = 10
NEW_TIMEFRAME = "10s"  # in minutes
CKPT_ROOT = Path("/app/chronos2_stream_ckpts_latest/")
CKPT_DIR = Path("/app/chronos-2-finetuned/finetuned-ckpt")
RELOAD_EVERY_SEC = 600

SCALER_PATH = Path("artifacts/scaler.joblib")
PCA_PATH = Path("artifacts/pca.joblib")
N_PCS = 16  

OHLC_TOPIC = "ohlc"
NEWS_TOPIC = "news"

KAFKA = {
    "bootstrap.servers": "kafka:9090",
    "group.id": "chronos_infer",
    "session.timeout.ms": "6000",
}


pipeline = Chronos2Pipeline.from_pretrained(str(CKPT_DIR), device_map=DEVICE)
_PIPELINE_LOCK = threading.Lock()
_current_ckpt = CKPT_DIR


fin_tok = AutoTokenizer.from_pretrained(FINBERT_ID)
fin_mdl = AutoModel.from_pretrained(FINBERT_ID).to(DEVICE).eval()


if SCALER_PATH.exists():
    z_scaler: StandardScaler = joblib.load(SCALER_PATH)
else:
    z_scaler = None

if PCA_PATH.exists():
    news_pca: PCA = joblib.load(PCA_PATH)
    PC_DIM = news_pca.n_components_
else:
    news_pca = None
    PC_DIM = 768  # raw FinBERT dim

COV_NAMES_BASE = ["open", "high", "low", "volume"]

NEWS_COLS = [f"news_pc_{i}" for i in range(PC_DIM)]

COV_ALL = COV_NAMES_BASE + NEWS_COLS


def _latest_finetuned_ckpt(root: Path) -> Path | None:
    cands = []
    if root.is_dir():
        for d in root.iterdir():
            if d.is_dir():
                p = d / "finetuned-ckpt"
                if p.is_dir():
                    cands.append(p)
    if not cands:
        return None
    return max(cands, key=lambda p: p.stat().st_mtime)


def _watch_and_reload():
    """Background thread: watches for new fine-tuned checkpoints and hot-reloads."""
    global pipeline, _current_ckpt
    while True:
        time.sleep(RELOAD_EVERY_SEC)
        try:
            latest = _latest_finetuned_ckpt(CKPT_ROOT)
            if latest is None:
                continue
            if latest.resolve() != _current_ckpt.resolve():
                new_pipe = Chronos2Pipeline.from_pretrained(str(latest), device_map=DEVICE)
                with _PIPELINE_LOCK:
                    pipeline = new_pipe
                    _current_ckpt = latest
        except Exception:
            # Don't kill the process if reloading fails once
            pass


def finbert_embed(texts):
    """Return L2-normalized FinBERT embeddings for a list of strings."""
    if len(texts) == 0:
        return np.zeros((0, 768), dtype=np.float32)
    with torch.no_grad():
        enc = fin_tok(
            texts,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors="pt",
        )
        enc = {k: v.to(DEVICE) for k, v in enc.items()}
        out = fin_mdl(**enc)
        if hasattr(out, "pooler_output") and out.pooler_output is not None:
            v = out.pooler_output
        else:
            v = out.last_hidden_state[:, 0, :]
        v = v / (v.norm(dim=1, keepdim=True) + 1e-8)
        return v.detach().cpu().float().numpy()


def build_features(
    window_closes,
    window_opens,
    window_highs,
    window_lows,
    window_vols,
    window_news_texts,
):
    closes = np.asarray(window_closes, dtype=np.float32)
    opens = np.asarray(window_opens, dtype=np.float32)
    highs = np.asarray(window_highs, dtype=np.float32)
    lows = np.asarray(window_lows, dtype=np.float32)
    vols = np.asarray(window_vols, dtype=np.float32)

    # Volume transform
    vols = np.log1p(vols)

    # Returns
    log_close = np.log(closes + 1e-12)
    ret = np.diff(log_close, prepend=log_close[0])

    # News
    news_txts = [t if isinstance(t, str) else "" for t in window_news_texts]
    embs = finbert_embed(news_txts)
    if len(embs) < len(news_txts):
        pad = np.zeros((len(news_txts) - len(embs), 768), dtype=np.float32)
        embs = np.vstack([embs, pad])
    pcs = news_pca.transform(embs) if news_pca is not None else embs

    # Stack covariates: base OHLCV + news PCs
    feats = np.column_stack([opens, highs, lows, vols, pcs])

    if z_scaler is not None:
        stack = np.column_stack([ret, feats]).astype(np.float32)
        stack = z_scaler.transform(stack)
        ret_z = stack[:, 0]
        feats_z = stack[:, 1:]
    else:
        ret_z = ret
        feats_z = feats

    return ret, ret_z, feats_z


class OhlcSchema(pw.Schema):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class NewsSchema(pw.Schema):
    dt_utc: str
    ticker: str
    source: str
    title: str
    url: str

class TickInputSchema(pw.Schema):
    s: str
    p: float
    t: int
    v: float  # Volume

ticks = pw.io.kafka.read(
    rdkafka_settings={
        "bootstrap.servers": "kafka:9090",
        "group.id": "stock_calculator_ticks_infer",  # New group ID
        "session.timeout.ms": "6000",
    },
    topic="stock_data",
    schema=TickInputSchema,
    format="json",
    autocommit_duration_ms=1000
)
ticks_processed = ticks.with_columns(
    symbol=ticks.s,
    timestamp=pw.this.t.dt.utc_from_timestamp("ms"),  # Convert int (ms) to datetime
    price=ticks.p,
    volume=ticks.v
).select(pw.this.symbol, pw.this.timestamp, pw.this.price, pw.this.volume).filter(pw.this.symbol == "BINANCE:BTCUSDT")
ohlc_bars = ticks_processed.windowby(
    ticks_processed.timestamp,
    window=pw.temporal.tumbling(duration=pw.Duration(NEW_TIMEFRAME)),
    behavior=pw.temporal.exactly_once_behavior(),  # 1-minute windows
    instance=ticks_processed.symbol
).reduce(
    symbol=pw.this._pw_instance,
    timestamp=pw.reducers.min(pw.this.timestamp),
    open=pw.reducers.argmin(pw.this.timestamp, pw.this.price),
    high=pw.reducers.max(pw.this.price),
    low=pw.reducers.min(pw.this.price),
    close=pw.reducers.argmax(pw.this.timestamp, pw.this.price),
    volume=pw.reducers.sum(pw.this.volume)
)
ohlc_stream = ohlc_bars.with_columns(
    return_val=pw.if_else(
        pw.this.open != 0,
        (pw.this.close - pw.this.open) / pw.this.open,
        0.0
    )
)

news_stream = pw.io.kafka.read(
    rdkafka_settings=KAFKA,
    topic=NEWS_TOPIC,
    schema=NewsSchema,
    format="json",
)



news_stream = news_stream.with_columns(
    dt_utc=news_stream.dt_utc.dt.strptime(fmt=FREQ_FMT),
)

# -------------------- Join OHLC with NEWS --------------------

joined = ohlc_stream.asof_join(
    news_stream,
    ohlc_stream.timestamp,
    news_stream.dt_utc,
    how=pw.JoinMode.LEFT,
    direction=pw.temporal.Direction.BACKWARD,
).select(
    *ohlc_stream,
    news_text=pw.coalesce(news_stream.title, ""),
    news_published_at_opt=news_stream.dt_utc,
)

epoch = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)

joined = joined.with_columns(
    news_published_at=pw.coalesce(joined.news_published_at_opt, epoch),
).without(
    joined.news_published_at_opt,
)

joined = joined.with_columns(
    news_text=pw.if_else(
        joined.timestamp - joined.news_published_at > timedelta(minutes=10),
        "",
        joined.news_text,
    ),
)

win = joined.groupby(pw.this.symbol).windowby(
    joined.timestamp,
    window=pw.temporal.sliding(
        duration=timedelta(minutes=1),
        hop=timedelta(seconds=10),
    ),
    instance=joined.symbol,
).reduce(
    symbol=pw.reducers.any(pw.this.symbol),
    windowStart=pw.this._pw_window_start,
    windowEnd=pw.this._pw_window_end,
    opens=pw.reducers.tuple(pw.this.open),
    highs=pw.reducers.tuple(pw.this.high),
    lows=pw.reducers.tuple(pw.this.low),
    closes=pw.reducers.tuple(pw.this.close),
    volumes=pw.reducers.tuple(pw.this.volume),
    news_texts=pw.reducers.tuple(pw.this.news_text),
)

def predict_window(closes, opens, highs, lows, volumes, news_texts, horizon):
    closes = tuple(closes)
    if len(closes) <  5:
        return json.dumps(
            {
                "ok": False,
                "msg": "too_short",
                "preds": [],
                "ckpt": str(_current_ckpt),
            }
        )

    _, ret_z, cov_z = build_features(
        closes,
        opens,
        highs,
        lows,
        volumes,
        news_texts,
    )

    with torch.no_grad():
        inputs = [
            {
                "target": torch.tensor(ret_z, dtype=torch.float32),
                "past_covariates": {
                    name: torch.tensor(cov_z[:, j], dtype=torch.float32)
                    for j, name in enumerate(COV_ALL)
                },
            }
        ]
        with _PIPELINE_LOCK:
            pipe = pipeline
            ckpt_tag = str(_current_ckpt)

        out = pipe.predict(inputs=inputs, prediction_length=horizon)[0]
        pred_ret_z = np.asarray(
            out["predictions"] if isinstance(out, dict) else out
        ).reshape(-1)

    if z_scaler is not None:
        dummy = np.zeros(
            (len(pred_ret_z), 1 + cov_z.shape[1]),
            dtype=np.float32,
        )
        dummy[:, 0] = pred_ret_z
        inv = z_scaler.inverse_transform(dummy)[:, 0]
        pred_ret = inv.astype(np.float32)
    else:
        pred_ret = pred_ret_z.astype(np.float32)

    last_log_close = float(np.log(float(closes[-1]) + 1e-12))
    pred_log_path = last_log_close + np.cumsum(pred_ret[:horizon])
    pred_close = np.exp(pred_log_path)

    return json.dumps(
        {
            "ok": True,
            "horizon": int(horizon),
            "preds": [float(x) for x in pred_close],
            "ckpt": ckpt_tag,
        }
    )

preds = win.select(
    win.symbol,
    windowStart=win.windowStart,
    windowEnd=win.windowEnd,
    preds_json=pw.apply(
        lambda c, o, h, l, v, n: predict_window(
            c,
            o,
            h,
            l,
            v,
            n,
            HORIZON,
        ),
        pw.this.closes,
        pw.this.opens,
        pw.this.highs,
        pw.this.lows,
        pw.this.volumes,
        pw.this.news_texts,
    ),
)

output_path = "/app/chronos_output/combinedStream.csv"
pw.io.csv.write(preds, output_path)
pw.io.kafka.write(
    preds,
    rdkafka_settings=KAFKA,
    topic_name="chronos_infer_preds",
    format="json",
)
t = threading.Thread(target=_watch_and_reload, daemon=True)
t.start()

pw.run()