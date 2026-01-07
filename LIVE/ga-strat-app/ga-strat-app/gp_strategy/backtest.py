# backtest.py
import numpy as np

def signals_from_func(func, dfw):
    n = len(dfw)
    sig = np.zeros(n, dtype=bool)
    for i in range(n):
        try:
            out = func(
                dfw.loc[i,'close_vec'],
                float(dfw.loc[i,'ema5_scal']),
                float(dfw.loc[i,'ema13_scal']),
                float(dfw.loc[i,'ema50_scal']),
                float(dfw.loc[i,'ema200_scal']),
            )
            sig[i] = bool(out)
        except:
            sig[i] = False
    return sig

def simulate_trades(signals, prices):
    prices = np.asarray(prices)
    ret = np.zeros(len(prices))
    ret[1:] = (prices[1:] / prices[:-1]) - 1

    pos = np.zeros(len(prices))
    pos[1:] = signals[:-1].astype(float)

    pnl = pos * ret
    equity = 1 + np.cumsum(pnl)

    return {
        "per_bar_returns": pnl,
        "equity_curve": equity,
        "positions": pos,
        "prices": prices
    }
