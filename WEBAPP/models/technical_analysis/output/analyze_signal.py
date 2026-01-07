import pandas as pd
import json
import matplotlib.pyplot as plt
import numpy as np

SIGNALS_JSONL = "../output/signal.jsonl"
signals = []

# --- ⬇️ NEW LIST OF VALID SIGNALS ⬇️ ---
VALID_RECOMMENDATIONS = ["BUY", "SELL", "HOLD", "STRONG BUY", "STRONG SELL"]

print(f"Loading signals from {SIGNALS_JSONL}...")
try:
    with open(SIGNALS_JSONL, 'r') as f:
        for line in f:
            data = json.loads(line)
            if 'signal' in data and data['signal']:
                signal_data = data['signal']

                # --- ⬇️ THIS IS THE FIX ⬇️ ---
                # Only analyze signals that are NOT errors
                if signal_data.get('recommendation') in VALID_RECOMMENDATIONS:
                    if 'combined_signal' in signal_data:
                        signals.append(signal_data['combined_signal'])

    if not signals:
        print("No valid signals (BUY/SELL/HOLD) were found in the file.")
        print("Please re-run your main script (the pathway one) to generate signals.")
        exit()

    print(f"Analyzed {len(signals)} VALID signals (ignored errors).")

    # Convert to a Pandas Series for easy stats
    sig_series = pd.Series(signals)

    print("\n--- Signal Distribution Statistics (Cleaned) ---")
    print(sig_series.describe(percentiles=[0.01, 0.05, 0.1, 0.20, 0.5, 0.80, 0.9, 0.95, 0.99]))

    # --- Plot a histogram ---
    print("\nGenerating histogram of signal values...")
    plt.figure(figsize=(10, 6))

    # Plot a histogram with 100 bins. We can't be sure of the range anymore,
    # so we'll let pandas choose the best range.
    plt.hist(sig_series, bins=100)

    plt.title('Distribution of "combined_signal" Values (Valid Signals Only)')
    plt.xlabel('Signal Value')
    plt.ylabel('Frequency')
    plt.grid(True)
    plt.savefig('signal_distribution_cleaned.png')
    print("Saved plot to 'signal_distribution_cleaned.png'")

except FileNotFoundError:
    print(f"Error: Signal file not found at {SIGNALS_JSONL}")
    print("Please make sure the file path is correct.")
except Exception as e:
    print(f"An error occurred: {e}")