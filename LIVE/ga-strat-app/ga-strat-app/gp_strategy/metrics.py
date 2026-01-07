import numpy as np

def roi(ec):
    return float(ec[-1] / ec[0] - 1)

def annual_factor(hours=6.5, days=252):
    return np.sqrt(hours * days)

def sharpe(r, hours=6.5):
    if len(r)<2: return 0.0
    m, s = np.mean(r), np.std(r)
    if s==0: return 0.0
    return float((m/s) * annual_factor(hours))

def sortino(r, hours=6.5):
    neg = r[r<0]
    if len(neg)==0: return float("inf")
    d = np.std(neg)
    if d==0: return float("inf")
    m = np.mean(r)
    return float((m/d) * annual_factor(hours))

def max_drawdown(ec):
    peak = np.maximum.accumulate(ec)
    dd = (ec - peak) / peak
    mdd = float(np.min(dd))
    trough = int(np.argmin(dd))
    peak_idx = np.argmax(ec[:trough+1])
    dur = trough - peak_idx
    return mdd, dur

def extract_trades(pos, prices):
    trades=[]
    i=0; n=len(prices)
    while i<n:
        if pos[i]>0:
            j=i+1
            while j<n and pos[j]>0: j+=1
            entry, exitp = prices[i], prices[j] if j<n else prices[-1]
            trades.append((exitp/entry)-1)
            i=j
        else:
            i+=1
    return np.array(trades)

def profit_factor(trades):
    if len(trades)==0: return 0.0
    wins = trades[trades>0].sum()
    losses = -trades[trades<0].sum()
    if losses==0:
        return float("inf") if wins>0 else 0.0
    return float(wins/losses)

def compute_metrics(sim):
    ec = sim["equity_curve"]
    r  = sim["per_bar_returns"]
    pos= sim["positions"]
    prices= sim["prices"]

    metrics={}
    metrics["roi"] = roi(ec)
    metrics["sharpe"] = sharpe(r)
    metrics["sortino"] = sortino(r)
    mdd, dur = max_drawdown(ec)
    metrics["max_drawdown"]=mdd
    metrics["drawdown_duration"]=dur
    metrics["exposure"]=float(np.mean(pos))

    trades = extract_trades(pos, prices)
    metrics["num_trades"]=len(trades)
    metrics["win_rate"]=float((trades>0).mean()) if len(trades)>0 else 0.0
    metrics["avg_trade_return"]=float(np.mean(trades)) if len(trades)>0 else 0.0
    metrics["profit_factor"]=profit_factor(trades)

    return metrics
