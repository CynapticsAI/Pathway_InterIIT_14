import pandas as pd
import numpy as np

def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def rsi(series, period):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(span=period, adjust=False).mean()
    avg_loss = loss.ewm(span=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def make_rolling_list(arr, window):
    n = len(arr)
    out = []
    for i in range(n):
        start = max(0, i - window + 1)
        w = arr[start:i+1]
        if len(w) < window:
            pad = np.full(window - len(w), w[0])
            w = np.concatenate([pad, w])
        else:
            w = w[-window:]
        out.append(w.tolist())
    return out


def preprocess_minute_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Take a minute-ohlcv DataFrame and return the hourly, feature-rich
    DataFrame used by the GP engine.
    Expected columns (case-insensitive): timestamp, open, high, low, close, volume.
    """
    print("Preprocessing in-memory minute DataFrame for STVGP…")

    df = df.copy()
    df.columns = [c.lower() for c in df.columns]

    if "timestamp" not in df.columns:
        raise ValueError("Input data must contain a 'timestamp' column")

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    for col in ["open", "high", "low", "close", "volume"]:
        if col not in df.columns:
            raise ValueError(f"Input data must contain '{col}' column")
        df[col] = pd.to_numeric(df[col], errors="coerce")

    print("Resampling to hourly…")
    df = df.set_index("timestamp")
    df = df.resample("1H").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    })
    df = df.dropna(subset=["open", "high", "low", "close"]).reset_index()

    # Hyper-params
    EMA5 = 5
    EMA13 = 13
    EMA50 = 50
    EMA200 = 200
    RSI14 = 14
    VEC_LEN = 21  # 21 hours

    print("Computing scalar terminals…")
    df["ema5_scal"] = ema(df["close"], EMA5)
    df["ema13_scal"] = ema(df["close"], EMA13)
    df["ema50_scal"] = ema(df["close"], EMA50)
    df["ema200_scal"] = ema(df["close"], EMA200)
    df["rsi14_scal"] = rsi(df["close"], RSI14)
    df["close_scal"] = df["close"]

    df["small_ema_diff"] = df["ema5_scal"] - df["ema13_scal"]
    df["big_ema_diff"] = df["ema50_scal"] - df["ema200_scal"]

    print("Computing vector terminals…")
    df["close_vec"] = make_rolling_list(df["close"].values,  VEC_LEN)
    df["high_vec"]  = make_rolling_list(df["high"].values,   VEC_LEN)
    df["low_vec"]   = make_rolling_list(df["low"].values,    VEC_LEN)
    df["vol_vec"]   = make_rolling_list(df["volume"].values, VEC_LEN)

    warmup = max(EMA200, RSI14, VEC_LEN)
    df = df.iloc[warmup:].reset_index(drop=True)

    df = df.dropna().reset_index(drop=True)
    print(f"Preprocessing complete (rows={len(df)})")
    return df

def preprocess_for_stvgp(csv_path, output_csv="stvgp_ready_hourly.csv"):
    """
    Legacy helper: read CSV from disk, preprocess, and save.
    """
    print("Loading minute-wise CSV…")
    df = pd.read_csv(csv_path)
    df_prep = preprocess_minute_df(df)
    df_prep.to_csv(output_csv, index=False)
    print(f"Saved {output_csv} (rows={len(df_prep)})")
    return df_prep


if __name__ == "__main__":
    preprocess_for_stvgp("minute_ohlcv.csv", "stvgp_ready_hourly.csv")
