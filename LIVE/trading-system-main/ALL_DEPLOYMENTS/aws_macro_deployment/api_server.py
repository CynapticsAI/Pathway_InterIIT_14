# api_server.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import pickle
import os
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from fredapi import Fred
import yfinance as yf
import torch
import torch.nn as nn
import asyncio  # Added for async operations

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S"
)

app = FastAPI(
    title="Stock Sector Prediction API",
    description="Real-time predictions for 11 stock market sectors using FRED economic data",
    version="1.0.0"
)

FRED_API_KEY = os.getenv("FRED_API_KEY")
if not FRED_API_KEY:
    logging.warning("FRED_API_KEY not set! Set it with: export FRED_API_KEY='your_key'")
    fred = None
else:
    fred = Fred(api_key=FRED_API_KEY)

SECTOR_TICKERS = {
    "Energy": "XLE",
    "Materials": "XLB",
    "Industrials": "XLI",
    "Consumer Discretionary": "XLY",
    "Consumer Staples": "XLP",
    "Health Care": "XLV",
    "Financials": "XLF",
    "Information Technology": "XLK",
    "Communication Services": "XLC",
    "Utilities": "XLU",
    "Real Estate": "XLRE"
}

SECTOR_FEATURES = {
    "Energy": ["DCOILWTICO", "CPIENGSL", "PPIENG", "INDPRO", "CPALTT01USM657N"],
    "Materials": ["PPIACO", "INDPRO", "CPALTT01USM657N", "MNFCTRIRSA"],
    "Industrials": ["INDPRO", "IPMAN", "CAPUTLB00004S", "DGORDER", "UNRATE"],
    "Consumer Discretionary": ["RSAFS", "UMCSENT", "UNRATE", "PCE", "CPIAUCSL"],
    "Consumer Staples": ["RRSFS", "CPIFABSL", "CPIAUCSL", "UNRATE"],
    "Health Care": ["CPIMEDSL", "GDP", "UNRATE", "CPIAUCSL"],
    "Financials": ["FEDFUNDS", "T10Y2Y", "M2SL", "HOUST", "MORTGAGE30US"],
    "Information Technology": ["IPB53100SQ", "DGORDER", "CPIAUCSL", "FEDFUNDS"],
    "Communication Services": ["UMCSENT", "PCE", "GDP", "CPIAUCSL"],
    "Utilities": ["FEDFUNDS", "CPENGSL", "T10Y3M", "INDPRO"],
    "Real Estate": ["HOUST", "PERMIT", "MORTGAGE30US", "CSUSHPINSA", "CPIAUCSL"]
}

# --- Response Models ---

class SectorPrediction(BaseModel):
    sector: str
    ticker: str
    predicted_return_pct: float
    sentiment: str
    confidence_score: float
    model_metrics: Dict[str, float]
    last_updated: str
    features_used: List[str]

class PredictionResponse(BaseModel):
    timestamp: str
    total_sectors: int
    predictions: List[SectorPrediction]
    market_summary: Dict[str, Any]

class HealthCheck(BaseModel):
    status: str
    models_loaded: int
    total_sectors: int
    last_training: Optional[str]
    last_prediction_update: Optional[str] # Added for cache status

# --- Caching Globals ---

# Cache for models
models_cache = {}

# NEW: Cache for the final prediction response
prediction_cache: Optional[PredictionResponse] = None
last_prediction_update: Optional[datetime] = None
PREDICTION_CACHE_TTL = 600  # 10 minutes (as requested)
cache_update_lock = asyncio.Lock()


# --- Model Definition ---

class RegularizedLSTM(nn.Module):
    """
    LSTM with regularization:
    - Dropout
    - Smaller model (32 units)
    - L2 regularization (weight decay)
    - Fewer layers (2)
    """
    
    def __init__(self, input_dim: int, hidden_dim: int = 32, num_layers: int = 2, dropout: float = 0.5):
        super(RegularizedLSTM, self).__init__()
        
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        self.lstm_covariates = nn.LSTM(
            input_dim, 
            hidden_dim,
            num_layers, 
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        self.lstm_target = nn.LSTM(
            1,
            hidden_dim // 2,
            1,
            batch_first=True
        )
        
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)
        self.dropout3 = nn.Dropout(dropout * 0.7)
        
        self.fc1 = nn.Linear(hidden_dim + hidden_dim // 2, hidden_dim)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_dim, 1)
    
    def forward(self, x_covariates: torch.Tensor, y_history: torch.Tensor) -> torch.Tensor:
        lstm_out_cov, _ = self.lstm_covariates(x_covariates)
        lstm_out_cov = lstm_out_cov[:, -1, :]
        lstm_out_cov = self.dropout1(lstm_out_cov)
        
        y_history = y_history.unsqueeze(-1)
        lstm_out_target, _ = self.lstm_target(y_history)
        lstm_out_target = lstm_out_target[:, -1, :]
        lstm_out_target = self.dropout2(lstm_out_target)
        
        combined = torch.cat([lstm_out_cov, lstm_out_target], dim=1)
        
        out = self.fc1(combined)
        out = self.relu(out)
        out = self.dropout3(out)
        out = self.fc2(out)
        
        return out.squeeze()

# --- Helper Functions ---

def convert_to_python_types(obj):
    """Convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_to_python_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_python_types(item) for item in obj]
    else:
        return obj

# --- Model Loading (Blocking) ---
# NOTE: These functions are synchronous and MUST be called with asyncio.to_thread

def load_model(sector: str):
    """Load a trained model from disk - FIXED to reconstruct model from state_dict"""
    filename = f"models/{sector.replace(' ', '_')}_model.pkl"
    
    try:
        if not os.path.exists(filename):
            logging.warning(f"Model file not found: {filename}")
            return None
        
        with open(filename, 'rb') as f:
            model_data = pickle.load(f)
        
        # CRITICAL FIX: Reconstruct the model from config and state_dict
        if 'model_config' in model_data and 'model_state_dict' in model_data:
            config = model_data['model_config']
            model = RegularizedLSTM(
                input_dim=config['input_dim'],
                hidden_dim=config['hidden_dim'],
                num_layers=config['num_layers'],
                dropout=config['dropout']
            )
            model.load_state_dict(model_data['model_state_dict'])
            model.eval()
            # logging.info(f"✓ Loaded model for {sector} (from config)") # Too noisy for loops
        elif 'model' in model_data:
            # Fallback for old format (if any old models still exist)
            model = model_data['model']
            model.eval()
            logging.info(f"✓ Loaded model for {sector} (legacy format)")
        else:
            logging.error(f"Invalid model format for {sector}")
            return None
        
        return model_data
    except Exception as e:
        logging.error(f"Error loading model for {sector}: {e}")
        import traceback
        traceback.print_exc()
        return None

def load_all_models():
    """Load all sector models into cache (Synchronous)"""
    global models_cache
    
    logging.info("Loading all models from disk...")
    new_models_cache = {}
    
    if not os.path.exists("models"):
        logging.warning("models/ directory not found. No models loaded.")
        models_cache = new_models_cache # Atomically update
        return
    
    for sector in SECTOR_TICKERS.keys():
        model_data = load_model(sector)
        if model_data:
            new_models_cache[sector] = model_data
    
    models_cache = new_models_cache # Atomically update
    logging.info(f"✓ Loaded {len(models_cache)}/{len(SECTOR_TICKERS)} models")
    return

# --- Data Fetching & Prediction (Blocking) ---
# NOTE: These functions are synchronous and MUST be called with asyncio.to_thread

def get_latest_fred_data(features: List[str], start_date="1990-01-01"):
    """Fetch latest FRED data for given features (Synchronous)"""
    if fred is None:
        logging.error("FRED API key not configured")
        return None
    
    data = {}
    failed_series = []
    
    for series_id in features:
        try:
            series = fred.get_series(series_id, observation_start=start_date)
            if len(series) > 0:
                data[series_id] = series
            else:
                logging.warning(f"Empty series for {series_id}")
                failed_series.append(series_id)
        except Exception as e:
            logging.warning(f"Failed to fetch {series_id}: {e}")
            failed_series.append(series_id)
    
    if len(failed_series) > 0:
        logging.info(f"Failed to fetch {len(failed_series)} series: {failed_series}")
    
    if not data:
        logging.error("No data fetched from FRED")
        return None
    
    df = pd.DataFrame(data)
    df.index = pd.to_datetime(df.index)
    df = df.resample("ME").last()
    
    # Fill missing values
    for col in df.columns:
        df[col] = df[col].ffill().bfill().fillna(0.0)
    
    # Final check for any remaining NaN or inf
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.fillna(0.0)
    
    # logging.info(f"FRED data fetched: {df.shape[0]} rows, {df.shape[1]} columns") # Too noisy
    return df

def robust_feature_engineering(df: pd.DataFrame, original_cols: List[str]) -> pd.DataFrame:
    """Conservative feature engineering (Synchronous)"""
    # logging.info("Creating robust features...") # Too noisy
    
    if len(df) < 50:
        logging.warning(f"Not enough data for feature engineering: {len(df)} rows")
        return pd.DataFrame()
    
    df_features = df.copy()
    
    # Lag features
    for col in original_cols:
        if col in df.columns:
            df_features[f'{col}_lag5'] = df[col].shift(5)
            df_features[f'{col}_lag20'] = df[col].shift(20)
    
    # Rolling features
    for col in original_cols:
        if col in df.columns:
            df_features[f'{col}_ma20'] = df[col].rolling(window=20, min_periods=10).mean()
            df_features[f'{col}_std20'] = df[col].rolling(window=20, min_periods=10).std()
    
    # Rate of change - prevent division by zero
    for col in original_cols:
        if col in df.columns:
            roc = df[col].pct_change(periods=20)
            roc = roc.replace([np.inf, -np.inf], 0.0)
            df_features[f'{col}_roc20'] = roc
    
    # Clean up - more aggressive
    df_features = df_features.replace([np.inf, -np.inf], np.nan)
    df_features = df_features.fillna(0.0)  # Fill NaN with 0 instead of dropping
    df_features = df_features.dropna(how='all')
    
    if len(df_features) == 0:
        logging.error("All data lost after feature engineering!")
        return pd.DataFrame()
    
    # logging.info(f"Robust features: {len(original_cols)} → {len(df_features.columns)} features, {len(df_features)} rows")
    return df_features

def temporal_interpolation(df: pd.DataFrame, method: str = 'linear') -> pd.DataFrame:
    """Linear interpolation (Synchronous)"""
    # logging.info("Interpolating (linear)...") # Too noisy
    
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    daily_index = pd.date_range(start=df.index.min(), end=df.index.max(), freq='D')
    df_daily = df.reindex(daily_index)
    df_daily = df_daily.interpolate(method=method, limit_direction='both')
    
    # logging.info(f"Augmented: {len(df)} → {len(df_daily)} points")
    return df_daily

def get_etf_daily(ticker: str) -> pd.Series:
    """Fetch daily ETF data (Synchronous)"""
    try:
        # logging.info(f"Fetching {ticker}...") # Too noisy
        df = yf.download(ticker, start="2000-01-01", interval="1d", 
                         progress=False, auto_adjust=False)
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [" ".join(col).strip() for col in df.columns.values]
        
        adj_cols = [c for c in df.columns if "Adj Close" in c]
        if not adj_cols:
            raise KeyError(f"'Adj Close' not found")
        
        series = df[adj_cols[0]].rename(ticker)
        series.index = pd.to_datetime(series.index)
        
        # logging.info(f"{ticker}: {len(series)} records")
        return series
    except Exception as e:
        logging.error(f"Error fetching {ticker}: {e}")
        return pd.Series()

def make_prediction(sector: str, model_data: Dict) -> Optional[Dict]:
    """Make prediction for a sector using loaded model (Synchronous)"""
    logging.info(f"Making prediction for {sector}...")
    try:
        # Reconstruct model if needed
        if 'model_config' in model_data and 'model_state_dict' in model_data:
            config = model_data['model_config']
            model = RegularizedLSTM(
                input_dim=config['input_dim'],
                hidden_dim=config['hidden_dim'],
                num_layers=config['num_layers'],
                dropout=config['dropout']
            )
            model.load_state_dict(model_data['model_state_dict'])
            model.eval()
        else:
            model = model_data.get('model')
            if model is None:
                logging.error(f"No model found for {sector}")
                return None
            model.eval()
        
        # Get model metadata
        trained_features = model_data['features']
        metrics = model_data['metrics']
        scaler = model_data['scaler']
        sequence_length = model_data['sequence_length']
        
        # Extract base features needed
        base_features_needed = set()
        for feat in trained_features:
            base_feat = feat.split('_lag')[0].split('_ma')[0].split('_std')[0].split('_roc')[0]
            base_features_needed.add(base_feat)
        
        base_features_needed = list(base_features_needed)
        # logging.info(f"Base features needed: {base_features_needed}")
        
        df_fred = get_latest_fred_data(base_features_needed)
        
        if df_fred is None or len(df_fred) == 0:
            logging.warning(f"No FRED data available for {sector}")
            return None
        
        available_base_features = [f for f in base_features_needed if f in df_fred.columns]
        
        if len(available_base_features) == 0:
            logging.warning(f"No matching features for {sector}")
            return None
        
        y = get_etf_daily(SECTOR_TICKERS[sector])
        if len(y) == 0:
            logging.warning(f"No yfinance data for {SECTOR_TICKERS[sector]}")
            return None
        
        y = y.pct_change().dropna()
        
        X = df_fred[available_base_features].copy()
        X.index = pd.to_datetime(df_fred.index)
        
        X_daily = temporal_interpolation(X, method='linear')
        
        df = X_daily.join(y, how="inner").dropna()
        # logging.info(f"Data: {len(df)} days")
        
        if len(df) < 250:
            logging.warning(f"Not enough combined data for {sector}: {len(df)} days")
            return None
        
        X_prep = df[available_base_features].copy()
        y_prep = df[y.name].copy()
        
        # Create engineered features
        X_engineered = robust_feature_engineering(X_prep, available_base_features)
        y_prep = y_prep.loc[X_engineered.index]
        
        # logging.info(f"Engineered features: {X_engineered.shape}")
        
        if len(X_engineered) == 0 or X_engineered.shape[1] == 0:
            logging.error(f"Feature engineering returned empty DataFrame for {sector}")
            return None
        
        # --- Data Cleaning ---
        X_engineered = X_engineered.replace([np.inf, -np.inf], np.nan)
        X_engineered = X_engineered.fillna(0)
        X_engineered = X_engineered.clip(lower=-10, upper=10)
        
        y_prep = y_prep.replace([np.inf, -np.inf], np.nan)
        y_prep = y_prep.fillna(0)
        y_prep = y_prep.clip(lower=-0.3, upper=0.3)
        
        if len(X_engineered) == 0:
            logging.error(f"No data left after cleaning for {sector}")
            return None
        
        # Match the trained features
        missing_features = set(trained_features) - set(X_engineered.columns)
        if missing_features:
            # logging.warning(f"Missing features: {missing_features}")
            for feat in missing_features:
                X_engineered[feat] = 0.0
        
        X_engineered = X_engineered[trained_features]
        # logging.info(f"Final feature shape: {X_engineered.shape}")
        
        X_latest = X_engineered.values
        y_latest = y_prep.values
        
        if len(X_latest) == 0:
            logging.error(f"Empty array after feature matching for {sector}")
            return None
        
        # Aggressive cleaning before scaling
        X_latest = X_latest.astype(np.float64)
        X_latest = np.nan_to_num(X_latest, nan=0.0, posinf=0.0, neginf=0.0)
        X_latest = np.clip(X_latest, -10, 10)

        if not np.all(np.isfinite(X_latest)):
            logging.critical(f"CRITICAL: Non-finite values STILL present in {sector}")
            return None
        
        try:
            X_latest = scaler.transform(X_latest)
        except Exception as e:
            logging.error(f"Scaler transform failed for {sector}: {e}")
            return None
        
        # Get the last sequence
        if len(X_latest) < sequence_length:
            logging.warning(f"Not enough data for sequence: {len(X_latest)} < {sequence_length}")
            return None
        
        X_seq = X_latest[-sequence_length:]
        y_history = y_latest[-sequence_length:]
        
        X_seq = torch.FloatTensor(X_seq).unsqueeze(0)
        y_history = torch.FloatTensor(y_history).unsqueeze(0)
        
        with torch.no_grad():
            prediction = model(X_seq, y_history).item()
        
        if not np.isfinite(prediction):
            logging.error(f"Non-finite prediction for {sector}")
            prediction = 0.0
        prediction = round(prediction * 100, 2)


        if prediction > 0.1:
            sentiment = "BULLISH"
        elif prediction < -0.1:
            sentiment = "BEARISH"
        else:
            sentiment = "NEUTRAL"
        
        dir_acc = metrics.get('test_dir_acc', 0)
        confidence = min(100, max(0, (dir_acc + abs(prediction) * 100) / 2))
        
        result = {
            'sector': sector,
            'ticker': SECTOR_TICKERS[sector],
            'predicted_return_pct': prediction,
            'sentiment': sentiment,
            'confidence_score': round(confidence, 2),
            'model_metrics': {
                'rmse': round(metrics.get('test_rmse', 0), 4),
                'mae': round(metrics.get('test_mae', 0), 4),
                'dir_acc': round(metrics.get('test_dir_acc', 0), 4)
            },
            'last_updated': model_data.get('timestamp', datetime.now().isoformat()),
            'features_used': available_base_features
        }
        
        logging.info(f"✓ Prediction generated for {sector}")
        return convert_to_python_types(result)
    
    except Exception as e:
        logging.error(f"Error making prediction for {sector}: {e}")
        import traceback
        traceback.print_exc()
        return None

# --- NEW: Caching and Background Tasks ---

async def update_prediction_cache():
    """
    (Async) This function performs the heavy lifting:
    1. Loads all models from disk (in a thread)
    2. Fetches all data and generates predictions concurrently (in threads)
    3. Caches the final PredictionResponse object
    """
    global prediction_cache, last_prediction_update, models_cache
    
    # Use the lock to prevent this function from running twice at the same time
    async with cache_update_lock:
        logging.info("Starting prediction cache update...")
        
        # 1. Load all models (blocking I/O, run in thread)
        await asyncio.to_thread(load_all_models)
        
        if len(models_cache) == 0:
            logging.warning("No models available. Skipping prediction update.")
            return

        # 2. Create a list of prediction tasks to run concurrently
        prediction_tasks = []
        for sector, model_data in models_cache.items():
            # Run each blocking make_prediction call in its own thread
            task = asyncio.to_thread(make_prediction, sector, model_data)
            prediction_tasks.append(task)
        
        # 3. Run all prediction tasks in parallel
        logging.info(f"Gathering predictions for {len(prediction_tasks)} sectors...")
        results = await asyncio.gather(*prediction_tasks, return_exceptions=True)
        
        predictions = []
        for result in results:
            if isinstance(result, Exception):
                logging.error(f"Prediction task failed: {result}")
            elif result is not None:
                predictions.append(result)

        if len(predictions) == 0:
            logging.error("Failed to generate any predictions. Cache not updated.")
            return

        # 4. Process results and build market summary
        avg_return = float(np.mean([p['predicted_return_pct'] for p in predictions]))
        bullish_count = sum(1 for p in predictions if p['sentiment'] == 'BULLISH')
        bearish_count = sum(1 for p in predictions if p['sentiment'] == 'BEARISH')
        neutral_count = sum(1 for p in predictions if p['sentiment'] == 'NEUTRAL')
        avg_confidence = float(np.mean([p['confidence_score'] for p in predictions]))
        avg_dir_acc = float(np.mean([p['model_metrics'].get('dir_acc', 0) for p in predictions]))
        
        if avg_return > 0.5:
            market_outlook = "BULLISH MARKET"
        elif avg_return < -0.5:
            market_outlook = "BEARISH MARKET"
        else:
            market_outlook = "NEUTRAL MARKET"
        
        predictions.sort(key=lambda x: x['predicted_return_pct'], reverse=True)
        
        market_summary = {
            "average_return_pct": round(avg_return, 2),
            "market_outlook": market_outlook,
            "bullish_sectors": bullish_count,
            "bearish_sectors": bearish_count,
            "neutral_sectors": neutral_count,
            "average_confidence": round(avg_confidence, 2),
            "average_dir_acc": round(avg_dir_acc, 4),
            "best_sector": predictions[0]['sector'] if predictions else None,
            "worst_sector": predictions[-1]['sector'] if predictions else None
        }
        
        # 5. Store the final result in the global cache
        new_cache_data = {
            "timestamp": datetime.now().isoformat(),
            "total_sectors": len(predictions),
            "predictions": predictions,
            "market_summary": market_summary
        }
        
        prediction_cache = PredictionResponse(**new_cache_data)
        last_prediction_update = datetime.now()
        logging.info(f"✅ Prediction cache updated with {len(predictions)} sectors.")

async def prediction_update_loop():
    """A background task that runs forever, updating the cache every 10 minutes."""
    while True:
        try:
            await update_prediction_cache()
        except Exception as e:
            logging.error(f"Error during scheduled cache update: {e}")
            import traceback
            traceback.print_exc()
            
        logging.info(f"Cache update loop sleeping for {PREDICTION_CACHE_TTL} seconds...")
        await asyncio.sleep(PREDICTION_CACHE_TTL)

# --- FastAPI Events ---

@app.on_event("startup")
async def startup_event():
    """Load models and start the prediction cache loop on startup"""
    logging.info("Starting API server...")
    
    # 1. Load models first (in a thread to not block startup)
    await asyncio.to_thread(load_all_models)
    
    # 2. Run the prediction update function ONCE immediately
    logging.info("Populating initial prediction cache...")
    await update_prediction_cache()
    
    # 3. Start the background loop to run every 10 minutes
    logging.info("Starting background cache update loop...")
    asyncio.create_task(prediction_update_loop())
    
    logging.info("API server ready!")

# --- API Endpoints ---

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Stock Sector Prediction API",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/predict": "Get predictions for all sectors (cached)",
            "/predict/{sector}": "Get prediction for specific sector (cached)",
            "/models": "List all loaded models",
            "/reload-models": "Manually trigger a cache and model reload",
            "/docs": "Interactive API documentation"
        }
    }

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint (reports status, does not trigger reloads)"""
    global models_cache, last_prediction_update
    
    latest_training = None
    if models_cache:
        training_times = [m.get('timestamp') for m in models_cache.values() if m.get('timestamp')]
        if training_times:
            latest_training = max(training_times)
    
    status = "degraded"
    if len(models_cache) > 0 and prediction_cache is not None:
        status = "healthy"
    elif len(models_cache) > 0 and prediction_cache is None:
        status = "degraded (models loaded, predictions pending)"
    
    return {
        "status": status,
        "models_loaded": len(models_cache),
        "total_sectors": len(SECTOR_TICKERS),
        "last_training": latest_training,
        "last_prediction_update": last_prediction_update.isoformat() if last_prediction_update else None
    }

@app.get("/models", response_model=Dict[str, Any])
async def list_models():
    """List all loaded models with metadata (reads from model cache)"""
    global models_cache
    
    models_info = {}
    for sector, model_data in models_cache.items():
        models_info[sector] = {
            "ticker": SECTOR_TICKERS[sector],
            "features_count": len(model_data.get('features', [])),
            "features": model_data.get('features', []),
            "metrics": convert_to_python_types(model_data.get('metrics', {})),
            "last_updated": model_data.get('timestamp'),
            "last_data_date": model_data.get('last_data_date')
        }
    
    return {
        "total_models": len(models_info),
        "models": models_info
    }

@app.get("/predict", response_model=PredictionResponse)
async def predict_all_sectors():
    """Get predictions for all sectors (from cache)"""
    if prediction_cache is None:
        raise HTTPException(
            status_code=503, 
            detail="Predictions are being generated. Please try again in a moment."
        )
    return prediction_cache

@app.get("/predict/{sector}", response_model=SectorPrediction)
async def predict_sector(sector: str):
    """Get prediction for a specific sector (from cache)"""
    if sector not in SECTOR_TICKERS:
        raise HTTPException(
            status_code=404, 
            detail=f"Sector '{sector}' not found. Available sectors: {list(SECTOR_TICKERS.keys())}"
        )
        
    if prediction_cache is None:
        raise HTTPException(
            status_code=503, 
            detail="Predictions are being generated. Please try again in a moment."
        )
    
    # Find the specific sector in the cached list
    for prediction in prediction_cache.predictions:
        if prediction.sector == sector:
            return prediction
            
    # If loop finishes without returning, the prediction failed for this sector
    raise HTTPException(
        status_code=404, 
        detail=f"Prediction for sector '{sector}' is not available in the cache (it may have failed during the update)."
    )

@app.post("/reload-models")
async def reload_models():
    """Manually trigger a reload of all models and a prediction cache update"""
    if cache_update_lock.locked():
        raise HTTPException(status_code=429, detail="A cache update is already in progress.")
    
    try:
        # Run the update function manually
        await update_prediction_cache()
        return {
            "status": "success",
            "message": f"Reloaded {len(models_cache)} models and updated prediction cache with {len(prediction_cache.predictions)} predictions.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload models: {str(e)}")

# --- Main Entry Point ---

if __name__ == "__main__":
    import uvicorn
    
    if not os.path.exists("models"):
        logging.warning(" 'models/' directory not found. Creating it...")
        os.makedirs("models")
        logging.warning(" No models available yet. Please run the training pipeline first.")
    
    model_files = [f for f in os.listdir("models") if f.endswith('.pkl')] if os.path.exists("models") else []
    if len(model_files) == 0:
        logging.warning(" No trained models found in 'models/' directory.")
        logging.warning("API will run but predictions will fail until models are trained.")
    else:
        logging.info(f"✓ Found {len(model_files)} model files")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)