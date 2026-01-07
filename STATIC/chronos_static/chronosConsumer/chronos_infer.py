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

CKPT_ROOT = Path("/app/chronos2_stream_ckpts_latest/")
CKPT_DIR = Path("/app/chronos-2-finetuned/finetuned-ckpt")
RELOAD_EVERY_SEC = 60

SCALER_PATH = Path("artifacts/scaler.joblib")
PCA_PATH = Path("artifacts/pca.joblib")
N_PCS = 16  

OHLC_TOPIC = "ohlc"
TWEETS_TOPIC = "tweets"
REDDIT_TOPIC = "reddit"

KAFKA = {
    "bootstrap.servers": "kafka:9092",
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
    tweet_pca: PCA = joblib.load(PCA_PATH)
    PC_DIM = tweet_pca.n_components_
else:
    tweet_pca = None
    PC_DIM = 768  # raw FinBERT dim

COV_NAMES_BASE = ["open", "high", "low", "volume"]

TWEET_COLS = [f"tweet_pc_{i}" for i in range(PC_DIM)]
REDDIT_COLS = [f"reddit_pc_{i}" for i in range(PC_DIM)]

COV_ALL = COV_NAMES_BASE + TWEET_COLS + REDDIT_COLS


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
    window_texts,
    window_reddit_texts,
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

    # Tweets
    txts = [t if isinstance(t, str) else "" for t in window_texts]
    embs = finbert_embed(txts)
    if len(embs) < len(txts):
        pad = np.zeros((len(txts) - len(embs), 768), dtype=np.float32)
        embs = np.vstack([embs, pad])
    pcs = tweet_pca.transform(embs) if tweet_pca is not None else embs

    # Reddit
    rtxts = [t if isinstance(t, str) else "" for t in window_reddit_texts]
    remb = finbert_embed(rtxts)
    if len(remb) < len(rtxts):
        rpad = np.zeros((len(rtxts) - len(remb), 768), dtype=np.float32)
        remb = np.vstack([remb, rpad])
    rpcs = tweet_pca.transform(remb) if tweet_pca is not None else remb

    # Stack covariates: base OHLCV + tweet PCs + reddit PCs
    feats = np.column_stack([opens, highs, lows, vols, pcs, rpcs])

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


class TweetSchema(pw.Schema):
    Date: str
    Tweet: str
    Company_Name: str


class RedditSchema(pw.Schema):
    Date: str
    Post: str

ohlc_stream = pw.io.kafka.read(
    rdkafka_settings=KAFKA,
    topic=OHLC_TOPIC,
    schema=OhlcSchema,
    format="json",
)

tweets_stream = pw.io.kafka.read(
    rdkafka_settings=KAFKA,
    topic=TWEETS_TOPIC,
    schema=TweetSchema,
    format="json",
)

reddit_stream = pw.io.kafka.read(
    rdkafka_settings=KAFKA,
    topic=REDDIT_TOPIC,
    schema=RedditSchema,
    format="json",
)

# Parse timestamps & add symbol
ohlc_stream = ohlc_stream.with_columns(
    timestamp=ohlc_stream.timestamp.dt.strptime(fmt=FREQ_FMT),
    symbol="TSLA",
)

tweets_stream = tweets_stream.with_columns(
    Date=tweets_stream.Date.dt.strptime(fmt=FREQ_FMT),
    symbol="TSLA",
)

reddit_stream = reddit_stream.with_columns(
    Date=reddit_stream.Date.dt.strptime(fmt=FREQ_FMT),
    symbol="TSLA",
)

# -------------------- Join OHLC with TWEETS --------------------

joined = ohlc_stream.asof_join(
    tweets_stream,
    ohlc_stream.timestamp,
    tweets_stream.Date,
    ohlc_stream.symbol == tweets_stream.symbol,
    how=pw.JoinMode.LEFT,
    direction=pw.temporal.Direction.BACKWARD,
).select(
    *ohlc_stream,
    text=pw.coalesce(tweets_stream.Tweet, ""),
    tweet_published_at_opt=tweets_stream.Date,
)

joined = joined.asof_join(
    reddit_stream,
    joined.timestamp,
    reddit_stream.Date,
    joined.symbol == reddit_stream.symbol,
    how=pw.JoinMode.LEFT,
    direction=pw.temporal.Direction.BACKWARD,
).select(
    *joined,
    reddit_text=pw.coalesce(reddit_stream.Post, ""),
    reddit_published_at_opt=reddit_stream.Date,
)

epoch = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)

joined = joined.with_columns(
    tweet_published_at=pw.coalesce(joined.tweet_published_at_opt, epoch),
    reddit_published_at=pw.coalesce(joined.reddit_published_at_opt, epoch),
).without(
    joined.tweet_published_at_opt,
    joined.reddit_published_at_opt,
)

joined = joined.with_columns(
    text=pw.if_else(
        joined.timestamp - joined.tweet_published_at > timedelta(minutes=10),
        "",
        joined.text,
    ),
    reddit_text=pw.if_else(
        joined.timestamp - joined.reddit_published_at > timedelta(minutes=10),
        "",
        joined.reddit_text,
    ),
)

win = joined.groupby(pw.this.symbol).windowby(
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
    texts=pw.reducers.tuple(pw.this.text),
    reddit_texts=pw.reducers.tuple(pw.this.reddit_text),
)

def predict_window(closes, opens, highs, lows, volumes, texts, reddit_texts, horizon):
    closes = tuple(closes)
    if len(closes) < horizon + 5:
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
        texts,
        reddit_texts,
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
        lambda c, o, h, l, v, t, rt: predict_window(
            c,
            o,
            h,
            l,
            v,
            t,
            rt,
            HORIZON,
        ),
        pw.this.closes,
        pw.this.opens,
        pw.this.highs,
        pw.this.lows,
        pw.this.volumes,
        pw.this.texts,
        pw.this.reddit_texts,
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
