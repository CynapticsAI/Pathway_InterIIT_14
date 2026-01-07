import argparse, ast, json, os
from typing import List, Tuple, Dict

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from pandas.tseries.frequencies import to_offset
import torch
from chronos import Chronos2Pipeline
from tqdm import tqdm

def _lower_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    return df

def mae(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    return float(np.mean(np.abs(y - p)))

def rmse(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    return float(np.sqrt(np.mean((y - p) ** 2)))

def mape(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    eps = 1e-8
    return float(np.mean(np.abs((y - p) / np.maximum(np.abs(y), eps))) * 100.0)

def directional_accuracy(true_vals, pred_vals, anchor_vals):
    """
    Directional accuracy:
        sign(y_true - anchor) == sign(y_pred - anchor)
    """
    y = np.asarray(true_vals, dtype=float)
    p = np.asarray(pred_vals, dtype=float)
    a = np.asarray(anchor_vals, dtype=float)
    if y.size == 0:
        return float("nan")
    true_dir = np.sign(y - a)
    pred_dir = np.sign(p - a)
    correct = (true_dir == pred_dir).astype(float)
    return float(correct.mean())

class ZScaler:
    def __init__(self):
        self.mu: Dict[str, float] = {}
        self.sd: Dict[str, float] = {}
    def fit(self, df: pd.DataFrame, cols: List[str]):
        for c in cols:
            x = df[c].astype(float).to_numpy()
            self.mu[c] = float(np.nanmean(x))
            s = float(np.nanstd(x))
            self.sd[c] = s if s > 1e-12 else 1.0
    def transform(self, df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
        out = df.copy()
        for c in cols:
            out[c] = (out[c].astype(float) - self.mu[c]) / self.sd[c]
        return out
    def inverse(self, arr: np.ndarray, col: str) -> np.ndarray:
        return arr.astype(float) * self.sd[col] + self.mu[col]

def to_dict_of_tensors(series_df: pd.DataFrame, cols: List[str]) -> dict:
    return {
        c: torch.tensor(series_df[c].to_numpy(dtype=np.float32), dtype=torch.float32)
        for c in cols
    }

def load_ohlcv(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = _lower_cols(df)
    dt = next((c for c in ["timestamp","date","datetime","time"] if c in df.columns), None)
    if dt is None:
        raise ValueError("Missing datetime in OHLCV.")
    df["timestamp"] = pd.to_datetime(df[dt])

    ren = {}
    for c in ["open","high","low","close","volume"]:
        if c not in df.columns:
            for alt in [f"{c}_price", c.upper(), c.capitalize()]:
                if alt in df.columns:
                    ren[alt] = c
                    break
            if c not in ren.values():
                raise ValueError(f"Missing column: {c}")
    if ren:
        df = df.rename(columns=ren)

    keep = ["timestamp","open","high","low","close","volume"]
    return (
        df[keep]
        .sort_values("timestamp")
        .drop_duplicates(subset=["timestamp"])
        .reset_index(drop=True)
    )

def _parse_embedding_cell(val):
    if isinstance(val, (list, np.ndarray)):
        return np.array(val, dtype=float)
    if isinstance(val, str):
        s = val.strip()
        try:
            return np.array(ast.literal_eval(s), dtype=float)
        except Exception:
            try:
                return np.array(json.loads(s), dtype=float)
            except Exception:
                return None
    return None

def load_tweets(csv_path: str) -> Tuple[pd.DataFrame, List[str]]:
    df = pd.read_csv(csv_path)
    df = _lower_cols(df)
    dt = next((c for c in ["timestamp","created_at","datetime","date","time"] if c in df.columns), None)
    if dt is None:
        raise ValueError("Missing datetime in tweets.")
    df["timestamp"] = pd.to_datetime(df[dt])

    emb_cols = [c for c in df.columns if c.startswith("emb_") or c.startswith("embedding_")]
    if not emb_cols:
        if "embedding" in df.columns:
            vecs = df["embedding"].apply(_parse_embedding_cell)
            nonnull = vecs.dropna()
            d = int(nonnull.map(len).max() if len(nonnull) else 0)
            if d == 0:
                raise ValueError("Unparsable 'embedding' column.")
            arr = np.vstack([v if v is not None else np.zeros(d) for v in vecs])
            emb_cols = [f"emb_{i}" for i in range(d)]
            df = pd.concat(
                [df, pd.DataFrame(arr, columns=emb_cols, index=df.index)],
                axis=1
            )
        else:
            raise ValueError("No FINBERT embeddings found.")

    keep = ["timestamp"] + emb_cols
    if "text" in df.columns:
        keep.append("text")

    return (
        df[keep]
        .sort_values("timestamp")
        .reset_index(drop=True),
        emb_cols,
    )

def aggregate_tweets_to_freq(tweets_df: pd.DataFrame, emb_cols: List[str], freq: str) -> pd.DataFrame:
    df = tweets_df.copy()
    df["bucket"] = df["timestamp"].dt.floor(freq)
    emb_agg = df.groupby("bucket")[emb_cols].mean()
    counts = df.groupby("bucket").size().rename("tweet_count")
    out = pd.concat([emb_agg, counts], axis=1).reset_index().rename(columns={"bucket":"timestamp"})
    return out

def enforce_regular_frequency(df: pd.DataFrame, freq: str, target_col: str = "close") -> pd.DataFrame:
    df = df.copy().set_index("timestamp")
    full_idx = pd.date_range(df.index.min(), df.index.max(), freq=freq)
    df = df.reindex(full_idx)

    cols = df.columns.tolist()
    price_cols = [c for c in ["open","high","low","close"] if c in cols]
    vol_cols   = [c for c in ["volume"] if c in cols]
    tweet_cols = [
        c for c in cols
        if c.startswith(("emb_","embedding_","tweet_pc_")) or c == "tweet_count"
    ]

    if target_col in df.columns:
        df[target_col] = df[target_col].ffill()
    for c in price_cols:
        df[c] = df[c].ffill()
    for c in ["open","high","low"]:
        if c in df.columns:
            df[c] = df[c].fillna(df[target_col])
    for c in vol_cols:
        df[c] = df[c].fillna(0.0)
    for c in tweet_cols:
        df[c] = df[c].fillna(0.0)

    return df.reset_index().rename(columns={"index":"timestamp"})

# PCA for tweet embeddings 
def pca_fit_transform(train_df: pd.DataFrame,
                      other_df: pd.DataFrame,
                      emb_cols: List[str],
                      n_components: int = 16):
    scaler = StandardScaler()
    pca = PCA(n_components=n_components, random_state=42)

    X_tr = train_df[emb_cols].fillna(0.0).values
    Z_tr = pca.fit_transform(scaler.fit_transform(X_tr))

    X_ot = other_df[emb_cols].fillna(0.0).values
    Z_ot = pca.transform(scaler.transform(X_ot))

    pc_cols = [f"tweet_pc_{i}" for i in range(n_components)]

    tr_out = pd.concat(
        [train_df.drop(columns=emb_cols).reset_index(drop=True),
         pd.DataFrame(Z_tr, columns=pc_cols)],
        axis=1
    )
    ot_out = pd.concat(
        [other_df.drop(columns=emb_cols).reset_index(drop=True),
         pd.DataFrame(Z_ot, columns=pc_cols)],
        axis=1
    )

    return tr_out, ot_out, pc_cols

# Main 
def main():
    os.environ.setdefault("PYTHONUNBUFFERED", "1")

    ap = argparse.ArgumentParser()
    ap.add_argument("--ohlcv", default = '../ohlcProducer/data_TSLA_sorted.csv')
    ap.add_argument("--tweets", default = 'chronos_output/embedded_out.csv')
    ap.add_argument("--freq", default="T")  # 1-minute default
    ap.add_argument("--pca_dims", type=int, default=16)
    ap.add_argument("--model_path", default="s3://autogluon/chronos-2")
    ap.add_argument("--num_steps", type=int, default=50, help="Fine-tune steps.")
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--batch_size", type=int, default=32)
    ap.add_argument("--teacher_forcing", action="store_true", default= True)
    ap.add_argument("--ret_clip", type=float, default=0.02)
    ap.add_argument("--stride", type=int, default=1)
    ap.add_argument("--horizon", type=int, default=5)
    ap.add_argument("--test_hours", type=int, default=3,
                    help="Length of final test window in hours (default: last 3h).")
    args = ap.parse_args()

    step_offset = to_offset(args.freq)

    # 1) Load + align
    ohlcv = load_ohlcv(args.ohlcv)
    tweets, emb_cols = load_tweets(args.tweets)

    ohlcv["timestamp"] = pd.to_datetime(ohlcv["timestamp"], utc=True).dt.tz_convert(None)
    tweets["timestamp"] = pd.to_datetime(tweets["timestamp"], utc=True).dt.tz_convert(None)

    tweets_agg = aggregate_tweets_to_freq(tweets, emb_cols, args.freq)
    # Leak-safe shift: tweets at time t affect next step.
    tweets_agg["timestamp"] = tweets_agg["timestamp"] + step_offset

    df = pd.merge(ohlcv, tweets_agg, on="timestamp", how="left")
    for c in emb_cols:
        if c in df.columns:
            df[c] = df[c].fillna(0.0)
    if "tweet_count" in df.columns:
        df["tweet_count"] = df["tweet_count"].fillna(0.0)

    df = df.sort_values("timestamp").reset_index(drop=True)
    df = enforce_regular_frequency(df, freq=args.freq)

    # 2) Target as log returns
    df["log_close"] = np.log(df["close"].astype(float))
    df["ret"] = df["log_close"].diff()

    # 3) Train / test split:
    max_ts = df["timestamp"].max()
    test_start_ts = max_ts - pd.Timedelta(hours=args.test_hours)

    if test_start_ts <= df["timestamp"].min():
        raise ValueError("Not enough history before the last test_hours for training.")

    # index of first test row
    split_idx = int(np.where(df["timestamp"] >= test_start_ts)[0][0])

    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()

    # Drop first NaN ret from train
    train_df = train_df.iloc[1:].reset_index(drop=True)
    test_df = test_df.reset_index(drop=True)

    if len(test_df) == 0:
        raise ValueError("Empty test window; check test_hours vs data range.")

    # 4) PCA over tweet embeddings (fit on train only)
    if emb_cols:
        tr_p, te_p, pc_cols = pca_fit_transform(train_df, test_df, emb_cols,
                                                n_components=args.pca_dims)
        train_df, test_df = tr_p, te_p
    else:
        pc_cols = []

    cov_cols = ["open","high","low","volume"] + pc_cols + \
               (["tweet_count"] if "tweet_count" in train_df.columns else [])

    # Log1p for volume
    if "volume" in cov_cols:
        for dfx in [train_df, test_df]:
            dfx["volume"] = np.log1p(dfx["volume"].astype(float))

    # 5) Standardize ret + covariates on train
    scaler = ZScaler()
    scaler.fit(train_df, ["ret"] + cov_cols)
    train_df = scaler.transform(train_df, ["ret"] + cov_cols)
    test_df = scaler.transform(test_df, ["ret"] + cov_cols)

    # True (unscaled) rets for test (for state updates)
    true_unscaled_ret = scaler.inverse(
        test_df["ret"].to_numpy(dtype=float),
        "ret"
    )

    # 6) Load + fine-tune Chronos-2 on full training window
    device_map = "cuda" if torch.cuda.is_available() else "cpu"
    pipeline = Chronos2Pipeline.from_pretrained(args.model_path, device_map=device_map)

    ctx_target = train_df["ret"].to_numpy(dtype=np.float32)
    ctx_cov_df = train_df[["timestamp"] + cov_cols].copy().reset_index(drop=True)

    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    finetuned = pipeline.fit(
        inputs=[{
            "target": torch.tensor(ctx_target, dtype=torch.float32),
            "past_covariates": to_dict_of_tensors(ctx_cov_df, cov_cols),
        }],
        prediction_length=1,
        num_steps=args.num_steps,
        learning_rate=args.lr,
        batch_size=args.batch_size,
        logging_steps=10,
    )

    # 7) Rolling multi-step forecasting (stride = 1) on last 3h
    k = max(1, args.stride)
    H = max(1, args.horizon)
    T = len(test_df)

    rows = []

    # Helper: global df with original closes for ground truth
    full_close = df.set_index("timestamp")["close"]

    pbar = tqdm(
        range(T),
        desc=f"Stride={k} multi-H={H} (teacher_forcing={args.teacher_forcing})",
        unit="step"
    )

    for t in pbar:
        if t % k == 0:
            # Effective horizon (avoid running past end)
            H_eff = min(H, T - t)

            # Future covariates for next H_eff steps
            fut_cov = test_df.iloc[t:t+H_eff][cov_cols]

            # Context for Chronos
            ctx = {
                "target": torch.tensor(ctx_target, dtype=torch.float32),
                "past_covariates": to_dict_of_tensors(ctx_cov_df, cov_cols),
            }

            pred_inputs = [{
                **ctx,
                "future_covariates": to_dict_of_tensors(fut_cov, cov_cols),
            }]

            with torch.no_grad():
                out = finetuned.predict(
                    inputs=pred_inputs,
                    prediction_length=H_eff
                )[0]

            pred_scaled = np.asarray(
                out["predictions"] if isinstance(out, dict) else out
            ).reshape(-1)

            pred_unscaled = scaler.inverse(pred_scaled, "ret").astype(float)
            pred_unscaled = np.clip(pred_unscaled, -args.ret_clip, args.ret_clip)

            # Anchor: last observed close *before* the first predicted step
            # In this loop, test_df[t] corresponds to the first predicted step (t+1 relative to anchor),
            # so anchor is:
            if t == 0:
                # Anchor is the final train point
                anchor_ts = df.iloc[split_idx - 1]["timestamp"]
            else:
                # Anchor is previous test step
                anchor_ts = test_df.iloc[t - 1]["timestamp"]

            anchor_close = float(full_close.loc[anchor_ts])

            # Construct forecasted closes relative to anchor_close
            cumsums = np.cumsum(pred_unscaled)        # returns from anchor
            pred_closes = np.exp(np.log(anchor_close) + cumsums)

            # Store H_eff horizons
            for h in range(H_eff):
                target_ts = test_df.iloc[t + h]["timestamp"]
                true_close = float(full_close.loc[target_ts])
                rows.append({
                    "anchor_timestamp": anchor_ts,
                    "timestamp": target_ts,
                    "horizon": h + 1,
                    "anchor_close": float(anchor_close),
                    "y_true_close": true_close,
                    "y_pred_close": float(pred_closes[h]),
                    "is_model_pred": 1,
                })

            # State update for next context step:
            state_ret = (
                true_unscaled_ret[t]
                if args.teacher_forcing else float(pred_unscaled[0])
            )

            used_scaled = (state_ret - scaler.mu["ret"]) / scaler.sd["ret"]
            ctx_target = np.concatenate(
                [ctx_target, np.array([used_scaled], dtype=np.float32)],
                axis=0
            )

            add_row = test_df.iloc[[t]][cov_cols].copy()
            add_row.insert(0, "timestamp", test_df.iloc[t]["timestamp"])
            ctx_cov_df = pd.concat([ctx_cov_df, add_row], ignore_index=True)

        else:
            # Between anchors: fast-forward using TRUE returns
            state_ret = true_unscaled_ret[t]
            used_scaled = (state_ret - scaler.mu["ret"]) / scaler.sd["ret"]
            ctx_target = np.concatenate(
                [ctx_target, np.array([used_scaled], dtype=np.float32)],
                axis=0
            )

            add_row = test_df.iloc[[t]][cov_cols].copy()
            add_row.insert(0, "timestamp", test_df.iloc[t]["timestamp"])
            ctx_cov_df = pd.concat([ctx_cov_df, add_row], ignore_index=True)

        if (t & 511) == 0:
            pbar.set_postfix(anchor_preds=len([1 for r in rows if r["horizon"] == 1]))

    # 8) Save preds + metrics
    pred_df = pd.DataFrame(rows).sort_values(
        ["anchor_timestamp", "horizon"]
    ).reset_index(drop=True)

    out_csv = f"preds_intraday_chronos2_stride_{k}_H{H}_last{args.test_hours}h.csv"
    pred_df.to_csv(out_csv, index=False)

    eval_df = pred_df[pred_df.get("is_model_pred", 1) == 1].copy()

    # Overall regression metrics
    overall = {
        "MAE": mae(eval_df["y_true_close"], eval_df["y_pred_close"]),
        "RMSE": rmse(eval_df["y_true_close"], eval_df["y_pred_close"]),
        "MAPE_%": mape(eval_df["y_true_close"], eval_df["y_pred_close"]),
        "n_eval": int(len(eval_df)),
    }

    # Overall directional accuracy
    overall["Directional_Accuracy"] = directional_accuracy(
        eval_df["y_true_close"],
        eval_df["y_pred_close"],
        eval_df["anchor_close"],
    )

    # Per-horizon
    per_h = {}
    for h, g in eval_df.groupby("horizon"):
        y = g["y_true_close"]
        p = g["y_pred_close"]
        a = g["anchor_close"]
        per_h[int(h)] = {
            "MAE": mae(y, p),
            "RMSE": rmse(y, p),
            "MAPE_%": mape(y, p),
            "Directional_Accuracy": directional_accuracy(y, p, a),
            "n": int(len(g)),
        }

    metrics = {
        "overall": overall,
        "per_horizon": per_h,
        "device_map": device_map,
        "pca_dims": int(len([c for c in test_df.columns if str(c).startswith("tweet_pc_")])),
        "freq": args.freq,
        "teacher_forcing": bool(args.teacher_forcing),
        "ret_clip": float(args.ret_clip),
        "stride": int(k),
        "horizon": int(H),
        "test_hours": int(args.test_hours),
        "notes": (
            "Train on all history before last test_hours; "
            "evaluate only on final test_hours with stride=1; "
            "DA = sign(y_true - anchor_close) == sign(y_pred - anchor_close)."
        ),
    }

    with open(
        f"metrics_intraday_chronos2_stride_{k}_H{H}_last{args.test_hours}h.json",
        "w"
    ) as f:
        json.dump(metrics, f, indent=2)

    print(out_csv)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
