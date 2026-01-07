NOTE : The weights for the static version are the same as the live version of chronos. To avoid multiple instances of the same weights, we have 
saved the weights only once inside the STATIC/chronos_static/chronosConsumer/chronos-2-finetuned folder. Please copy-paste here to reproduce the results

<div align="center">
  <h1>Dual Pipeline Stock Forecasting System</h1>
  <p><strong>Real-time Stock Price Forecasting with Chronos-2 & SARIMAX, Powered by Pathway</strong></p>
</div>

<p align="center">
    <a href="#overview">Overview</a> |
    <a href="#project-structure">Project Structure</a> |
    <a href="#getting-started">Getting Started</a> |
    <a href="#architecture">Architecture</a> |
    <a href="#usage">Usage</a>
</p>

## Overview

A complete end-to-end streaming machine learning system featuring two parallel forecasting pipelines: **Chronos-2** (deep learning time series model) and **SARIMAX** (statistical model with volume/volatility spike detection). The system automatically selects the best-performing forecast based on windowed performance metrics. Real-time data from multiple sources (OHLC, tweets, Reddit) feeds into both pipelines through Kafka, simulating production streaming environments.

### Key Features

- **Dual Forecasting Pipelines**: Chronos-2 (deep learning) and SARIMAX (statistical) run in parallel for redundancy and comparison
- **Intelligent Model Selection**: Automatically switches to the best-performing forecast based on recent window performance
- **Spike Detection**: Real-time volume and volatility anomaly detection feeding into SARIMAX
- **Multimodal Data Integration**: Ingests OHLC data, Twitter sentiment, and Reddit posts
- **Continuous Learning**: Both models retrain automatically on latest data windows
- **Hot Model Reloading**: Chronos-2 dynamically loads updated checkpoints without downtime
- **Stream Simulation**: Kafka producers replay historical data at configurable frequencies
- **Temporal Joins**: Leverages Pathway's temporal join capabilities for data alignment
- **Dockerized Deployment**: Complete stack orchestrated with Docker Compose

## Project Structure

```
chronos/
├── chronosConsumer/                      # Chronos-2 deep learning pipeline
│   ├── chronos-2-finetuned/              # Pretrained Chronos-2 weights
│   ├── chronos_output/                   # Training checkpoints directory
│   ├── heartbeat/                        # Training heartbeat monitoring
│   ├── chronos_infer.py                  # Inference (hot-reloads models)
│   ├── chronos_train.py                  # Training pipeline
│   ├── embed.py                          # FinBERT embeddings generator
│   ├── Dockerfile
│   └── requirements.txt
├── ohlcProducer/                         # OHLC data producer
│   ├── data_TSLA_sorted.csv              # Historical OHLC data
│   ├── ohlcProducer.py                   # Kafka producer
│   ├── Dockerfile
│   └── requirements.txt
├── tweetProducer/                        # Twitter sentiment data producer
│   ├── stock_tweets_sorted.csv           # Historical tweet data
│   ├── tweetProducer.py                  # Kafka producer
│   ├── Dockerfile
│   └── requirements.txt
├── redditProducer/                       # Reddit sentiment data producer
│   ├── reddit_tesla.csv                  # Historical Reddit posts
│   ├── redditProducer.py                 # Kafka producer
│   ├── Dockerfile
│   └── requirements.txt
├── sarimaxConsumer/                      # SARIMAX statistical pipeline
│   ├── sarimax_forecast.py               # SARIMAX forecasting & feature extraction
│   ├── output/                           # Forecast outputs
│   ├── Dockerfile
│   └── requirements.txt
├── spike_detector/                       # Volume & volatility anomaly detection
│   ├── spike_detector.py                 # Z-score based spike detection
│   ├── output/                           # Spike alerts & volatility metrics
│   ├── Dockerfile
│   └── requirements.txt
├── selection/                            # Model selection & switching
│   ├── select_model.py                   # Selects best forecast based on performance
|   |-- test_pipeline.py                  # metrics verification
│   ├── output/                           # Final selected predictions
│   ├── Dockerfile
│   └── requirements.txt
├── output/                               # Final outputs directory
├── docker-compose.yml                    # Orchestrates entire stack
└── README.md
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Hugging Face account with access to Chronos-2 model
- Python 3.10+ (for local development)

### Installation

1. **Hugging Face Authentication**:

Login to Hugging Face Hub to access the Chronos-2 model:

```bash
huggingface-cli login
```

Enter your Hugging Face token when prompted.

2. **Launch the entire pipeline**:

```bash
docker-compose up --build
```

That's it! The system will:
- Start Kafka and Zookeeper
- Launch data producers (OHLC, tweets, Reddit)
- Run spike detector on OHLC data
- Start SARIMAX pipeline with spike detection features
- Begin Chronos-2 training pipeline (saves checkpoints every 60s)
- Start Chronos-2 inference pipeline (reloads models every 60s)
- Run model selection (compares both forecasts, outputs best prediction)
- Generate final predictions to `output/final_combined_signal.jsonl`

## Architecture

### Data Flow Overview

```
┌─────────────────────────────────────────────────────────┐
│ Data Sources (Kafka Producers)                          │
├──────────┬──────────────┬──────────────────────────────┤
│ OHLC     │ Tweets       │ Reddit Posts                 │
│ Producer │ Producer     │ Producer                     │
└──────────┴──────┬───────┴──────────────┬───────────────┘
                  │                      │
           ┌──────▼──────────────────────▼─────────┐
           │ Spike Detector                        │
           │ (Volume & Volatility Anomalies)       │
           └──────┬──────────────────────────────┬─┘
                  │                              │
        ┌─────────▼──────────┐        ┌──────────▼────────────┐
        │ CHRONOS PIPELINE   │        │ SARIMAX PIPELINE      │
        ├────────────────────┤        ├─────────────────────┤
        │ • Train            │        │ • Consume OHLC       │
        │ • Infer            │        │ • Use spike features  │
        │ • Output forecast  │        │ • Consume Reddit     │
        └─────────┬──────────┘        │ • Output forecast    │
                  │                   └──────────┬───────────┘
                  │                              │
                  └──────────────┬───────────────┘
                                 │
                        ┌────────▼──────────┐
                        │ Model Selection   │
                        │ (Choose Best)     │
                        └────────┬──────────┘
                                 │
                        ┌────────▼──────────┐
                        │ Final Output      │
                        │ (Best Forecast)   │
                        └───────────────────┘
```

### Components

#### 1. **Kafka Producers** (Data Simulation)

##### `ohlcProducer/ohlcProducer.py`
- Reads historical OHLC data from `data_TSLA_sorted.csv`
- Publishes to Kafka topic `ohlc` at configurable frequency
- Simulates real-time market data stream

##### `tweetProducer/tweetProducer.py`
- Reads historical tweets from `stock_tweets_sorted.csv`
- Publishes to Kafka topic `tweets` at configurable frequency
- Simulates real-time social media sentiment stream

##### `redditProducer/redditProducer.py`
- Reads historical Reddit posts from `reddit_tesla.csv`
- Publishes to Kafka topic `reddit` at configurable frequency
- Provides alternative sentiment stream

#### 2. **Spike Detector** (`spike_detector/`)

**Input:**
- Consumes from Kafka topic: `ohlc`

**Processing:**
- Maintains 30-minute rolling window of OHLC bars
- Calculates volume and price range statistics
- Computes Z-scores for volume and volatility
- Categorizes risk levels:
  - **CRITICAL**: Both volume and volatility Z-scores > 5.0
  - **HIGH**: Both volume and volatility Z-scores > 3.0
  - **MEDIUM**: Either volume or volatility Z-score > 3.0
  - **LOW**: Default

**Output:**
- Publishes to Kafka topic: `volume_volatility_data`
- Writes spike alerts and volatility metrics to JSONL files
- Feeds spike features into SARIMAX pipeline

#### 3. **Chronos-2 Pipeline** (`chronosConsumer/`)

##### `chronos_train.py` - Training Pipeline
**Input:**
- Consumes from Kafka topics: `ohlc`, `tweets`
- Uses pretrained weights from `chronos-2-finetuned/`

**Processing:**
- Performs temporal asof joins to align tweets with price data
- Maintains 120-minute sliding windows (1-minute hop)
- Extracts features:
  - Log returns from close prices
  - OHLC values and log-transformed volume
  - FinBERT embeddings (PCA-reduced to 16 dimensions)
  - Only tweets within 10 minutes of price updates are used

**Output:**
- Retrains model every 60 seconds on latest window
- Saves checkpoints to `chronos_output/{timestamp}/finetuned-ckpt/`
- Writes heartbeat to `heartbeat/c_.csv` for monitoring

##### `chronos_infer.py` - Inference Pipeline
**Input:**
- Consumes same Kafka streams with identical preprocessing
- Monitors `chronos_output/` for new checkpoints

**Processing:**
- Generates 10-step ahead forecasts every minute
- Checks for updated model weights every 60 seconds
- Hot-swaps to latest checkpoint with thread-safe locking
- No downtime during model updates

**Output:**
- Predictions in JSON format
- Feeds to model selection component

#### 4. **SARIMAX Pipeline** (`sarimaxConsumer/`)

**Input:**
- Consumes from Kafka topics: `ohlc`, `reddit`, `volume_volatility_data`
- Uses spike detection features from spike detector

**Processing:**
- Fits SARIMAX model on 60-minute lookback window
- Updates forecasts every minute
- Incorporates volume and volatility spike features
- Computes technical indicators:
  - RSI (Relative Strength Index)
  - Price momentum
  - Volume momentum
  - Volatility metrics

**Output:**
- Forecast prices and confidence metrics
- Feeds to model selection component

#### 5. **Model Selection** (`selection/`)

**Input:**
- Consumes from both `chronos_infer.py` and `sarimax_forecast.py`
- Tracks performance metrics for both models on rolling windows

**Processing:**
- Maintains windowed performance history
- Compares forecast accuracy of both models
- Selects the model with better recent performance
- Automatically switches between Chronos and SARIMAX

**Output:**
- Best available forecast to `output/final_combined_signal.jsonl`
- Includes:
  - Selected model indicator
  - Forecast price
  - Confidence metrics
  - Timestamp and metadata

#### 6. **Utility Scripts**

##### `test_pipeline.py`
- Evaluates model performance on static CSV data
- Computes metrics (MAE, RMSE, etc.)
- Useful for offline validation

## Usage

### Running the Full Pipeline

```bash
# Start everything
docker-compose up --build

# Run in detached mode
docker-compose up -d --build

# View logs
docker-compose logs -f chronos-train
docker-compose logs -f chronos-infer
docker-compose logs -f sarimax
docker-compose logs -f spike-detector
docker-compose logs -f selection

# Stop all services
docker-compose down
```

### Local Testing

**Test Chronos on static data**:
```bash
cd chronos/chronosConsumer
python embed.py  # creates embedding csv for tweets
python chronos_test.py # trains, tests and provides metrics
```

## Configuration

### Key Parameters

#### Training (`chronos_train.py`)
```python
TRAIN_INTERVAL_SEC = 60    # Seconds between model updates
PAST_LEN = 20              # Historical context length
NUM_STEPS = 50             # Training steps per update
LR = 1e-5                  # Learning rate
BATCH_SIZE = 32            # Training batch size
HORIZON = 10               # Forecast horizon
```

#### Inference (`chronos_infer.py`)
```python
RELOAD_EVERY_SEC = 60      # Seconds between checkpoint checks
HORIZON = 10               # Forecast horizon (must match training)
```

#### Spike Detector (`spike_detector/spike_detector.py`)
```python
ROLLING_WINDOW_DURATION = "30m"  # Baseline window for statistics
ROLLING_WINDOW_HOP = "1m"        # Frequency of spike checks
SPIKE_THRESHOLD = 3.0            # Z-score threshold (3.0 = 3-sigma)
MIN_BARS_FOR_STATS = 5           # Minimum bars to compute statistics
```

#### SARIMAX (`sarimaxConsumer/sarimax_forecast.py`)
```python
WINDOW_DURATION = "30m"    # Length of data for analysis
WINDOW_HOP = "1m"          # Forecast frequency
SARIMAX_LOOKBACK = 60      # Number of bars for fitting
WARM_UP_TIME = 5           # Minimum bars before first forecast
```

#### Model Selection (`selection/select_model.py`)
```python
PERFORMANCE_WINDOW = "30m" # Window for calculating model performance
REEVAL_INTERVAL = "1m"     # Frequency of model switching decisions
```

#### Producers
```python
# Adjust streaming frequency in producer files
PUBLISH_INTERVAL = 1.0     # Seconds between messages (OHLC)
TWEET_INTERVAL = 2.5       # Seconds between tweets
REDDIT_INTERVAL = 2.5      # Seconds between Reddit posts
```

### Kafka Topics

| Topic | Producer | Schema | Description |
|-------|----------|--------|-------------|
| `ohlc` | ohlcProducer | `timestamp, open, high, low, close, volume` | Stock OHLC data |
| `tweets` | tweetProducer | `Date, Tweet, Company_Name` | Twitter sentiment |
| `reddit` | redditProducer | `Date, Post` | Reddit sentiment |
| `volume_volatility_data` | spike_detector | `timestamp, symbol, volume_zscore, volatility_zscore, risk_level` | Spike detection results |
| `chronos_forecast` | chronos_infer | `predictions, confidence, timestamp` | Chronos-2 forecasts |
| `sarimax_forecast` | sarimax_forecast | `forecast, metrics, timestamp` | SARIMAX forecasts |
| `final_forecast` | selection | `forecast, selected_model, timestamp` | Selected best forecast |

### Output Files

| File | Location | Purpose |
|------|----------|---------|
| `final_combined_signal.jsonl` | `output/` | Final selected predictions |
| `sarimax_forecast.jsonl` | `sarimaxConsumer/output/` | SARIMAX forecasts |
| `spike_alerts.jsonl` | `spike_detector/output/` | Volume/volatility spike alerts |
| `volume_volatility.jsonl` | `spike_detector/output/` | Rolling volatility statistics |
| `combinedStream.csv` | `chronosConsumer/` | Chronos-2 predictions |

### Environment Variables

Sample .env files are provided in respective component directories. Rename and add your API keys as needed.


## License

This project uses:
- **Pathway**: [BSL 1.1 License](https://pathway.com/license/)
- **Chronos**: Amazon Science License
- **FinBERT**: Apache 2.0 License

## Acknowledgments

Built with:
- [Pathway](https://pathway.com/) - Live data framework
- [Chronos-2](https://github.com/amazon-science/chronos-forecasting) - Time series foundation model
- [FinBERT](https://github.com/ProsusAI/finBERT) - Financial sentiment analysis

---

<div align="center">
  <strong>Real-time ML Pipeline powered by <a href="https://pathway.com/">Pathway</a></strong>
</div>
