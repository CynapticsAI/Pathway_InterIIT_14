import pandas as pd
from .engine.ga_optimizer import genetic_optimize


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df = df.rename(columns={
        "timestamp": "Date",
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume",
    })
    df = df.set_index("Date").sort_index()

    full = pd.date_range(df.index.min(), df.index.max(), freq="1min")
    return df.reindex(full).ffill()


def run_ga_strategy(
    data_path: str,
    train_months: int = 6,
    valid_months: int = 1,
):
    """
    Run GA parameter optimisation for existing strategies.

    Parameters
    ----------
    data_path : str
        Path to 1-minute OHLCV CSV.
    train_months : int
        Length of training window.
    valid_months : int
        Length of validation window.

    Returns
    -------
    dict
        Whatever `genetic_optimize` returns
        (e.g. {strategy_name: (score, params, metrics), ...})
    """
    df = load_data(data_path)

    train_end = df.index.max() - pd.DateOffset(months=valid_months)
    train_start = train_end - pd.DateOffset(months=train_months)

    df_train = df[(df.index >= train_start) & (df.index < train_end)]
    df_valid = df[df.index >= train_end]

    results = genetic_optimize(df_train, df_valid)
    return results


if __name__ == "__main__":
    data_path = "data/data_TSLA_sorted_.csv"
    res = run_ga_strategy(data_path)

    print("\nFINAL RESULTS")
    for strat, (score, params, metrics) in res.items():
        print(f"\nStrategy: {strat}")
        print(f"  Best Params: {params}")
        print(f"  Train: {metrics['train']}")
        print(f"  Valid: {metrics['valid']}")
