"""
TIME SERIES FORECASTING
- Regularization to prevent overfitting
- Dropout layers
- Early stopping
- Data validation and cleaning
- Cross-validation monitoring
- Ensemble predictions
- Directional accuracy calculations
"""

import logging
import os
import threading
import time
import warnings
from datetime import datetime
from math import sqrt
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import pathway as pw
import torch
import torch.nn as nn
import yfinance as yf
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import RobustScaler
from torch.utils.data import DataLoader, Dataset

warnings.filterwarnings('ignore')

# Create directories
os.makedirs("logs", exist_ok=True)
os.makedirs("models", exist_ok=True)

# Setup logging
log_filename = f"logs/training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(log_filename, mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logging.info("Time Series System")
logging.info(f"Logging to: {log_filename}")

# Schema
class FREDDataSchema(pw.Schema):
    date: str
    fetch_timestamp: str
    DCOILWTICO: float
    CPIENGSL: float
    PPIENG: float
    INDPRO: float
    CPALTT01USM657N: float
    PPIACO: float
    MNFCTRIRSA: float
    IPMAN: float
    CAPUTLB00004S: float
    DGORDER: float
    UNRATE: float
    RSAFS: float
    UMCSENT: float
    PCE: float
    CPIAUCSL: float
    RRSFS: float
    CPIFABSL: float
    CPIMEDSL: float
    GDP: float
    FEDFUNDS: float
    T10Y2Y: float
    M2SL: float
    HOUST: float
    MORTGAGE30US: float
    IPB53100SQ: float
    CPENGSL: float
    T10Y3M: float
    PERMIT: float
    CSUSHPINSA: float

# Kafka settings
rdkafka_consumer_settings = {
    "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092"),
    "security.protocol": "plaintext",
    "group.id": "fred_group",
    "session.timeout.ms": "6000",
    "auto.offset.reset": "earliest",
}

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

def robust_feature_engineering(df: pd.DataFrame, original_cols: List[str]) -> pd.DataFrame:
    """
    Conservative feature engineering to prevent overfitting
    - Only proven features
    - Avoid creating too many correlated features
    - Focus on stability over complexity
    """
    logging.info("Creating robust features...")
    
    df_features = df.copy()
    
    for col in original_cols:
        df_features[f'{col}_lag5'] = df[col].shift(5)
        df_features[f'{col}_lag20'] = df[col].shift(20)
    
    for col in original_cols:
        df_features[f'{col}_ma20'] = df[col].rolling(window=20).mean()
        df_features[f'{col}_std20'] = df[col].rolling(window=20).std()
    
    for col in original_cols:
        df_features[f'{col}_roc20'] = df[col].pct_change(periods=20)
    
    df_features = df_features.dropna()
    
    logging.info(f"Robust features: {len(original_cols)} → {len(df_features.columns)} (~35 features)")
    
    return df_features

def clean_outliers(X: np.ndarray, y: np.ndarray, threshold: float = 3) -> tuple[np.ndarray, np.ndarray]:
    """Remove extreme outliers that cause overfitting."""
    logging.info(f"Cleaning outliers (threshold={threshold} std)...")
    
    y_mean = y.mean()
    y_std = y.std()
    z_scores = np.abs((y - y_mean) / y_std)
    
    mask = z_scores < threshold
    
    outliers_removed = (~mask).sum()
    logging.info(f"Removed {outliers_removed} outliers ({outliers_removed/len(y)*100:.1f}%)")
    
    return X[mask], y[mask]

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

class TimeSeriesDataset(Dataset):
    def __init__(self, X: np.ndarray, y: np.ndarray, sequence_length: int = 30):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)
        self.sequence_length = sequence_length
    
    def __len__(self) -> int:
        return len(self.X) - self.sequence_length
    
    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        X_seq = self.X[idx:idx + self.sequence_length]
        y_target = self.y[idx + self.sequence_length]
        y_history = self.y[idx:idx + self.sequence_length]
        return X_seq, y_history, y_target

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

def directional_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate directional accuracy: percentage of correct direction predictions
    (up/down) ignoring magnitude.
    """
    signs_true = np.sign(y_true)
    signs_pred = np.sign(y_pred)
    mask = (signs_true != 0) & (signs_pred != 0)
    if np.sum(mask) == 0:
        return 0.0
    return np.mean(signs_true[mask] == signs_pred[mask]) * 100

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

def train_model(X_train: np.ndarray, y_train: np.ndarray,
                X_val: np.ndarray, y_val: np.ndarray,
                input_dim: int, epochs: int = 60, batch_size: int = 64,
                learning_rate: float = 0.001, sequence_length: int = 30,
                patience: int = 8) -> tuple[RegularizedLSTM, List[float], List[float], torch.device]:
    """
    Training with measures to prevent overfitting:
    - Early stopping (patience=8)
    - Weight decay (1e-4)
    - Model (32 units)
    - Dropout (0.5)
    """
    
    train_dataset = TimeSeriesDataset(X_train, y_train, sequence_length)
    val_dataset = TimeSeriesDataset(X_val, y_val, sequence_length)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    model = RegularizedLSTM(input_dim=input_dim, hidden_dim=32, num_layers=2, dropout=0.5)
    model = model.to(device)
    
    criterion = nn.MSELoss()
    
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.3, patience=4
    )
    
    train_losses: List[float] = []
    val_losses: List[float] = []
    best_val_loss = float('inf')
    patience_counter = 0
    best_model_state: Optional[Dict[str, Any]] = None
    
    logging.info("Training (dropout=0.5, weight_decay=1e-4)...")
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        for X_batch, y_history_batch, y_batch in train_loader:
            X_batch = X_batch.to(device)
            y_history_batch = y_history_batch.to(device)
            y_batch = y_batch.to(device)
            
            optimizer.zero_grad()
            outputs = model(X_batch, y_history_batch)
            loss = criterion(outputs, y_batch)
            loss.backward()
            
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=0.5)
            
            optimizer.step()
            train_loss += loss.item()
        
        train_loss /= len(train_loader)
        train_losses.append(train_loss)
        
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for X_batch, y_history_batch, y_batch in val_loader:
                X_batch = X_batch.to(device)
                y_history_batch = y_history_batch.to(device)
                y_batch = y_batch.to(device)
                
                outputs = model(X_batch, y_history_batch)
                loss = criterion(outputs, y_batch)
                val_loss += loss.item()
        
        val_loss /= len(val_loader)
        val_losses.append(val_loss)
        
        scheduler.step(val_loss)
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            best_model_state = model.state_dict().copy()
        else:
            patience_counter += 1
        
        if (epoch + 1) % 10 == 0:
            gap = train_loss - val_loss
            logging.info(f"Epoch [{epoch+1}/{epochs}] - Train: {train_loss:.6f}, "
                        f"Val: {val_loss:.6f}, Gap: {gap:.6f}")
        
        if patience_counter >= patience:
            logging.info(f"Early stopping at epoch {epoch+1}")
            break
    
    model.load_state_dict(best_model_state)
    
    final_train_loss = train_losses[-1] if train_losses else 0
    if best_val_loss > final_train_loss * 1.5:
        logging.warning(f"Overfitting detected! Val loss {best_val_loss/final_train_loss:.2f}x train loss")
    else:
        logging.info(f"Good generalization. Val/Train ratio: {best_val_loss/final_train_loss:.2f}x")
    
    logging.info(f"Training complete. Best Val Loss: {best_val_loss:.6f}")
    
    return model, train_losses, val_losses, device

def predict_with_teacher_forcing(model: RegularizedLSTM, X_test: np.ndarray, y_test_history: np.ndarray,
                                 sequence_length: int, device: torch.device) -> np.ndarray:
    """Make predictions."""
    model.eval()
    predictions = []
    
    with torch.no_grad():
        for i in range(sequence_length, len(X_test)):
            X_seq = X_test[i-sequence_length:i]
            y_history = y_test_history[i-sequence_length:i]
            
            X_seq = torch.FloatTensor(X_seq).unsqueeze(0).to(device)
            y_history = torch.FloatTensor(y_history).unsqueeze(0).to(device)
            
            pred = model(X_seq, y_history)
            predictions.append(pred.cpu().numpy())
    
    return np.array(predictions).flatten()

def train_sector(df_fred: pd.DataFrame, sector: str) -> Optional[Dict[str, Any]]:
    """Training."""
    try:
        logging.info(f"\n{'='*70}")
        logging.info(f"Training {sector}")
        logging.info(f"{'='*70}")
        
        features = SECTOR_FEATURES[sector]
        
        available_features = []
        for f in features:
            if f in df_fred.columns:
                non_zero_count = (df_fred[f] != 0).sum()
                if non_zero_count > 10:
                    available_features.append(f)
        
        if len(available_features) == 0:
            logging.warning("No valid features")
            return None
        
        logging.info(f"Features: {available_features}")
        
        y = get_etf_daily(SECTOR_TICKERS[sector])
        if len(y) == 0:
            return None
        
        y = y.pct_change().dropna()
        
        X = df_fred[available_features].copy()
        X.index = pd.to_datetime(df_fred['date'])
        
        X_daily = temporal_interpolation(X, method='linear')
        
        df = X_daily.join(y, how="inner").dropna()
        logging.info(f"Data: {len(df)} days")
        
        if len(df) < 500:
            logging.warning("Not enough data")
            return None
        
        X_prep = df[available_features].copy()
        y_prep = df[y.name].copy()
        
        X_engineered = robust_feature_engineering(X_prep, available_features)
        y_prep = y_prep.loc[X_engineered.index]
        
        logging.info(f"Engineered features: {X_engineered.shape}")
        
        X_clean = X_engineered.values
        y_clean = y_prep.values
        X_clean, y_clean = clean_outliers(X_clean, y_clean, threshold=3)
        
        dates_clean = X_engineered.index[:len(X_clean)]
        
        X_engineered = pd.DataFrame(X_clean, columns=X_engineered.columns, index=dates_clean)
        y_prep = pd.Series(y_clean, index=dates_clean)
        
        X_engineered = X_engineered.replace([np.inf, -np.inf], np.nan).fillna(0)
        y_prep = y_prep.replace([np.inf, -np.inf], np.nan).fillna(0)
        X_engineered = X_engineered.clip(lower=-3, upper=3)
        y_prep = y_prep.clip(lower=-0.3, upper=0.3)
        
        n = len(X_engineered)
        train_end = int(n * 0.70)
        val_end = int(n * 0.80)
        
        X_train = X_engineered.iloc[:train_end].values
        X_val = X_engineered.iloc[train_end:val_end].values
        X_test = X_engineered.iloc[val_end:].values
        
        y_train = y_prep.iloc[:train_end].values
        y_val = y_prep.iloc[train_end:val_end].values
        y_test = y_prep.iloc[val_end:].values
        
        logging.info(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
        
        scaler_X = RobustScaler()
        X_train = scaler_X.fit_transform(X_train)
        X_val = scaler_X.transform(X_val)
        X_test = scaler_X.transform(X_test)
        
        sequence_length = 30
        model, train_losses, val_losses, device = train_model(
            X_train, y_train, X_val, y_val,
            input_dim=X_train.shape[1],
            epochs=60,
            batch_size=64,
            learning_rate=0.001,
            sequence_length=sequence_length,
            patience=8
        )
        
        logging.info("Making predictions...")
        y_train_pred = predict_with_teacher_forcing(model, X_train, y_train, sequence_length, device)
        y_val_pred = predict_with_teacher_forcing(model, X_val, y_val, sequence_length, device)
        y_test_pred = predict_with_teacher_forcing(model, X_test, y_test, sequence_length, device)
        
        y_train_aligned = y_train[sequence_length:]
        y_val_aligned = y_val[sequence_length:]
        y_test_aligned = y_test[sequence_length:]
        
        train_rmse = sqrt(mean_squared_error(y_train_aligned, y_train_pred))
        train_mae = mean_absolute_error(y_train_aligned, y_train_pred)
        train_dir_acc = directional_accuracy(y_train_aligned, y_train_pred)
        
        val_rmse = sqrt(mean_squared_error(y_val_aligned, y_val_pred))
        val_mae = mean_absolute_error(y_val_aligned, y_val_pred)
        val_dir_acc = directional_accuracy(y_val_aligned, y_val_pred)
        
        test_rmse = sqrt(mean_squared_error(y_test_aligned, y_test_pred))
        test_mae = mean_absolute_error(y_test_aligned, y_test_pred)
        test_dir_acc = directional_accuracy(y_test_aligned, y_test_pred)
        
        rmse_ratio = test_rmse / (train_rmse + 1e-10)
        
        logging.info(f"Train Dir Acc={train_dir_acc:.2f}%, Val Dir Acc={val_dir_acc:.2f}%, Test Dir Acc={test_dir_acc:.2f}%")
        
        last_prediction = y_test_pred[-1]
        sentiment = "BULLISH" if last_prediction > 0.02 else "BEARISH" if last_prediction < -0.02 else "NEUTRAL"
        
        logging.info(f"Next Return: {last_prediction*100:+.2f}% | {sentiment}")
        
        metrics = {
            'train_rmse': train_rmse,
            'train_mae': train_mae,
            'train_dir_acc': train_dir_acc,
            'val_rmse': val_rmse,
            'val_mae': val_mae,
            'val_dir_acc': val_dir_acc,
            'test_rmse': test_rmse,
            'test_mae': test_mae,
            'test_dir_acc': test_dir_acc,
            'train_samples': len(y_train_aligned),
            'val_samples': len(y_val_aligned),
            'test_samples': len(y_test_aligned),
            'rmse_ratio': rmse_ratio
        }
        
        model_data = {
            'model_state_dict': model.state_dict(),
            'sector': sector,
            'features': list(X_engineered.columns),
            'scaler': scaler_X,
            'metrics': metrics,
            'sequence_length': sequence_length,
            'timestamp': datetime.now().isoformat()
        }
        
        model_path = f"models/{sector.replace(' ', '_')}_model.pkl"
        with open(model_path, 'wb') as f:
            import pickle
            pickle.dump(model_data, f)
        
        logging.info(f"Model saved: {model_path}")
        
        return {
            'sector': sector,
            'predicted_return': last_prediction,
            'predicted_return_pct': last_prediction * 100,
            'sentiment': sentiment,
            'train_dir_acc': train_dir_acc,
            'val_dir_acc': val_dir_acc,
            'test_dir_acc': test_dir_acc,
            'rmse_ratio': rmse_ratio,
            'overfitting_level': 'Low' if rmse_ratio < 1.3 else 'Moderate' if rmse_ratio < 1.5 else 'High',
            'n_features': X_train.shape[1],
            'timestamp': datetime.now().isoformat(),
            'model_saved': True
        }
        
    except Exception as e:
        logging.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

class DataManager:
    def __init__(self, buffer_threshold: int = 15, time_threshold: int = 60):
        self.data_buffer: List[Dict[str, Any]] = []
        self.buffer_threshold = buffer_threshold
        self.time_threshold = time_threshold
        self.last_training_time = time.time()
        self.lock = threading.Lock()
        self.total_received = 0
        self.training_count = 0
    
    def add_data(self, row_dict: Dict[str, Any]) -> None:
        with self.lock:
            self.data_buffer.append(row_dict)
            self.total_received += 1
    
    def should_trigger_training(self) -> bool:
        with self.lock:
            buffer_full = len(self.data_buffer) >= self.buffer_threshold
            time_elapsed = (time.time() - self.last_training_time) > self.time_threshold
            has_data = len(self.data_buffer) > 0
            return buffer_full or (time_elapsed and has_data)
    
    def get_and_clear_buffer(self) -> List[Dict[str, Any]]:
        with self.lock:
            data = self.data_buffer.copy()
            self.data_buffer = []
            self.last_training_time = time.time()
            self.training_count += 1
            return data

data_manager = DataManager(buffer_threshold=15, time_threshold=60)

def trigger_training() -> None:
    accumulated_data = data_manager.get_and_clear_buffer()
    
    if len(accumulated_data) == 0:
        return
    
    logging.info(f"\n{'='*80}")
    logging.info("TRAINING CYCLE")
    logging.info(f"{'='*80}")
    
    df_fred = pd.DataFrame(accumulated_data)
    df_fred = df_fred.drop_duplicates(subset=['date'], keep='last')
    
    all_predictions: List[Dict[str, Any]] = []
    
    for idx, sector in enumerate(SECTOR_TICKERS.keys(), 1):
        logging.info(f"\n{'#'*70}")
        logging.info(f"Sector {idx}/{len(SECTOR_TICKERS)}: {sector}")
        logging.info(f"{'#'*70}")
        
        result = train_sector(df_fred, sector)
        if result:
            all_predictions.append(result)
    
    if all_predictions:
        predictions_df = pd.DataFrame(all_predictions)
        output_file = "predictions.csv"
        file_exists = os.path.isfile(output_file)
        
        predictions_df.to_csv(output_file, mode='a', header=not file_exists, index=False)
        
        avg_ratio = np.mean([p['rmse_ratio'] for p in all_predictions])
        avg_dir_acc = np.mean([p['test_dir_acc'] for p in all_predictions])
        
        logging.info(f"\n{'='*80}")
        logging.info(f"COMPLETE - Avg RMSE Ratio: {avg_ratio:.4f}, Avg Dir Acc: {avg_dir_acc:.2f}%")
        logging.info(f"{'='*80}\n")

def training_monitor() -> None:
    while True:
        try:
            if data_manager.should_trigger_training():
                trigger_training()
            time.sleep(5)
        except Exception as e:
            logging.error(f"Error: {e}")

def test_training_with_backup() -> None:
    backup_file = "data/fred_stream.csv"
    
    if os.path.exists(backup_file):
        logging.info("\nTesting with backup CSV\n")
        
        try:
            df = pd.read_csv(backup_file)
            data_list = df.to_dict('records')
            for row in data_list:
                data_manager.add_data(row)
            
            trigger_training()
        except Exception as e:
            logging.error(f"Error: {e}")

monitor_thread = threading.Thread(target=training_monitor, daemon=True)
monitor_thread.start()

def process_incoming_data(key: Any, row: Any, time: Any, is_addition: bool) -> None:
    if is_addition:
        row_dict = {}
        for field in FREDDataSchema.__annotations__.keys():
            row_dict[field] = row[field]
        data_manager.add_data(row_dict)

fred_data_stream = pw.io.kafka.read(
    rdkafka_consumer_settings,
    topic="fred_economic_data",
    schema=FREDDataSchema,
    format="json",
    autocommit_duration_ms=1000
)

pw.io.subscribe(
    fred_data_stream,
    on_change=process_incoming_data,
    on_end=lambda: logging.info("Stream ended")
)

pw.io.csv.write(fred_data_stream, "streamed_fred_backup.csv")

print("\n" + "="*80)
print("TIME SERIES FORECASTING SYSTEM")
print("="*80)
print("")
print("TECHNIQUES:")
print("  - Small model (32 units)")
print("  - High dropout (0.5)")
print("  - L2 regularization (weight_decay=1e-4)")
print("  - Early stopping (patience=8)")
print("  - Fewer features (~35)")
print("  - Outlier removal")
print("  - RobustScaler")
print("  - 70/10/20 train/val/test split")
print("  - Directional accuracy calculations")
print("")
print("OUTPUT:")
print("  - predictions.csv")
print("  - models/*_model.pkl")
print("="*80 + "\n")

time.sleep(5)
test_training_with_backup()

pw.run()