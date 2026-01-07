import pandas as pd
import numpy as np

def compute_rsi(series: pd.Series, period: int) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period).mean()
    rs = avg_gain / (avg_loss + 1e-12)
    return 100 - (100 / (1 + rs))

def compute_vwap(df: pd.DataFrame) -> pd.Series:
    cum_pv = (df["Close"] * df["Volume"]).cumsum()
    cum_v = df["Volume"].cumsum()
    return cum_pv / (cum_v + 1e-12)

def compute_bollinger(df: pd.DataFrame, period: int, std_dev: float):
    ma = df["Close"].rolling(period, min_periods=period).mean()
    std = df["Close"].rolling(period, min_periods=period).std()
    upper = ma + std_dev * std
    lower = ma - std_dev * std
    return ma, upper, lower

def compute_donchian(df: pd.DataFrame, period: int):
    upper = df["High"].rolling(period, min_periods=period).max()
    lower = df["Low"].rolling(period, min_periods=period).min()
    return upper, lower
