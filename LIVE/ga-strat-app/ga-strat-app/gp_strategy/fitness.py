# fitness.py
"""
Improved fitness evaluation for GP trading strategies.

This version:
 - Prioritizes Sharpe ratio (most important)
 - Also rewards ROI
 - Penalizes very low exposure (anti-gambling/anti-artifact)
 - Penalizes too few trades (avoids inflated Sharpe from tiny samples)
 - Includes parsimony penalty
 - Produces clean, JSON-safe metrics
"""
import numpy as np
import math

def simulate_signal_series(signal_series, close_series):
    """
    Simple next-bar execution:
      - If signal is True and not in position: enter at next bar close
      - If signal is False and in position: exit at next bar close
    Returns: trade returns list, exposure time series
    """
    in_pos = False
    entry_price = None
    trades = []
    exposures = []

    n = len(signal_series)
    for i in range(n):
        s = bool(signal_series[i])

        if s and not in_pos:
            entry_price = float(close_series[i])
            in_pos = True
            exposures.append(1.0)
        elif (not s) and in_pos:
            exit_price = float(close_series[i])
            if entry_price and entry_price != 0:
                ret = (exit_price - entry_price) / entry_price
                trades.append(ret)
            in_pos = False
            entry_price = None
            exposures.append(0.0)
        else:
            exposures.append(1.0 if in_pos else 0.0)

    if in_pos and entry_price is not None:
        exit_price = float(close_series[-1])
        if entry_price != 0:
            ret = (exit_price - entry_price) / entry_price
            trades.append(ret)

    return trades, exposures

# Metrics
def calc_metrics(trades, exposures):
    metrics = {}
    trades = list(trades)
    exposures = np.array(exposures, dtype=float)

    # ROI
    metrics["roi"] = float(sum(trades)) if len(trades) else 0.0

    # Sharpe
    if len(trades) > 1:
        arr = np.array(trades, dtype=float)
        mean_ret = np.mean(arr)
        std_ret = np.std(arr, ddof=0)
        metrics["sharpe"] = float((mean_ret / std_ret) * math.sqrt(252)) if std_ret > 1e-12 else 0.0
    else:
        metrics["sharpe"] = 0.0

    # Sortino
    if len(trades):
        arr = np.array(trades)
        negs = arr[arr < 0]
        down_std = np.std(negs, ddof=0) if len(negs) else 0.0
        metrics["sortino"] = float((np.mean(arr) / down_std) * math.sqrt(252)) if down_std > 1e-12 else 0.0
    else:
        metrics["sortino"] = 0.0

    # Drawdown
    if len(trades):
        eq = np.cumprod([1.0] + [1.0 + r for r in trades])
        peak = np.maximum.accumulate(eq)
        dd = (eq - peak) / peak
        metrics["max_drawdown"] = float(np.min(dd))
        metrics["drawdown_duration"] = int((len(dd) - int(np.argmax(peak))))
    else:
        metrics["max_drawdown"] = 0.0
        metrics["drawdown_duration"] = 0

    # Exposure
    metrics["exposure"] = float(np.mean(exposures)) if len(exposures) else 0.0

    # Trade stats
    metrics["num_trades"] = int(len(trades))
    if len(trades):
        wins = sum(1 for r in trades if r > 0)
        metrics["win_rate"] = float(wins / len(trades))
        metrics["avg_trade_return"] = float(np.mean(trades))
        gross_win = sum(r for r in trades if r > 0)
        gross_loss = -sum(r for r in trades if r < 0)
        metrics["profit_factor"] = float(gross_win / gross_loss) if gross_loss > 0 else float('inf')
    else:
        metrics["win_rate"] = 0.0
        metrics["avg_trade_return"] = 0.0
        metrics["profit_factor"] = float('inf')

    return metrics


# Fitness
PARSIMONY_K = 0.001     # size penalty

def evaluate_individual(ind, tb, df_window):
    """Evaluate strategy on df_window (already preprocessed)."""

    try:
        func = tb.compile(expr=ind)
    except Exception:
        return -10.0, {"roi":0,"sharpe":0,"sortino":0,"max_drawdown":0,"drawdown_duration":0,
                       "exposure":0,"num_trades":0,"win_rate":0,"avg_trade_return":0,"profit_factor":0}

    signals = []
    closes = []

    for _, row in df_window.iterrows():
        try:
            args = [
                row["close_vec"],
                row["high_vec"],
                row["low_vec"],
                row["vol_vec"],
                float(row["ema5_scal"]),
                float(row["ema13_scal"]),
                float(row["ema50_scal"]),
                float(row["ema200_scal"]),
                float(row["rsi14_scal"]),
            ]
            val = func(*args)
            signals.append(bool(val))
        except Exception:
            signals.append(False)

        closes.append(float(row["close"]))

    trades, exposures = simulate_signal_series(signals, closes)
    metrics = calc_metrics(trades, exposures)

    sharpe = metrics["sharpe"]
    roi = metrics["roi"]
    exposure = metrics["exposure"]
    num_trades = metrics["num_trades"]
    max_drawdown = metrics["max_drawdown"]

    if max_drawdown < -0.20:
        return -1000.0, metrics

    fitness = (
        0.7 * sharpe +     
        0.3 * roi         
    )

    fitness += max_drawdown * 0.5 

    if exposure < 0.05:
        fitness -= (0.05 - exposure) * 5.0 

    if num_trades < 30:
        fitness -= (30 - num_trades) * 0.02

    # Parsimony penalty
    size = len(ind)
    fitness -= PARSIMONY_K * size

    return float(fitness), metrics
