#!/usr/bin/env python3
"""
Evaluation script for 1-min-ahead price predictions.

Assumes a JSONL file with columns:
- timestamp
- real_close          (actual price)
- crns_pred           (CHRONOS prediction)
- sari_pred           (SARIMAX prediction)
- model_selected      ("CHRONOS" or "SARIMAX")

Final prediction per row = prediction from the model in `model_selected`.

Metrics (computed on UNSORTED rows):
- RMSE, MAE, MAPE, Directional Accuracy

Plot (using SORTED timestamps):
- Real vs Predicted close price over time
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Hard-coded path
FILE_PATH = "/STATIC(ONLY_FOR_RESULT_REPRODUCIBILITY)/chronos_static/selection/s_output/model_selection.jsonl"   # change if needed


def load_data(path: str) -> pd.DataFrame:
    # Load as-is; DO NOT sort here
    df = pd.read_json(path, lines=True)

    # Decide final prediction based on model_selected
    df["final_pred"] = np.where(
        df["model_selected"] == "SARIMAX",
        df["sari_pred"],
        df["crns_pred"],
    )
    return df


def compute_metrics(df: pd.DataFrame):
    """
    Compute metrics on the ORIGINAL (unsorted) row order.
    """
    y_true = df["real_close"].to_numpy(dtype=float)
    y_pred = df["final_pred"].to_numpy(dtype=float)

    # Residual = real_close - final_pred
    residual = y_true - y_pred

    # RMSE
    rmse = np.sqrt(np.mean(residual ** 2))

    # MAE
    mae = np.mean(np.abs(residual))

    # MAPE (skip zeros in denominator)
    non_zero_mask = y_true != 0
    mape = np.mean(
        np.abs(residual[non_zero_mask] / y_true[non_zero_mask])
    ) * 100.0

    # Directional accuracy:
    # Compare sign(real_close_t - real_close_{t-1})
    # vs sign(final_pred_t - real_close_{t-1})
    prev_true = df["real_close"].shift(1)
    actual_dir = np.sign(df["real_close"] - prev_true)
    pred_dir = np.sign(df["final_pred"] - prev_true)

    valid_mask = prev_true.notna()
    dir_acc = (actual_dir[valid_mask] == pred_dir[valid_mask]).mean() * 100.0

    return rmse, mae, mape, dir_acc


def plot_series(df: pd.DataFrame, title: str = "Real vs Predicted Close Price"):
    """
    Plot using a TIME-SORTED copy of the data.
    """
    df_sorted = df.copy()
    df_sorted["timestamp"] = pd.to_datetime(df_sorted["timestamp"])
    df_sorted = df_sorted.sort_values("timestamp")

    plt.figure(figsize=(14, 5))
    plt.plot(df_sorted["timestamp"], df_sorted["real_close"], label="Real Close")
    plt.plot(df_sorted["timestamp"], df_sorted["final_pred"],
             label="Predicted (1-min ahead)", alpha=0.8)
    plt.xlabel("Time")
    plt.ylabel("Price")
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


def main():
    df = load_data(FILE_PATH)

    # Metrics on unsorted data
    rmse, mae, mape, dir_acc = compute_metrics(df)

    print("=== Evaluation Metrics (1-min ahead) ===")
    print(f"RMSE : {rmse:.4f}")
    print(f"MAE  : {mae:.4f}")
    print(f"MAPE : {mape:.2f}%")
    print(f"Dir Accuracy (up/down vs prev close): {dir_acc:.2f}%")

    # Plot on time-sorted copy
    plot_series(df)


if __name__ == "__main__":
    main()