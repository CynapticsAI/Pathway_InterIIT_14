import os
import json
import pandas as pd
from typing import List, Dict, Any
from fastapi import FastAPI

app = FastAPI(title="Market Data & Signals API")

# --- Configuration ---
# File paths based on the codebase structure
# Note: In a real deployment, these paths would point to the mounted volumes.
# Here we assume the server runs from the repo root and accesses files in subdirectories.

FILES = {
    "news": "news_producer/news_NVDA.csv",
    "ohlc": "spike_detector/ohlc_bars.jsonl",
    "vol_data": "spike_detector/vol_data.jsonl", # Contains volume & volatility z-scores
    "volume_volatility": "spike_detector/volume_volatility.jsonl", # Contains stats
    "sarimax_signal": "sarimaxConsumer/final_combined_signal.jsonl",
    "model_selection": "selection/s_output/model_selection.jsonl",
    # Intermediate files that might be useful
    "ohlc_sari": "sarimaxConsumer/ohlc_bars.jsonl",
    "comp_csv": "selection/s_output/comp.csv",
    "trigger_output": "trigger/t_output/trigger_output.jsonl"
}

# --- Helper Functions ---

def read_jsonl(filepath: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Reads the last `limit` lines from a JSONL file."""
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return []

    data = []
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            # Get last `limit` lines
            last_lines = lines[-limit:] if limit > 0 else lines
            for line in last_lines:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return []

    return data

def read_csv(filepath: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Reads the last `limit` rows from a CSV file."""
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return []

    try:
        # Read the entire file is simplest for small files, but for large ones we might want to be smarter.
        # Assuming files are manageable for this context.
        df = pd.read_csv(filepath)
        if limit > 0:
            df = df.tail(limit)

        # Convert NaN to None for JSON compatibility
        df = df.where(pd.notnull(df), None)
        return df.to_dict(orient='records')
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return []

# --- Endpoints ---

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Market Data API is running"}

@app.get("/news", summary="Get latest news")
def get_news(limit: int = 20):
    """
    Returns the latest news items.
    """
    return read_csv(FILES["news"], limit=limit)

@app.get("/ohlc", summary="Get latest OHLC bars")
def get_ohlc(limit: int = 50, source: str = "spike_detector"):
    """
    Returns the latest OHLC bars.
    param source: 'spike_detector' or 'sarimax' (default: spike_detector)
    """
    filepath = FILES["ohlc"]
    if source == "sarimax":
        filepath = FILES["ohlc_sari"]

    return read_jsonl(filepath, limit=limit)

@app.get("/volatility", summary="Get volume and volatility analysis")
def get_volatility(limit: int = 50):
    """
    Returns the latest volume and volatility z-scores and risk levels.
    """
    # vol_data.jsonl has timestamp, symbol, volume_zscore, volatility_zscore
    # volume_volatility.jsonl has stats like avg_volume, std_volume etc.
    # We'll serve vol_data as it's the processed z-score stream
    return read_jsonl(FILES["vol_data"], limit=limit)

@app.get("/signals", summary="Get SARIMAX & Sentiment signals")
def get_signals(limit: int = 20):
    """
    Returns the latest combined signals from SARIMAX and Sentiment analysis.
    Includes final signal, individual scores, and forecast price.
    """
    return read_jsonl(FILES["sarimax_signal"], limit=limit)

@app.get("/prediction", summary="Get Model Selection & Final Prediction")
def get_prediction(limit: int = 20):
    """
    Returns the result of the model selection (Chronos vs SARIMAX) and the final price prediction.
    """
    return read_jsonl(FILES["model_selection"], limit=limit)

@app.get("/comparison", summary="Get Model Comparison Data")
def get_comparison(limit: int = 20):
    """
    Returns the comparison data between models (CSV source).
    """
    return read_csv(FILES["comp_csv"], limit=limit)

@app.get("/trigger", summary="Get Model Comparison Data")
def get_comparison(limit: int = 20):
    """
    Returns the comparison data between models (CSV source).
    """
    return read_jsonl(FILES["trigger_output"], limit=limit)

@app.get("/all", summary="Get latest snapshot of all data")
def get_all(limit: int = 5):
    """
    Returns a consolidated snapshot of the latest data from all sources.
    """
    return {
        "news": get_news(limit=limit),
        "ohlc": get_ohlc(limit=limit),
        "volatility": get_volatility(limit=limit),
        "signals": get_signals(limit=limit),
        "prediction": get_prediction(limit=limit)
    }

if __name__ == "__main__":
    import uvicorn
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000)
