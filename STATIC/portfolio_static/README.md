<div align="center">
  <h1>Real-Time Portfolio Optimization System</h1>
  <p><strong>Multi-Strategy Portfolio Management with CVaR, Omega, and Custom Risk Models, Powered by Pathway</strong></p>
</div>

<p align="center">
    <a href="#overview">Overview</a> |
    <a href="#project-structure">Project Structure</a> |
    <a href="#getting-started">Getting Started</a> |
    <a href="#architecture">Architecture</a> |
    <a href="#usage">Usage</a>
</p>

## Overview

A complete end-to-end streaming portfolio optimization system featuring three distinct portfolio management services: **Creator** (new portfolio construction), **Rebalancer** (portfolio adjustment), and **Diversifier** (risk mitigation through diversification). The system processes real-time stock scores and market data through Kafka, applies multiple optimization strategies (CVaR, Omega, Custom), and persists results to PostgreSQL for continuous portfolio management.

### Key Features

- **Three Portfolio Services**: Creator, Rebalancer, and Diversifier for different portfolio management needs
- **Multiple Optimization Strategies**: CVaR (Conditional Value at Risk), Omega Ratio, and Custom Beta-constrained optimization
- **Real-Time Data Processing**: Ingests stock scores and prices via Kafka streams
- **Continuous Risk Monitoring**: Calculates rolling returns and maintains historical performance data
- **PostgreSQL Persistence**: Stores market snapshots, returns history, and optimization results
- **RESTful API**: FastAPI-based service for triggering optimizations and retrieving results
- **Automated Rebalancing**: Generates trade recommendations based on portfolio drift
- **Dockerized Deployment**: Complete stack orchestrated with Docker Compose

## Project Structure

```
eval/portfolio_2/
├── backend/
│   ├── api_server.py                     # FastAPI REST API server
│   ├── portfolio.py                      # Core optimization engine
│   ├── Dockerfile
│   └── requirements.txt
├── data/
│   ├── AMZN.csv                          # Historical stock data
│   ├── BX.csv
│   ├── MSFT.csv
│   ├── NIO.csv
│   ├── stock_tweets.csv                  # Sentiment data
│   └── TSLA.csv
├── evaluation/
│   └── evaluation.py                     # Performance metrics & backtesting
├── output/
│   └── highValue.jsonl                   # High-value stock alerts
├── processing/
│   ├── scorer.py                         # Stock scoring pipeline
│   ├── Dockerfile
│   └── requirements.txt
├── producers/
│   ├── producer_sentiment.py             # Sentiment data producer
│   ├── producer_stock.py                 # Stock price data producer
│   ├── Dockerfile
│   └── requirements.txt
└── docker-compose.yml                    # Orchestrates entire stack
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.10+ (for local development)
- PostgreSQL (handled by Docker Compose)

### Installation

1. **Launch the entire pipeline**:

```bash
docker-compose up --build
```

That's it! The system will:
- Start Kafka and Zookeeper
- Initialize PostgreSQL database with required schemas
- Launch stock and sentiment data producers
- Start the scoring pipeline (generates stock_scores)
- Begin portfolio optimization engine
- Start the FastAPI server on `http://localhost:8000`

## Architecture

### Data Flow Overview

```
┌─────────────────────────────────────────────────────────┐
│ Data Sources (Kafka Producers)                          │
├──────────┬──────────────────────────────────────────────┤
│ Stock    │ Sentiment                                     │
│ Producer │ Producer                                      │
└──────────┴──────┬───────────────────────────────────────┘
                  │
           ┌──────▼──────────────────────────────────┐
           │ Scoring Pipeline                        │
           │ (Combines price + sentiment)            │
           └──────┬──────────────────────────────────┘
                  │
                  ├─────────► Kafka: stock_scores
                  │
        ┌─────────▼──────────┐
        │ Portfolio Engine   │
        ├────────────────────┤
        │ • Market Snapshot  │
        │ • Returns Calc     │
        │ • Optimization     │
        └─────────┬──────────┘
                  │
                  ├─────────► PostgreSQL
                  │            • market_data_snapshot
                  │            • returns_history
                  │            • optimization_results
                  │
        ┌─────────▼──────────┐
        │ FastAPI Server     │
        │ (REST Endpoints)   │
        └────────────────────┘
```

### Components

#### 1. **Kafka Producers** (producers/)

##### producer_stock.py
- Reads historical stock price data from CSV files (AMZN, BX, MSFT, NIO, TSLA)
- Publishes OHLC data to Kafka topic `stock_prices`
- Simulates real-time market data stream at configurable frequency

##### producer_sentiment.py
- Reads sentiment data from `stock_tweets.csv`
- Publishes to Kafka topic `stock_sentiment`
- Provides social media sentiment scores for stocks

#### 2. **Scoring Pipeline** (processing/scorer.py)

**Input:**
- Consumes from Kafka topics: `stock_prices`, `stock_sentiment`

**Processing:**
- Performs temporal joins to align sentiment with price data
- Calculates composite stock scores using:
  - Price momentum
  - Volume trends
  - Sentiment scores
  - Technical indicators

**Output:**
- Publishes to Kafka topic: `stock_scores`
- Schema: `{symbol, stock_score, latest_price, timestamp}`
- Writes high-value stocks (score > threshold) to `output/highValue.jsonl`

#### 3. **Portfolio Engine** (backend/portfolio.py)

##### DatabaseManager
- Manages PostgreSQL connections and schema
- Creates three core tables:
  - `market_data_snapshot`: Latest stock prices and scores
  - `returns_history`: Rolling return calculations
  - `optimization_results`: Portfolio optimization outputs

##### Pathway Streaming Pipeline
**Market Data Snapshot:**
- 1-second tumbling windows per symbol
- Captures latest price and stock score
- Writes to `market_data_snapshot` table

**Returns Calculator:**
- 1-minute sliding windows (5-second hop)
- Computes percentage returns for each symbol
- Writes to `returns_history` table

##### OptimizationEngine
Implements three optimization strategies:

**1. CVaR (Conditional Value at Risk)**
- Minimizes tail risk using CVaR optimization
- Uses historical returns distribution
- Suitable for risk-averse portfolios

**2. Omega Ratio**
- Maximizes Sharpe ratio as proxy for Omega
- Balances return against volatility
- General-purpose optimization

**3. Custom (Beta-Constrained)**
- Allows beta targeting relative to market
- Adds custom constraints via CVXPY
- Flexible for specific risk profiles

##### Portfolio Services

**CreatorService** - New Portfolio Construction
- Filters stocks by hurdle rate (minimum score)
- Applies selected optimization strategy
- Returns optimal weights for new portfolio

**RebalancerService** - Portfolio Adjustment
- Compares current holdings to optimal weights
- Generates BUY/SELL trade recommendations
- Triggers only when drift exceeds threshold (1%)

**DiversifierService** - Risk Mitigation
- Considers current holdings + candidate stocks
- Optimizes for maximum diversification
- Maintains hurdle rate filtering

#### 4. **FastAPI Server** (backend/api_server.py)

**Endpoints:**

```
POST /api/portfolio/create
Body: {
  "user_id": "user123",
  "config": {
    "strategy_name": "CVaR",
    "risk_params": {"hurdle_rate": 0.5}
  }
}
Response: {"weights": {"TSLA": 0.3, "AMZN": 0.4, ...}, "count": 5}

POST /api/portfolio/rebalance
Body: {
  "user_id": "user123",
  "config": {...},
  "current_portfolio": [
    {"symbol": "TSLA", "weight": 0.25},
    {"symbol": "AMZN", "weight": 0.30}
  ]
}
Response: {
  "weights": {...},
  "trades": {"TSLA": {"action": "BUY", "delta": 0.05}}
}

POST /api/portfolio/diversify
Body: {
  "user_id": "user123",
  "config": {...},
  "current_portfolio": [...]
}
Response: {"weights": {...}}
```

#### 5. **Evaluation** (evaluation/evaluation.py)

- Backtests optimization strategies on historical data
- Computes performance metrics:
  - Total return
  - Sharpe ratio
  - Maximum drawdown
  - Win rate
- Compares strategy effectiveness

## Usage

### Running the Full Pipeline

```bash
# Start everything
docker-compose up --build

# Run in detached mode
docker-compose up -d --build

# View logs
docker-compose logs -f portfolio-engine
docker-compose logs -f api-server
docker-compose logs -f scorer

# Stop all services
docker-compose down
```

### Making API Requests

**Create a new portfolio:**
```bash
curl -X POST http://localhost:8000/api/portfolio/create \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "config": {
      "strategy_name": "CVaR",
      "risk_params": {"hurdle_rate": 0.6}
    }
  }'
```

**Rebalance existing portfolio:**
```bash
curl -X POST http://localhost:8000/api/portfolio/rebalance \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "config": {"strategy_name": "Omega"},
    "current_portfolio": [
      {"symbol": "TSLA", "weight": 0.25},
      {"symbol": "MSFT", "weight": 0.30},
      {"symbol": "AMZN", "weight": 0.45}
    ]
  }'
```

### Local Testing

**Test scoring pipeline:**
```bash
cd processing
python scorer.py
```

**Run evaluation/backtest:**
```bash
cd evaluation
python evaluation.py
```

## Configuration

### Key Parameters

#### Portfolio Engine (backend/portfolio.py)
```python
# Risk Parameters
HURDLE_RATE = 0.5              # Minimum stock score to consider
REBALANCE_THRESHOLD = 0.01     # Minimum weight change to trigger trade

# Window Sizes
SNAPSHOT_WINDOW = "1s"         # Market data snapshot frequency
RETURNS_WINDOW = "1m"          # Returns calculation window
RETURNS_HOP = "5s"             # Returns calculation frequency

# Database
POSTGRES_HOST = "postgres"
POSTGRES_DB = "portfolio_db"
POSTGRES_USER = "user"
POSTGRES_PASSWORD = "password"
```

#### Scoring Pipeline (processing/scorer.py)
```python
SCORE_THRESHOLD = 0.7          # High-value stock threshold
SENTIMENT_WEIGHT = 0.3         # Sentiment contribution to score
PRICE_WEIGHT = 0.7             # Price momentum contribution
```

#### Producers
```python
STOCK_PUBLISH_INTERVAL = 1.0   # Seconds between stock updates
SENTIMENT_INTERVAL = 2.0       # Seconds between sentiment updates
```

### Kafka Topics

| Topic | Producer | Schema | Description |
|-------|----------|--------|-------------|
| stock_prices | producer_stock | symbol, open, high, low, close, volume, timestamp | Stock OHLC data |
| stock_sentiment | producer_sentiment | symbol, sentiment_score, timestamp | Social media sentiment |
| stock_scores | scorer | symbol, stock_score, latest_price, timestamp | Combined scoring output |

### Database Tables

| Table | Columns | Purpose |
|-------|---------|---------|
| market_data_snapshot | symbol, price, stock_score, timestamp, time, diff | Latest market state per symbol |
| returns_history | symbol, return_value, timestamp, time, diff | Historical returns for optimization |
| optimization_results | user_id, timestamp, strategy, service_type, result_json | Optimization outputs and history |

### Output Files

| File | Location | Purpose |
|------|----------|---------|
| highValue.jsonl | output/ | Stocks exceeding score threshold |

### Environment Variables

Create a `.env` file in the root directory:

```env
POSTGRES_HOST=postgres
POSTGRES_DB=portfolio_db
POSTGRES_USER=user
POSTGRES_PASSWORD=password
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
API_PORT=8000
```

## Optimization Strategies

### CVaR (Conditional Value at Risk)
- **Use Case**: Risk-averse investors, tail risk management
- **Method**: Minimizes expected loss in worst-case scenarios
- **Best For**: Conservative portfolios, volatile markets

### Omega Ratio
- **Use Case**: General-purpose optimization
- **Method**: Maximizes Sharpe ratio (return/volatility)
- **Best For**: Balanced risk-return profiles

### Custom (Beta-Constrained)
- **Use Case**: Market-neutral or beta-targeted strategies
- **Method**: Adds beta constraints to mean-variance optimization
- **Parameters**: `target_beta` in risk_params
- **Best For**: Institutional portfolios with specific beta targets

## License

This project uses:
- **Pathway**: [BSL 1.1 License](https://pathway.com/license/)
- **PyPortfolioOpt**: MIT License
- **CVXPY**: Apache 2.0 License

## Acknowledgments

Built with:
- [Pathway](https://pathway.com/) - Real-time data processing framework
- [PyPortfolioOpt](https://pyportfolioopt.readthedocs.io/) - Portfolio optimization library
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [CVXPY](https://www.cvxpy.org/) - Convex optimization library

---

<div align="center">
  <strong>Real-time Portfolio Management powered by <a href="https://pathway.com/">Pathway</a></strong>
</div>