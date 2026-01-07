import os, time, json, datetime, shutil
from datetime import timedelta
from pathlib import Path
from typing import List
import numpy as np
import torch
import pathway as pw
from chronos import Chronos2Pipeline
from transformers import AutoTokenizer, AutoModel
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import joblib

os.environ["TOKENIZERS_PARALLELISM"] = "false"

FINBERT_ID = "ProsusAI/finbert"
FREQ_FMT = "%Y-%m-%d %H:%M:%S%z"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
CKPT_DIR = "/app/chronos-2-finetuned/finetuned-ckpt"

TRAIN_INTERVAL_SEC = 600
NEW_TIMEFRAME = "1m"  # in minutes
PAST_LEN = 20
NUM_STEPS = 50
LR = 1e-5
BATCH_SIZE = 32
HORIZON = 10 

OHLC_TOPIC = "ohlc"
NEWS_TOPIC = "news"

KAFKA = {
    "bootstrap.servers": "kafka:9092",
    "group.id": "chronos_train",
    "session.timeout.ms": "6000",
}

SCALER_PATH = Path("artifacts/scaler.joblib")
PCA_PATH = Path("artifacts/pca.joblib")


pipeline = Chronos2Pipeline.from_pretrained(CKPT_DIR, device_map=DEVICE)


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
    PC_DIM = 768

COV_NAMES_BASE = ["open", "high", "low", "volume"]
NEWS_COLS = [f"news_pc_{i}" for i in range(PC_DIM)]

COV_ALL = COV_NAMES_BASE + NEWS_COLS

_last_train_ts = 0.0




def save_single_checkpoint(pipe, root_folder="chronos2_checkpoints"):
    """
    Deletes all old checkpoints inside root_folder and saves exactly one new checkpoint.
    """
    root = Path(root_folder)

    # delete old checkpoints
    if root.exists():
        for item in root.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
    else:
        root.mkdir(parents=True, exist_ok=True)

    # create new timestamped folder
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = root / ts
    out_dir.mkdir(parents=True, exist_ok=True)

    # save model
    pipe.save_pretrained(str(out_dir))

    # optional meta.json
    with open(out_dir / "meta.json", "w") as f:
        json.dump({"saved_at": ts}, f)

    print(f"\n✅ Saved new checkpoint to: {out_dir}\n")




def finbert_embed(texts: List[str]) -> np.ndarray:
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
        v = (
            out.pooler_output
            if getattr(out, "pooler_output", None) is not None
            else out.last_hidden_state[:, 0, :]
        )
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

    vols = np.log1p(vols)

    log_close = np.log(closes + 1e-12)
    ret = np.diff(log_close, prepend=log_close[0])

    
    news_txts = [t if isinstance(t, str) else "" for t in window_news_texts]
    embs = finbert_embed(news_txts)
    if len(embs) < len(news_txts):
        pad = np.zeros((len(news_txts) - len(embs), 768), dtype=np.float32)
        embs = np.vstack([embs, pad])
    pcs = news_pca.transform(embs) if news_pca is not None else embs

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
        "bootstrap.servers": "kafka:9092",
        "group.id": "stock_calculator_ticks",  # New group ID
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

ohlc_stream = ohlc_stream.with_columns(
    timestamp=ohlc_stream.timestamp
    symbol="TSLA",
)
news_stream = news_stream.with_columns(
    dt_utc=news_stream.dt_utc.dt.strptime(fmt=FREQ_FMT),
    symbol=news_stream.ticker,
)


joined = ohlc_stream.asof_join(
    news_stream,
    ohlc_stream.timestamp,
    news_stream.dt_utc,
    ohlc_stream.symbol == news_stream.symbol,
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


windowed = joined.groupby(pw.this.symbol).windowby(
    joined.timestamp,
    window=pw.temporal.sliding(
        duration=timedelta(minutes=120),
        hop=timedelta(minutes=1),
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



def _fit_latest_only(closes, opens, highs, lows, volumes, news_texts):
    global _last_train_ts, pipeline

    now = time.time()
    if (now - _last_train_ts) < TRAIN_INTERVAL_SEC:
        return None

    closes = tuple(closes)
    if len(closes) < PAST_LEN + 1:
        _last_train_ts = now
        return None

    _, ret_z, cov_z = build_features(
        closes,
        opens,
        highs,
        lows,
        volumes,
        news_texts,
    )

    target = torch.tensor(ret_z[-PAST_LEN:], dtype=torch.float32)
    cov = cov_z[-PAST_LEN:, :]

    cov_dict = {
        name: torch.tensor(cov[:, j], dtype=torch.float32)
        for j, name in enumerate(COV_ALL)
    }

    inputs = [{"target": target, "past_covariates": cov_dict}]

    pipeline = pipeline.fit(
        inputs=inputs,
        prediction_length=1,
        num_steps=NUM_STEPS,
        learning_rate=LR,
        batch_size=BATCH_SIZE,
        logging_steps=10,
    )

    save_single_checkpoint(pipeline, root_folder="chronos2_stream_ckpts_latest")
    _last_train_ts = now
    return None


train_table = windowed.select(
    windowed.symbol,
    windowed.windowStart,
    windowed.windowEnd,
    out=pw.apply(
        lambda c, o, h, l, v, n: _fit_latest_only(c, o, h, l, v, n),
        windowed.closes,
        windowed.opens,
        windowed.highs,
        windowed.lows,
        windowed.volumes,
        windowed.news_texts,
    ),
)

pw.io.csv.write(train_table, "/app/heartbeat/c_.csv")

pw.run(monitoring_level=pw.MonitoringLevel.ALL)