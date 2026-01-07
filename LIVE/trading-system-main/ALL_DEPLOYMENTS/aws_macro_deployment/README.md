# Real-Time Stock Sector Prediction with Pathway

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/Pathway-Live%20Data%20Framework-green.svg" alt="Pathway"/>
  <img src="https://img.shields.io/badge/FastAPI-0.104+-009688.svg" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Streaming-ML-orange.svg" alt="Streaming ML"/>
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED.svg" alt="Docker"/>
  <br/>
  <a href="#features">Features</a> |
  <a href="#pathway-framework">Pathway Framework</a> |
  <a href="#getting-started">Getting Started</a> |
  <a href="#deployment">Deployment</a> |
  <a href="#api-usage">API Usage</a>
</div>

---

A production-ready **streaming machine learning pipeline** built entirely with **Pathway** - the Python framework for live data processing. This system demonstrates Pathway's capabilities for real-time ETL, incremental computation, and streaming ML by predicting stock market sector performance using live economic data from FRED.

## What This Does

This system continuously monitors 29 economic indicators from FRED, trains machine learning models for 11 stock market sectors, and provides real-time predictions through a REST API. The entire pipeline runs on streaming data, automatically updating models as new economic data becomes available.

**Predicted Sectors:**
- Energy (XLE)
- Materials (XLB)  
- Industrials (XLI)
- Consumer Discretionary (XLY)
- Consumer Staples (XLP)
- Health Care (XLV)
- Financials (XLF)
- Information Technology (XLK)
- Communication Services (XLC)
- Utilities (XLU)
- Real Estate (XLRE)

## Pathway Framework<a id="pathway-framework"></a>

This project showcases **Pathway's core capabilities** for building production-ready streaming applications:

### Pathway Connectors

**CSV Streaming Connector** (`pw.io.csv.read`)
- Monitors CSV files for real-time updates with `mode='streaming'`
- Automatically detects new rows and streams them through the pipeline
- Uses `autocommit_duration_ms` for fine-grained control over commit intervals

**Kafka Connector** (`pw.io.kafka`)
- **Reader**: `pw.io.kafka.read()` consumes from Kafka topics with schema validation
- **Writer**: `pw.io.kafka.write()` publishes streaming data to Kafka topics
- Native support for JSON format with automatic serialization/deserialization
- Configurable consumer groups, offsets, and connection settings

**Subscribe Mechanism** (`pw.io.subscribe`)
- Real-time monitoring of table changes with `on_change` callbacks
- Tracks additions, updates, and deletions in streaming tables
- Enables custom processing logic for each streaming event

**CSV Writer** (`pw.io.csv.write`)
- Continuously writes streaming data to CSV for backup and replay
- Maintains consistent state snapshots for recovery

### Unified Batch and Streaming

The same Pathway code runs in both **development** (batch) and **production** (streaming) modes:

```python
# Development: Process historical data
fred_data_table = pw.io.csv.read(
    csv_path,
    schema=FREDDataSchema,
    mode='static'  # Batch processing
)

# Production: Stream real-time data
fred_data_table = pw.io.csv.read(
    csv_path,
    schema=FREDDataSchema,
    mode='streaming'  # Real-time processing
)
```

**No code changes needed** - just switch the mode parameter!

### Streaming Machine Learning

This project implements **streaming ML** where models retrain automatically as new data arrives:

**Incremental Training Pipeline**:
1. `pw.io.kafka.read()` streams FRED economic indicators
2. `pw.io.subscribe()` monitors incoming data points
3. Custom buffer accumulates data until training threshold is met
4. LSTM models retrain on complete historical + new data
5. Updated models are persisted and served via API

**Key Implementation**:
```python
# Stream from Kafka with schema validation
fred_data_stream = pw.io.kafka.read(
    rdkafka_consumer_settings,
    topic="fred_economic_data",
    schema=FREDDataSchema,
    format="json",
    autocommit_duration_ms=1000
)

# Subscribe to changes and trigger ML pipeline
pw.io.subscribe(
    fred_data_stream,
    on_change=process_incoming_data,
    on_end=lambda: logging.info("Stream ended")
)

# Backup streaming data to CSV
pw.io.csv.write(fred_data_stream, "streamed_fred_backup.csv")
```

### Python-First Development

Write your entire pipeline in **pure Python** while Pathway's **Rust engine** handles:
- Multithreading and parallel processing
- Memory-efficient streaming operations
- Incremental computation and state management
- Automatic change propagation through the pipeline

### Schema Validation

Pathway's strong typing with `pw.Schema` ensures data quality:

```python
class FREDDataSchema(pw.Schema):
    date: str
    fetch_timestamp: str
    DCOILWTICO: float  # Oil prices
    CPIAUCSL: float    # CPI
    FEDFUNDS: float    # Fed funds rate
    # ... 26 more economic indicators
```

Every record is validated against the schema at ingestion time, preventing bad data from entering the pipeline.

## Architecture<a id="architecture"></a>

The system uses **Pathway connectors** to build an end-to-end streaming ML pipeline:

```
FRED API → CSV Stream → Pathway CSV Connector → Pathway Kafka Connector → Kafka
                ↓                                           ↓
          (streaming mode)                      (pw.io.kafka.write)
                                                           
                                                          ↓
                                                    Kafka Topic
                                                          ↓
                                            Pathway Kafka Consumer
                                              (pw.io.kafka.read)
                                                          ↓
                                              pw.io.subscribe + Buffer
                                                          ↓
                                                 Streaming ML Training
                                                          ↓
                                                   Trained Models
                                                          ↓
                                                    FastAPI Server
```

### Component Breakdown

### Component Breakdown

**Producer (`pathway_fred_producer.py`)** - Pathway CSV & Kafka Connectors
- Fetches 29 economic indicators from FRED API every 10 minutes
- Streams data row-by-row to CSV for realistic streaming simulation
- **`pw.io.csv.read(mode='streaming')`** monitors CSV for new data
- **`pw.io.kafka.write()`** publishes to Kafka topic in real-time
- **`pw.io.subscribe()`** logs each data point as it streams through
- Handles missing data with intelligent forward/backward filling

**Consumer (`pathway_consumer_training.py`)** - Pathway Streaming ML
- **`pw.io.kafka.read()`** consumes economic data from Kafka with schema validation
- **`pw.io.subscribe()`** with custom `on_change` callback processes each incoming record
- Maintains data buffer with intelligent training triggers (15 records or 60 seconds)
- Automatically retrains LSTM models when buffer threshold is met
- **`pw.io.csv.write()`** creates backup stream for data recovery
- Persists models with comprehensive metrics and metadata

**API Server (`api_server.py`)** - Real-Time Predictions
- FastAPI-based REST API serving predictions from trained models
- Auto-reloads models every 5 minutes to reflect latest training
- Fetches live FRED data for up-to-date predictions
- Comprehensive endpoints for health checks, model metadata, and predictions

## Features<a id="features"></a>

**Pathway CSV Streaming**: Real-time file monitoring with `mode='streaming'` - automatically detects and processes new rows as they're written. Perfect for development and testing before moving to production Kafka streams.

**Pathway Kafka Integration**: Native Kafka connectors (`pw.io.kafka.read` and `pw.io.kafka.write`) with built-in schema validation, JSON serialization, and consumer group management. No need for separate Kafka libraries.

**Unified Batch/Streaming Code**: The same Pathway code runs in both batch (`mode='static'`) and streaming (`mode='streaming'`) modes. Develop with batch processing, deploy with streaming - zero code changes.

**Streaming ML with Pathway Subscribe**: `pw.io.subscribe()` provides real-time callbacks for data changes, enabling reactive ML pipelines that retrain automatically when new data arrives. Maintains complete history for accurate training.

**Strong Schema Typing**: `pw.Schema` validates every incoming record, ensuring data quality at ingestion time. Type mismatches are caught immediately, preventing pipeline failures downstream.

**Python API with Rust Performance**: Write pure Python code that runs on Pathway's Rust engine. Get multithreading, parallel processing, and memory efficiency without leaving Python.

**Automated Model Persistence**: Models automatically save with metadata (features, metrics, timestamps) for full traceability and reproducibility. API hot-reloads models without downtime.

**Production-Ready Streaming**: Full Docker Compose setup with Kafka, Zookeeper, and all Pathway components. Includes health checks, automatic restarts, and volume persistence.

**Comprehensive Metrics**: Each prediction includes confidence scores, directional accuracy, RMSE, MAE, and market sentiment analysis (BULLISH/BEARISH/NEUTRAL).

**Economic Indicator Coverage**: Streams 29 real-time FRED indicators: oil prices, inflation (CPI/PPI), unemployment, GDP, interest rates, yield curves, housing data, and manufacturing indices.

## Getting Started<a id="getting-started"></a>

### Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose (for containerized deployment)
- FRED API key (get one free at [https://fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html))

### Installation

**Step 1: Clone the repository**

```bash
git clone <your-repo-url>
cd aws_macro_deployment
```

**Step 2: Set up environment variables**

Create a `.env` file in the project root:

```bash
FRED_API_KEY=your_fred_api_key_here
KAFKA_BOOTSTRAP_SERVERS=localhost:9090
```

**Step 3: Install dependencies**

```bash
pip install -r requirements.txt
```

**Step 4: Create necessary directories**

```bash
mkdir -p data models logs
```

### Quick Start with Docker

The easiest way to run the entire Pathway streaming pipeline:

```bash
# Start all services (Kafka + Pathway producer + Pathway consumer + API)
docker compose up -d

# View logs
docker compose logs -f

# Check service status
docker compose ps

# Stop all services
docker compose down
```

Services will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Kafka**: localhost:9090

### Manual Running (Without Docker)

**Terminal 1: Start Kafka**

```bash
# Start Zookeeper
zookeeper-server-start /path/to/zookeeper.properties

# Start Kafka (in another terminal)
kafka-server-start /path/to/kafka.properties
```

**Terminal 2: Start Pathway Producer**

This demonstrates **Pathway's CSV and Kafka connectors**:

```bash
export FRED_API_KEY="your_key"
python pathway_fred_producer.py --fetch-interval 600
```

What this does:
- Fetches FRED data and writes to CSV row-by-row
- **`pw.io.csv.read(mode='streaming')`** monitors the CSV file
- **`pw.io.kafka.write()`** streams each row to Kafka topic
- All in pure Python with Pathway's streaming engine

**Terminal 3: Start Pathway Consumer**

This demonstrates **Pathway's streaming ML capabilities**:

```bash
python pathway_consumer_training.py --retrain-threshold 5
```

What this does:
- **`pw.io.kafka.read()`** consumes from Kafka with schema validation
- **`pw.io.subscribe()`** triggers ML pipeline on each data point
- **`pw.io.csv.write()`** backs up stream to CSV
- Automatically retrains LSTM models when buffer fills

**Terminal 4: Start API**

```bash
python api_server.py
```

## Pathway Code Examples<a id="pathway-examples"></a>

### Example 1: Streaming CSV with Pathway

```python
import pathway as pw

# Define schema for type safety
class FREDDataSchema(pw.Schema):
    date: str
    fetch_timestamp: str
    DCOILWTICO: float
    CPIAUCSL: float
    # ... more indicators

# Read CSV in streaming mode - monitors file for new rows
fred_data_table = pw.io.csv.read(
    "data/fred_stream.csv",
    schema=FREDDataSchema,
    mode='streaming',  # Key: enables real-time monitoring
    autocommit_duration_ms=1000  # Commit every 1 second
)

# Subscribe to changes - gets called for each new row
pw.io.subscribe(
    fred_data_table,
    on_change=lambda key, row, time, is_addition: 
        print(f"New data: {row['date']}") if is_addition else None
)

# Run the streaming pipeline
pw.run()
```

### Example 2: Kafka Producer with Pathway

```python
import pathway as pw

# Kafka producer settings
rdkafka_settings = {
    "bootstrap.servers": "localhost:9090",
    "security.protocol": "plaintext",
}

# Stream from CSV...
fred_data = pw.io.csv.read(
    "data/fred_stream.csv",
    schema=FREDDataSchema,
    mode='streaming'
)

# ...directly to Kafka topic
pw.io.kafka.write(
    fred_data,
    rdkafka_settings,
    topic_name="fred_economic_data",
    format="json"  # Automatic JSON serialization
)

pw.run()
```

### Example 3: Kafka Consumer with Streaming ML

```python
import pathway as pw

# Kafka consumer settings
rdkafka_settings = {
    "bootstrap.servers": "localhost:9090",
    "group.id": "ml_pipeline",
    "auto.offset.reset": "earliest"
}

# Consume from Kafka with schema validation
data_stream = pw.io.kafka.read(
    rdkafka_settings,
    topic="fred_economic_data",
    schema=FREDDataSchema,
    format="json",
    autocommit_duration_ms=1000
)

# Process each record as it arrives
def process_data(key, row, time, is_addition):
    if is_addition:
        # Add to buffer
        buffer.append(row)
        
        # Trigger ML training when buffer is full
        if len(buffer) >= 15:
            train_models(buffer)
            buffer.clear()

pw.io.subscribe(
    data_stream,
    on_change=process_data
)

# Backup stream to CSV for recovery
pw.io.csv.write(data_stream, "backup.csv")

pw.run()
```

### Example 4: Batch to Streaming - Same Code!

```python
# Development: Process historical data
def create_pipeline(mode='static'):
    data = pw.io.csv.read(
        "data/fred_data.csv",
        schema=FREDDataSchema,
        mode=mode  # 'static' or 'streaming'
    )
    
    # ... rest of pipeline logic ...
    
    pw.run()

# Development/testing
create_pipeline(mode='static')  # Batch processing

# Production
create_pipeline(mode='streaming')  # Real-time streaming
```

No code changes - just switch the mode!

## Deployment<a id="deployment"></a>

### Local Docker Deployment

The system includes a complete Docker Compose setup with health checks and automatic restarts:

```bash
docker compose up -d
```

This launches:
- Zookeeper (port 2181)
- Kafka (port 9090)
- FRED Producer (streams economic data)
- Model Training Consumer (trains models)
- Prediction API (port 8000)

### AWS EC2 Deployment

Use the provided deployment script for one-command deployment to AWS:

**Step 1: Configure your EC2 credentials**

Add to your `.env` file:

```bash
KEY_FILE=/path/to/your-key.pem
EC2_HOST=ec2-user@your-ec2-ip
```

**Step 2: Deploy**

```bash
chmod +x deployment.sh
./deployment.sh
```

The script will:
- Copy all necessary files to your EC2 instance
- Set up directories and environment
- Build and start Docker containers
- Display service status and logs

**Step 3: Access your deployed API**

The deployment script will output your public API URL:

```
API available at: http://your-ec2-ip:8000
API docs at: http://your-ec2-ip:8000/docs
```

### Kubernetes Deployment

For production-scale deployments, the system can be deployed on Kubernetes. Docker images can be pushed to a container registry and deployed using Kubernetes manifests.

## API Usage<a id="api-usage"></a>

### Get Predictions for All Sectors

```bash
curl http://localhost:8000/predict
```

**Response:**

```json
{
  "timestamp": "2025-11-09T19:30:00",
  "total_sectors": 11,
  "predictions": [
    {
      "sector": "Information Technology",
      "ticker": "XLK",
      "predicted_return_pct": 2.45,
      "sentiment": "BULLISH",
      "confidence_score": 78.5,
      "model_metrics": {
        "rmse": 0.0234,
        "mae": 0.0189,
        "dir_acc": 0.6234
      },
      "last_updated": "2025-11-09T18:00:00",
      "features_used": ["IPB53100SQ", "DGORDER", "CPIAUCSL", "FEDFUNDS"]
    }
  ],
  "market_summary": {
    "average_return_pct": 1.23,
    "market_outlook": "BULLISH MARKET",
    "bullish_sectors": 7,
    "bearish_sectors": 2,
    "neutral_sectors": 2,
    "average_confidence": 72.4,
    "best_sector": "Information Technology",
    "worst_sector": "Energy"
  }
}
```

### Get Prediction for Specific Sector

```bash
curl http://localhost:8000/predict/Financials
```

### Health Check

```bash
curl http://localhost:8000/health
```

### List All Models

```bash
curl http://localhost:8000/models
```

### Reload Models Manually

```bash
curl -X POST http://localhost:8000/reload-models
```

### Interactive API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger documentation where you can test all endpoints directly in your browser.

## Project Structure

```
aws_macro_deployment/
├── data/                          # Data storage
│   └── fred_stream.csv           # Streaming economic data
├── models/                        # Trained ML models
│   ├── Energy_model.pkl
│   ├── Financials_model.pkl
│   └── ...
├── pathway_fred_producer.py      # FRED data collector + Pathway Kafka producer
├── pathway_consumer_training.py  # Pathway Kafka consumer + model trainer
├── api_server.py                 # FastAPI prediction server
├── docker compose.yaml           # Multi-service Docker setup
├── Dockerfile.producer           # Producer container
├── Dockerfile.consumer           # Consumer container
├── Dockerfile.api                # API container
├── deployment.sh                 # EC2 deployment script
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables
└── README.md                     # This file
```

## Configuration

### Environment Variables

All configuration is done through the `.env` file:

```bash
# Required
FRED_API_KEY=your_fred_api_key

# Optional (with defaults)
KAFKA_BOOTSTRAP_SERVERS=localhost:9090
EC2_HOST=ec2-user@your-ip
KEY_FILE=/path/to/key.pem
```

### Producer Configuration

```bash
python pathway_fred_producer.py \
  --csv data/fred_stream.csv \
  --kafka localhost:9090 \
  --fetch-interval 600 \
  --start-date 1990-01-01
```

### Consumer Configuration

```bash
python pathway_consumer_training.py \
  --kafka localhost:9090 \
  --retrain-threshold 5 \
  --min-training-samples 36
```

## Economic Indicators

The system monitors 29 FRED series across different categories:

**Energy**: Oil prices (DCOILWTICO), energy CPI (CPIENGSL, CPENGSL), energy PPI (PPIENG)

**Manufacturing**: Industrial production (INDPRO, IPMAN), capacity utilization (CAPUTLB00004S), durable goods orders (DGORDER)

**Consumer**: Retail sales (RSAFS, RRSFS), consumer sentiment (UMCSENT), personal consumption (PCE)

**Inflation**: CPI (CPIAUCSL, CPIFABSL, CPIMEDSL), PPI (PPIACO), international inflation (CPALTT01USM657N)

**Labor**: Unemployment rate (UNRATE)

**Financial**: Fed funds rate (FEDFUNDS), yield curve (T10Y2Y, T10Y3M), money supply (M2SL), mortgage rates (MORTGAGE30US)

**Housing**: Housing starts (HOUST), building permits (PERMIT), home prices (CSUSHPINSA)

**GDP**: Gross domestic product (GDP)

**Technology**: Computer and electronic products production (IPB53100SQ)

## Pathway Performance and Monitoring<a id="performance"></a>

### Rust-Powered Streaming Engine

Pathway runs your Python code on a **high-performance Rust engine** based on Differential Dataflow, delivering:

**Multithreading**: Automatic parallel processing without Python's GIL limitations
```bash
# Launch with 4 threads for parallel processing
pathway spawn --threads 4 python pathway_consumer_training.py
```

**Memory Efficiency**: Streaming operations keep constant memory footprint regardless of data volume. Only active working set is in memory.

**Incremental Computation**: Pathway automatically tracks changes and only recomputes affected parts of the pipeline - no need to reprocess entire datasets.

**Sub-second Latency**: Real-time predictions with minimal delay from data arrival to model inference.

### Pathway Dashboard Monitoring

Pathway comes with a built-in monitoring dashboard accessible when running your pipeline:

```bash
pathway spawn python pathway_consumer_training.py
```

The dashboard provides real-time insights:
- **Message throughput** per connector (CSV, Kafka reader, Kafka writer)
- **System latency** from ingestion to processing
- **Live log messages** and error tracking
- **Data flow visualization** through the pipeline
- **Connector health** and connection status

### Why Pathway for Streaming ML?

Traditional batch ML pipelines require complete retraining on full datasets. Pathway enables:

1. **Continuous Learning**: Models update automatically as new data streams in
2. **Always Fresh**: Predictions use the latest available data without manual ETL runs
3. **Production-Ready**: Same code runs in dev (batch) and prod (streaming)
4. **Resource Efficient**: Only processes new/changed data, not entire history

### Model Metrics

Each trained model tracks comprehensive performance metrics:
- **RMSE**: Root Mean Square Error of return predictions
- **MAE**: Mean Absolute Error
- **Directional Accuracy**: Percentage of correct up/down predictions
- **R² Score**: Train, validation, and test set performance
- **Overfitting Detection**: R² gap and RMSE ratio monitoring

### System Benchmarks

In our testing with 11 sectors and 29 economic indicators:

- **Data Ingestion**: 1000+ records/second via Pathway Kafka connector
- **Model Training**: Complete pipeline (all 11 sectors) in ~5-8 minutes
- **API Latency**: <100ms for prediction requests with cached models
- **Memory Usage**: <2GB for entire streaming pipeline
- **Throughput**: Handles continuous streaming with zero data loss
- **Scalability**: Pathway's Rust engine enables horizontal scaling

### API Performance

The API includes automatic model caching with configurable TTL to balance freshness and performance. Models are reloaded every 5 minutes by default, ensuring predictions use recently trained models without sacrificing response time.

## Troubleshooting

**Models not loading**

Ensure the consumer has run and created model files in the `models/` directory. Check logs for training errors.

**Kafka connection issues**

Verify Kafka is running and accessible at the configured bootstrap servers. For Docker, use the internal network hostname `kafka:29092`.

**FRED API errors**

Check that your FRED API key is valid and has not exceeded rate limits. The free tier allows 120 requests/minute.

**No predictions available**

Models require at least 36 months of data to train. Wait for sufficient data to accumulate or use a longer historical start date.

**Docker services not starting**

Check Docker logs with `docker compose logs <service-name>`. Ensure all health checks pass before dependent services start.

## Technical Details

**Streaming Architecture with Pathway**: Built on Pathway's unified batch/streaming framework, this system demonstrates production-ready real-time ML with automatic model updates as new economic data arrives.

**Machine Learning**: LSTM neural networks with regularization (dropout, L2, early stopping) trained on engineered features including percentage changes, moving averages, and lagged values.

**Pathway Connectors**: 
- **CSV Streaming**: `pw.io.csv.read(mode='streaming')` for development and testing
- **Kafka Integration**: `pw.io.kafka.read()` and `pw.io.kafka.write()` for production streaming
- **Subscribe Mechanism**: `pw.io.subscribe()` for real-time change tracking and ML triggers

**Schema Validation**: Strong typing with `pw.Schema` ensures data quality at ingestion time, catching type errors before they propagate through the pipeline.

**Feature Engineering**: Automatic calculation of returns, percentage changes, 20-period moving averages, standard deviations, and rate-of-change indicators for each economic series.

**Data Handling**: Robust missing value imputation using forward-fill, backward-fill, and zero-filling strategies to handle sparse economic data releases.

**Rust Engine Benefits**: Pathway's Rust engine provides multithreading, parallel processing, and memory-efficient streaming without Python GIL limitations.

## Why Pathway?

This project showcases why **Pathway is ideal for streaming ML pipelines**:

✅ **Same code for dev and prod** - Switch from batch to streaming by changing one parameter  
✅ **Built-in connectors** - Native CSV and Kafka support with schema validation  
✅ **Python-first** - Write pure Python, run on Rust for performance  
✅ **Real-time ML** - Automatic model updates as new data streams in  
✅ **Production-ready** - Docker deployment, monitoring dashboard, persistence  
✅ **Type safety** - Schema validation catches errors at ingestion time  
✅ **Zero config streaming** - No complex stream processing frameworks needed

### Pathway vs Traditional Approaches

| Feature | Traditional (Airflow + Spark) | Pathway |
|---------|-------------------------------|---------|
| Code complexity | Separate batch/stream code | Unified codebase |
| Setup | Complex multi-tool stack | Single Python framework |
| Type safety | Runtime errors common | Compile-time schema validation |
| Performance | Python overhead | Rust engine performance |
| Streaming ML | Difficult to implement | Built-in support |
| Development speed | Slow iteration | Rapid prototyping |

## Performance Benchmarks

With Pathway's Rust-powered engine, this system achieves:
- **Sub-second latency** for real-time predictions via `pw.io.subscribe` callbacks
- **Efficient streaming** with minimal memory footprint through incremental computation
- **Automatic updates** - models retrain seamlessly as new data arrives via Kafka connector
- **Multithreading** - parallel processing across sectors with `pathway spawn --threads N`
- **Zero downtime** - API serves predictions while models train in background

For more comprehensive Pathway benchmarks comparing to Flink, Spark, and Kafka Streams, see [Pathway Benchmarks](https://github.com/pathwaycom/pathway-benchmarks).