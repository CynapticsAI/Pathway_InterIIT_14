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

# Response Models
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

# Cache for models
models_cache = {}
last_cache_time = None
CACHE_DURATION = 300  # 5 minutes

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
            logging.info(f"✓ Loaded model for {sector} (from config)")
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
    """Load all sector models into cache"""
    global models_cache, last_cache_time
    
    logging.info("Loading all models...")
    models_cache = {}
    
    if not os.path.exists("models"):
        logging.warning("models/ directory not found. No models loaded.")
        last_cache_time = datetime.now()
        return models_cache
    
    for sector in SECTOR_TICKERS.keys():
        model_data = load_model(sector)
        if model_data:
            models_cache[sector] = model_data
    
    last_cache_time = datetime.now()
    logging.info(f"✓ Loaded {len(models_cache)}/{len(SECTOR_TICKERS)} models")
    
    return models_cache

def get_latest_fred_data(features: List[str], start_date="1990-01-01"):
    """Fetch latest FRED data for given features"""
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
    
    logging.info(f"FRED data fetched: {df.shape[0]} rows, {df.shape[1]} columns")
    
    return df

def robust_feature_engineering(df: pd.DataFrame, original_cols: List[str]) -> pd.DataFrame:
    """
    Conservative feature engineering to prevent overfitting
    - Only proven features
    - Avoid creating too many correlated features
    - Focus on stability over complexity
    """
    logging.info("Creating robust features...")
    
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
            # Use fill_method=None to avoid the warning and handle zeros
            roc = df[col].pct_change(periods=20)
            # Replace inf values that come from dividing by zero
            roc = roc.replace([np.inf, -np.inf], 0.0)
            df_features[f'{col}_roc20'] = roc
    
    # Clean up - more aggressive
    df_features = df_features.replace([np.inf, -np.inf], np.nan)
    df_features = df_features.fillna(0.0)  # Fill NaN with 0 instead of dropping
    
    # Only drop rows that are ALL NaN (shouldn't happen after fillna, but safety check)
    df_features = df_features.dropna(how='all')
    
    if len(df_features) == 0:
        logging.error("All data lost after feature engineering!")
        return pd.DataFrame()
    
    logging.info(f"Robust features: {len(original_cols)} → {len(df_features.columns)} features, {len(df_features)} rows")
    
    return df_features

def temporal_interpolation(df: pd.DataFrame, method: str = 'linear') -> pd.DataFrame:
    """Linear interpolation (simpler, less overfitting than cubic)."""
    logging.info("Interpolating (linear)...")
    
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    daily_index = pd.date_range(start=df.index.min(), end=df.index.max(), freq='D')
    df_daily = df.reindex(daily_index)
    df_daily = df_daily.interpolate(method=method, limit_direction='both')
    
    logging.info(f"Augmented: {len(df)} → {len(df_daily)} points")
    return df_daily

def get_etf_daily(ticker: str) -> pd.Series:
    """Fetch daily ETF data."""
    try:
        logging.info(f"Fetching {ticker}...")
        df = yf.download(ticker, start="2000-01-01", interval="1d", 
                        progress=False, auto_adjust=False)
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [" ".join(col).strip() for col in df.columns.values]
        
        adj_cols = [c for c in df.columns if "Adj Close" in c]
        if not adj_cols:
            raise KeyError(f"'Adj Close' not found")
        
        series = df[adj_cols[0]].rename(ticker)
        series.index = pd.to_datetime(series.index)
        
        logging.info(f"{ticker}: {len(series)} records")
        return series
    except Exception as e:
        logging.error(f"Error: {e}")
        return pd.Series()

def make_prediction(sector: str, model_data: Dict) -> Optional[Dict]:
    """Make prediction for a sector using loaded model"""
    try:
        # Reconstruct model if needed (for compatibility)
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
            # Legacy support
            model = model_data.get('model')
            if model is None:
                logging.error(f"No model found for {sector}")
                return None
            model.eval()
        
        # Get the exact features used during training
        trained_features = model_data['features']
        metrics = model_data['metrics']
        scaler = model_data['scaler']
        sequence_length = model_data['sequence_length']
        
        # Extract base features from engineered feature names
        # E.g., "DCOILWTICO_lag5" -> "DCOILWTICO"
        base_features_needed = set()
        for feat in trained_features:
            # Split on '_lag', '_ma', '_std', '_roc' to get base feature
            base_feat = feat.split('_lag')[0].split('_ma')[0].split('_std')[0].split('_roc')[0]
            base_features_needed.add(base_feat)
        
        base_features_needed = list(base_features_needed)
        logging.info(f"Base features needed: {base_features_needed}")
        
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
            return None
        
        y = y.pct_change().dropna()
        
        X = df_fred[available_base_features].copy()
        X.index = pd.to_datetime(df_fred.index)
        
        X_daily = temporal_interpolation(X, method='linear')
        
        df = X_daily.join(y, how="inner").dropna()
        logging.info(f"Data: {len(df)} days")
        
        if len(df) < 250:
            logging.warning("Not enough data")
            return None
        
        X_prep = df[available_base_features].copy()
        y_prep = df[y.name].copy()
        
        # Create engineered features
        X_engineered = robust_feature_engineering(X_prep, available_base_features)
        y_prep = y_prep.loc[X_engineered.index]
        
        logging.info(f"Engineered features: {X_engineered.shape}")
        
        # Check if feature engineering returned empty DataFrame
        if len(X_engineered) == 0 or X_engineered.shape[1] == 0:
            logging.error(f"Feature engineering returned empty DataFrame for {sector}")
            return None
        
        # CRITICAL: Clean infinity and NaN values IMMEDIATELY after feature engineering
        # Step 1: Replace inf with NaN
        X_engineered = X_engineered.replace([np.inf, -np.inf], np.nan)
        
        # Step 2: Fill NaN with 0
        X_engineered = X_engineered.fillna(0)
        
        # Step 3: Clip to reasonable range
        X_engineered = X_engineered.clip(lower=-10, upper=10)
        
        # Step 4: Ensure all values are finite
        for col in X_engineered.columns:
            if not np.all(np.isfinite(X_engineered[col])):
                logging.warning(f"Column {col} still has non-finite values, forcing to 0")
                X_engineered[col] = X_engineered[col].replace([np.inf, -np.inf], 0).fillna(0)
        
        # Clean y_prep as well
        y_prep = y_prep.replace([np.inf, -np.inf], np.nan)
        y_prep = y_prep.fillna(0)
        y_prep = y_prep.clip(lower=-0.3, upper=0.3)
        
        # Check if we have enough data after cleaning
        if len(X_engineered) == 0:
            logging.error(f"No data left after cleaning for {sector}")
            return None
        
        # CRITICAL: Ensure we have the exact same features as during training
        # Match the trained features
        missing_features = set(trained_features) - set(X_engineered.columns)
        if missing_features:
            logging.warning(f"Missing features: {missing_features}")
            # Add missing features as zeros
            for feat in missing_features:
                X_engineered[feat] = 0.0
        
        # Keep only the features that were used during training, in the same order
        X_engineered = X_engineered[trained_features]
        
        logging.info(f"Final feature shape: {X_engineered.shape}")
        
        X_latest = X_engineered.values
        y_latest = y_prep.values
        
        # Final check before scaling
        if len(X_latest) == 0:
            logging.error(f"Empty array after feature matching for {sector}")
            return None
        
        # AGGRESSIVE cleaning before scaling - this is critical!
        # Step 1: Convert to float64 explicitly
        X_latest = X_latest.astype(np.float64)
        
        # Step 2: Replace any inf values
        X_latest = np.where(np.isinf(X_latest), 0.0, X_latest)
        
        # Step 3: Replace any NaN values  
        X_latest = np.where(np.isnan(X_latest), 0.0, X_latest)
        
        # Step 4: Clip extreme values
        X_latest = np.clip(X_latest, -10, 10)
        
        # Step 5: Force clean with nan_to_num (no conditions, just do it)
        X_latest = np.nan_to_num(X_latest, nan=0.0, posinf=0.0, neginf=0.0, 
                                  copy=False)
        
        # Step 6: Final validation with detailed logging
        if not np.all(np.isfinite(X_latest)):
            logging.error(f"Non-finite values STILL present after cleaning in {sector}")
            logging.error(f"Inf count: {np.isinf(X_latest).sum()}, NaN count: {np.isnan(X_latest).sum()}")
            logging.error(f"Min: {np.nanmin(X_latest)}, Max: {np.nanmax(X_latest)}")
            logging.error(f"Sample values: {X_latest.flat[:10]}")
            # This should never happen now, but just in case
            X_latest = np.zeros_like(X_latest)
            logging.error("Replaced all with zeros as last resort!")
        
        # Step 7: Final assertion - this should NEVER fail now
        try:
            assert np.all(np.isfinite(X_latest)), "X_latest still contains non-finite values!"
        except AssertionError as e:
            logging.critical(f"CRITICAL: Assertion failed for {sector}: {e}")
            logging.critical(f"Shape: {X_latest.shape}, dtype: {X_latest.dtype}")
            logging.critical(f"Min: {np.nanmin(X_latest)}, Max: {np.nanmax(X_latest)}")
            # Force it to work
            X_latest = np.zeros_like(X_latest)
        
        # Step 8: One more safety check with explicit float64 conversion
        X_latest = X_latest.astype(np.float64, copy=False)
        
        logging.info(f"Pre-scaler check: shape={X_latest.shape}, "
                    f"finite={np.all(np.isfinite(X_latest))}, "
                    f"min={np.min(X_latest):.4f}, max={np.max(X_latest):.4f}")
        
        try:
            X_latest = scaler.transform(X_latest)
        except Exception as e:
            logging.error(f"Scaler transform failed for {sector}: {e}")
            logging.error(f"X_latest shape: {X_latest.shape}")
            logging.error(f"X_latest stats - min: {np.min(X_latest)}, max: {np.max(X_latest)}, mean: {np.mean(X_latest)}")
            logging.error(f"Contains inf: {np.isinf(X_latest).any()}, contains nan: {np.isnan(X_latest).any()}")
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
        
        # Ensure prediction is finite
        if not np.isfinite(prediction):
            logging.error(f"Non-finite prediction for {sector}")
            prediction = 0.0
        
        if prediction > 0.01:
            sentiment = "BULLISH"
        elif prediction < -0.01:
            sentiment = "BEARISH"
        else:
            sentiment = "NEUTRAL"
        
        dir_acc = metrics.get('test_dir_acc', 0)
        confidence = min(100, max(0, (dir_acc + abs(prediction) * 100) / 2))
        
        result = {
            'sector': sector,
            'ticker': SECTOR_TICKERS[sector],
            'predicted_return_pct': round(prediction * 100, 2),
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
        
        return convert_to_python_types(result)
    
    except Exception as e:
        logging.error(f"Error making prediction for {sector}: {e}")
        import traceback
        traceback.print_exc()
        return None

@app.on_event("startup")
async def startup_event():
    """Load models on startup"""
    logging.info("Starting API server...")
    load_all_models()
    logging.info("API server ready!")

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Stock Sector Prediction API",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/predict": "Get predictions for all sectors",
            "/predict/{sector}": "Get prediction for specific sector",
            "/models": "List all loaded models",
            "/docs": "Interactive API documentation"
        }
    }

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    global models_cache, last_cache_time
    
    if last_cache_time is None or (datetime.now() - last_cache_time).seconds > CACHE_DURATION:
        load_all_models()
    
    latest_training = None
    if models_cache:
        training_times = [m.get('timestamp') for m in models_cache.values() if m.get('timestamp')]
        if training_times:
            latest_training = max(training_times)
    
    return {
        "status": "healthy" if len(models_cache) > 0 else "degraded",
        "models_loaded": len(models_cache),
        "total_sectors": len(SECTOR_TICKERS),
        "last_training": latest_training
    }

@app.get("/models", response_model=Dict[str, Any])
async def list_models():
    """List all loaded models with metadata"""
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
    """Get predictions for all sectors"""
    global models_cache, last_cache_time
    
    if last_cache_time is None or (datetime.now() - last_cache_time).seconds > CACHE_DURATION:
        logging.info("Cache expired, reloading models...")
        load_all_models()
    
    if len(models_cache) == 0:
        raise HTTPException(status_code=503, detail="No models available. Please train models first.")
    
    predictions = []
    
    for sector, model_data in models_cache.items():
        prediction = make_prediction(sector, model_data)
        if prediction:
            predictions.append(prediction)
    
    if len(predictions) == 0:
        raise HTTPException(status_code=500, detail="Failed to generate predictions")
    
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
    
    return {
        "timestamp": datetime.now().isoformat(),
        "total_sectors": len(predictions),
        "predictions": predictions,
        "market_summary": {
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
    }

@app.get("/predict/{sector}", response_model=SectorPrediction)
async def predict_sector(sector: str):
    """Get prediction for a specific sector"""
    global models_cache, last_cache_time
    
    if last_cache_time is None or (datetime.now() - last_cache_time).seconds > CACHE_DURATION:
        load_all_models()
    
    if sector not in SECTOR_TICKERS:
        raise HTTPException(
            status_code=404, 
            detail=f"Sector '{sector}' not found. Available sectors: {list(SECTOR_TICKERS.keys())}"
        )
    
    if sector not in models_cache:
        raise HTTPException(
            status_code=503, 
            detail=f"Model for sector '{sector}' not available. Please train the model first."
        )
    
    prediction = make_prediction(sector, models_cache[sector])
    
    if prediction is None:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate prediction for sector '{sector}'"
        )
    
    return prediction

@app.post("/reload-models")
async def reload_models():
    """Manually reload all models from disk"""
    try:
        load_all_models()
        return {
            "status": "success",
            "message": f"Reloaded {len(models_cache)} models",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload models: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    if not os.path.exists("models"):
        logging.warning(" 'models/' directory not found. Creating it...")
        os.makedirs("models")
        logging.warning(" No models available yet. Please run the training pipeline first.")
    
    model_files = [f for f in os.listdir("models") if f.endswith('.pkl')] if os.path.exists("models") else []
    if len(model_files) == 0:
        logging.warning("No trained models found in 'models/' directory.")
        logging.warning("API will run but predictions will fail until models are trained.")
    else:
        logging.info(f"Found {len(model_files)} model files")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)