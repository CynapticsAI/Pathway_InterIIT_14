import numpy as np
import pandas as pd

DEFAULT_COST = 0.0005

def apply_costs(strategy_ret, signal):
    turnover = signal.diff().abs().fillna(0.0)
    return strategy_ret - turnover * DEFAULT_COST

def finalize_strategy(ret, signal, cost):
    strat = signal.shift(1) * ret
    strat = strat - signal.diff().abs().fillna(0.0) * cost
    return strat

def to_daily_returns(minute_ret):
    minute_ret = minute_ret.dropna()
    log_ret = np.log1p(minute_ret)
    daily_log = log_ret.groupby(log_ret.index.date).sum()
    daily = np.expm1(daily_log)
    daily.index = pd.to_datetime(daily.index)
    return daily

def sharpe(daily):
    if daily.std() == 0:
        return -999
    return (daily.mean() / daily.std()) * np.sqrt(252)

def sortino(daily):
    downside = daily[daily < 0]
    if downside.std() == 0:
        return -999
    return (daily.mean() / downside.std()) * np.sqrt(252)

def max_drawdown(minute_ret):
    eq = (1 + minute_ret.fillna(0)).cumprod()
    peak = eq.cummax()
    return float((eq / peak - 1).min())
