"""
Public API for the GP strategy engine.

Key function:
    run_gp_strategy(data, out_dir="stvgp_out")

- `data` can be:
    * a string path to a minute OHLCV CSV, OR
    * a list of dicts, OR
    * a dict of column -> list (JSON from FastAPI).

Returns:
    {
      "raw_results": [...],      # as returned by GP engine
      "strategies": [...],       # with human_readable strings
    }
"""
from typing import Union, Sequence, Mapping, Any
import os

import pandas as pd

from .preprocess_stvgp import preprocess_minute_df
from .gp_engine import run_evolution_df
from .translate_strategies import translate_results_in_memory


def _data_to_dataframe(data: Union[str, Sequence[Mapping[str, Any]], Mapping[str, Sequence[Any]]]) -> pd.DataFrame:
    """
    Helper: convert various input formats into a minute-wise DataFrame.
    """
    if isinstance(data, str):
        # path to CSV
        df = pd.read_csv(data)
        return df

    # list[dict] or dict of lists
    df = pd.DataFrame(data)
    return df


def run_gp_strategy(data, out_dir: str = "stvgp_out"):
    """
    High-level entrypoint used by FastAPI.

    Example (JSON body):
    {
        "bars": [
            {"timestamp": "...", "open": ..., "high": ..., "low": ..., "close": ..., "volume": ...},
            ...
        ]
    }
    Then you would call:
        run_gp_strategy(body["bars"])
    """
    os.makedirs(out_dir, exist_ok=True)

    df_minute = _data_to_dataframe(data)
    df_prep = preprocess_minute_df(df_minute)

    raw_results = run_evolution_df(df_prep, out_dir)
    strategies = translate_results_in_memory(raw_results)

    return {
        "raw_results": raw_results,
        "strategies": strategies,
    }
