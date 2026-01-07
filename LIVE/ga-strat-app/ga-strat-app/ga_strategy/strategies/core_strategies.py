import numpy as np
import pandas as pd
from ..indicators.basic_indicators import compute_rsi, compute_vwap, compute_bollinger, compute_donchian

def forward_fill(signal):
    return signal.replace(0.0, np.nan).ffill().fillna(0.0)

def run_rsi(df, params, cost, finalize_strategy_fn):
    per = int(params["rsi_period"])
    os = float(params["oversold_level"])
    ob = float(params["overbought_level"])

    rsi = compute_rsi(df["Close"], per)
    signal = pd.Series(0.0, index=df.index)
    signal[rsi < os] = 1.0
    signal[rsi > ob] = -1.0

    signal = forward_fill(signal)
    ret = df["Close"].pct_change()
    return finalize_strategy_fn(ret, signal, cost), signal

def run_bollinger(df, params, cost, finalize_strategy_fn):
    period = int(params["bb_period"])
    dev = float(params["bb_std_dev"])

    ma, upper, lower = compute_bollinger(df, period, dev)
    signal = pd.Series(0.0, index=df.index)
    signal[df["Close"] < lower] = 1.0
    signal[df["Close"] > upper] = -1.0

    signal = forward_fill(signal)
    ret = df["Close"].pct_change()
    return finalize_strategy_fn(ret, signal, cost), signal

def run_donchian(df, params, cost, finalize_strategy_fn):
    period = int(params["channel_period"])
    upper, lower = compute_donchian(df, period)
    signal = pd.Series(0.0, index=df.index)
    signal[df["Close"] > upper] = 1.0
    signal[df["Close"] < lower] = -1.0

    signal = forward_fill(signal)
    ret = df["Close"].pct_change()
    return finalize_strategy_fn(ret, signal, cost), signal

def run_vwap(df, params, cost, finalize_strategy_fn):
    vw = int(params["vwap_window"])
    zt = float(params["z_threshold"])
    trend_ma = int(params["trend_ma"])

    vwap = compute_vwap(df)
    diff = df["Close"] - vwap
    std = diff.rolling(vw).std()
    z = diff / (std + 1e-12)

    trend = df["Close"].rolling(trend_ma).mean()

    signal = pd.Series(0.0, index=df.index)
    signal[(z < -zt) & (df["Close"] > trend)] = 1.0
    signal[(z > zt) & (df["Close"] < trend)] = -1.0

    signal = forward_fill(signal)
    ret = df["Close"].pct_change()
    return finalize_strategy_fn(ret, signal, cost), signal
