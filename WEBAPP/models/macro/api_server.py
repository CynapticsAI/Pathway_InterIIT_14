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
    logging.warning("⚠️  FRED_API_KEY not set! Set it with: export FRED_API_KEY='your_key'")
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
    """Load a trained model from disk"""
    filename = f"models/{sector.replace(' ', '_')}_model.pkl"
    
    try:
        if not os.path.exists(filename):
            logging.warning(f"Model file not found: {filename}")
            return None
        
        with open(filename, 'rb') as f:
            model_data = pickle.load(f)
        
        logging.info(f"✓ Loaded model for {sector}")
        return model_data
    except Exception as e:
        logging.error(f"Error loading model for {sector}: {e}")
        return None

def load_all_models():
    """Load all sector models into cache"""
    global models_cache, last_cache_time
    
    logging.info("Loading all models...")
    models_cache = {}
    
    if not os.path.exists("models"):
        logging.warning("⚠️  models/ directory not found. No models loaded.")
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
    
    for series_id in features:
        try:
            series = fred.get_series(series_id, observation_start=start_date)
            data[series_id] = series
        except Exception as e:
            logging.warning(f"Failed to fetch {series_id}: {e}")
            data[series_id] = pd.Series(dtype=float)
    
    if not data:
        return None
    
    df = pd.DataFrame(data)
    df.index = pd.to_datetime(df.index)
    df = df.resample("ME").last()
    
    for col in df.columns:
        df[col] = df[col].ffill().bfill().fillna(0.0)
    
    return df

def make_prediction(sector: str, model_data: Dict) -> Optional[Dict]:
    """Make prediction for a sector using loaded model"""
    try:
        model = model_data['model']
        features = model_data['features']
        metrics = model_data['metrics']
        
        df_fred = get_latest_fred_data(features)
        
        if df_fred is None or len(df_fred) == 0:
            logging.warning(f"No FRED data available for {sector}")
            return None
        
        available_features = [f for f in features if f in df_fred.columns]
        
        if len(available_features) == 0:
            logging.warning(f"No matching features for {sector}")
            return None
        
        X_prep = df_fred[available_features].ffill().pct_change().dropna()
        
        if len(X_prep) == 0:
            logging.warning(f"No data after preprocessing for {sector}")
            return None
        
        X_latest = X_prep.iloc[-1]
        X_latest = X_latest.replace([np.inf, -np.inf], np.nan).fillna(0).clip(-10, 10)
        
        prediction = model.predict(X_latest.values.reshape(1, -1))[0]
        print(prediction)
        if prediction > 0.02:
            sentiment = "BULLISH"
        elif prediction < -0.02:
            sentiment = "BEARISH"
        else:
            sentiment = "NEUTRAL"
        
        dir_acc = metrics.get('dir_acc', 0)
        confidence = min(100, max(0, (dir_acc * 100 + abs(prediction) * 100) / 2))
        
        result = {
            'sector': sector,
            'ticker': SECTOR_TICKERS[sector],
            'predicted_return_pct': round(prediction * 100, 2),
            'sentiment': sentiment,
            'confidence_score': round(confidence, 2),
            'model_metrics': {
                'rmse': round(metrics.get('rmse', 0), 4),
                'mae': round(metrics.get('mae', 0), 4),
                'dir_acc': round(metrics.get('dir_acc', 0), 4)
            },
            'last_updated': model_data.get('timestamp', datetime.now().isoformat()),
            'features_used': available_features
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
    logging.info("🚀 Starting API server...")
    load_all_models()
    logging.info("✅ API server ready!")

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
        logging.warning("⚠️  'models/' directory not found. Creating it...")
        os.makedirs("models")
        logging.warning("⚠️  No models available yet. Please run the training pipeline first.")
    
    model_files = [f for f in os.listdir("models") if f.endswith('.pkl')] if os.path.exists("models") else []
    if len(model_files) == 0:
        logging.warning("⚠️  No trained models found in 'models/' directory.")
        logging.warning("⚠️  API will run but predictions will fail until models are trained.")
    else:
        logging.info(f"✓ Found {len(model_files)} model files")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)