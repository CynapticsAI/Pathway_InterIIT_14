<div align="center">
  <p><strong>Real-time Portfolio Optimization Engine with Pathway, PostgreSQL, and Kafka</strong></p>
</div>

<p align="center">
    <a href="#overview">Overview</a> |
    <a href="#architecture">Architecture</a> |
    <a href="#optimization-strategies">Optimization Strategies</a> |
    <a href="#service-modes">Service Modes</a> |
    <a href="#installation">Installation</a> |
    <a href="#usage">Usage</a> |
    <a href="#api-reference">API Reference</a> |
    <a href="#troubleshooting">Troubleshooting</a>
</p>

---

## Overview

This system implements a sophisticated, real-time portfolio optimization engine that leverages streaming data processing and advanced mathematical optimization techniques. Built on **Pathway's** high-performance streaming framework, it continuously processes market data, sentiment signals, and macroeconomic indicators to generate optimal portfolio allocations.

The platform supports three distinct service modes—**Creator**, **Rebalancer**, and **Diversifier**—each designed to address specific portfolio management needs. The system implements multiple optimization strategies including Mean-Variance, CVaR, and Omega ratio optimization.

### Key Features

- **Real-time Streaming Analytics**: Processes live market data through Kafka topics with sub-second latency
- **Multi-Signal Alpha Generation**: Fuses stock scores, sentiment analysis, and macroeconomic predictions into a unified alpha signal
- **Advanced Optimization**: Implements Mean-Variance, CVaR (Conditional Value at Risk), and Omega ratio optimization
- **Three Service Modes**: Creator (new portfolios), Rebalancer (optimize existing), Diversifier (expand universe)
- **Performance Analytics**: Real-time calculation of expected returns, risk metrics, and Sharpe ratios
- **PostgreSQL Integration**: Persistent storage for market snapshots, returns history, and optimization results
- **Temporal Windowing**: Rolling return calculations and time-based aggregations for robust risk modeling

---

## Architecture

The system follows a streaming ETL architecture with real-time data fusion and persistent storage.

### Component Overview

```
Kafka Topics (Input)
    ├── stock_scores      → Stock-level signals
    └── sentiment_scores  → Market sentiment data
         ↓
Pathway Pipeline
    ├── Temporal Windows (5s tumbling)
    ├── Master Data Join (sector enrichment)
    ├── Macro API Integration (sector forecasts)
    └── Alpha Score Calculation
         ↓
PostgreSQL Database
    ├── market_data_snapshot (current state)
    ├── returns_history (rolling returns)
    └── optimization_results (audit trail)
         ↓
Optimization Services
    ├── Creator Service
    ├── Rebalancer Service
    └── Diversifier Service
         ↓
API Server (FastAPI)
```

### Data Flow Architecture

#### 1. **Data Ingestion Layer**

The system consumes two primary Kafka streams:

- **stock_scores**: Contains `symbol`, `stock_score`, `latest_price`, and `timestamp`
- **sentiment_scores**: Contains `symbol`, `sentiment_score`, and `t` (epoch milliseconds)

#### 2. **Stream Processing Pipeline** (Pathway)

The Pathway pipeline performs real-time transformations:

**Step 1: Temporal Aggregation**
- Both streams are windowed using 5-second **tumbling windows**
- Stock scores: Takes max score and latest price per symbol
- Sentiment scores: Averages sentiment across the window

**Step 2: Master Data Enrichment**
- Joins with master stock list (stored in database) to add sector information
- Each symbol is tagged with its corresponding sector classification

**Step 3: Macro Score Integration**
- Makes HTTP calls to external Macro API (`/predict/{sector}`)
- Retrieves sector-level return forecasts
- Converts predictions to normalized scores (0.0 to 1.0)

**Step 4: Alpha Score Calculation**
```
Alpha = 0.4 × Stock_Score + 0.4 × Macro_Score + 0.2 × ((Sentiment + 1) / 2)
```

This weighted combination creates a multi-factor alpha signal.

**Step 5: Returns Calculation**
- Uses 10-minute **sliding windows** with 60-second hops
- Calculates returns: `(Price_end - Price_start) / Price_start`
- Builds covariance matrices for risk modeling

#### 3. **Persistent Storage Layer**

Two write patterns to PostgreSQL:

- **Snapshot Mode** (`market_data_snapshot`): Always reflects current state (upserts on `symbol` primary key)
- **Stream Mode** (`returns_history`): Appends all return calculations with timestamps

---

## Optimization Strategies

The system implements three mathematically rigorous optimization approaches.

### 1. Mean-Variance Optimization (Markowitz)

**Objective**: Maximize the Sharpe ratio (risk-adjusted returns)

```
Maximize: (μᵀw - rf) / √(wᵀΣw)
Subject to: Σw = 1, w ≥ 0
```

Where:
- `μ` = Expected returns (alpha scores)
- `Σ` = Covariance matrix (from returns history)
- `w` = Portfolio weights
- `rf` = Risk-free rate (set to 0.0)

**Implementation Details**:
- Uses **Ledoit-Wolf shrinkage** for covariance estimation to handle noisy data
- Adds ridge regularization (`1e-4 × I`) to ensure positive definite matrices
- Supports optional beta constraints via CVXPY

### 2. CVaR Optimization (Conditional Value at Risk)

**Objective**: Minimize tail risk while achieving target return

```
Minimize: CVaR_α(portfolio returns)
Subject to: E[R] ≥ target_return, Σw = 1, w ≥ 0
```

**Why CVaR?**
- Mean-Variance assumes normal distributions; CVaR handles fat tails
- Focuses on downside risk in worst-case scenarios
- Target return set to mean alpha score across universe

**Implementation**:
- Uses `EfficientCVaR` from PyPortfolioOpt
- Operates directly on returns distribution (not just covariance)
- More robust during market stress periods

### 3. Omega Ratio Optimization

**Objective**: Maximize probability-weighted gains over losses

```
Maximize: Ω(threshold) = E[max(R - threshold, 0)] / E[max(threshold - R, 0)]
```

**Formulation** (Linear Programming):
```
Minimize: Σy_t
Subject to:
    - y_t ≥ hurdle - (returns_t · w)
    - Σw = 1
    - w ≥ 0, y ≥ 0
```

**Advantages**:
- Considers the entire return distribution
- User-defined hurdle rate allows for client-specific risk thresholds
- No assumption about distribution shape

**Implementation**:
- Solved using CVXPY with ECOS solver
- Hurdle rate annualized: `hurdle / 252` (trading days)
- Returns full weight vector rounded to 4 decimals

---

## Service Modes

The system provides three distinct portfolio management services, each optimized for different use cases.

### 1. Creator Service

**Purpose**: Build a new portfolio from scratch

**Process**:
1. Fetches current market snapshot from database
2. Filters universe:
   - Stocks with `alpha_score ≥ hurdle_rate`
   - Excludes hard-to-borrow tickers
3. Runs selected optimization strategy
4. Returns weights and analytics

**Output**:
```json
{
  "weights": {"AAPL": 0.25, "MSFT": 0.18, ...},
  "tickers_analyzed": 47,
  "stock_exposure": {"AAPL": 0.25, ...},
  "sector_exposure": {"Technology": 0.43, ...},
  "new_portfolio_metrics": {
    "expected_return": 0.0234,
    "risk": 0.0156,
    "sharpe_ratio": 1.50
  }
}
```

**Use Case**: Initial portfolio construction, client onboarding

---

### 2. Rebalancer Service

**Purpose**: Optimize existing portfolio without adding new assets

**Process**:
1. Receives current portfolio as input: `[{"symbol": "AAPL", "weight": 0.30}, ...]`
2. Fetches latest market data for those symbols only
3. Re-optimizes weights within the existing universe
4. Calculates required trades (buys/sells)
5. Compares old vs. new portfolio metrics

**Trade Calculation**:
```python
delta = target_weight - current_weight
if |delta| > 0.001:  # 0.1% threshold
    action = "BUY" if delta > 0 else "SELL"
```

**Output**:
```json
{
  "weights": {"AAPL": 0.28, "MSFT": 0.22, ...},
  "trades": {
    "AAPL": {"action": "SELL", "delta": -0.02},
    "MSFT": {"action": "BUY", "delta": 0.04}
  },
  "old_portfolio_metrics": {"sharpe_ratio": 1.32, ...},
  "new_portfolio_metrics": {"sharpe_ratio": 1.45, ...}
}
```

**Use Case**: Periodic rebalancing, drift correction

---

### 3. Diversifier Service

**Purpose**: Expand portfolio universe while managing concentration risk

**Process**:
1. Identifies candidate stocks (same filters as Creator)
2. Creates expanded universe: `current_holdings ∪ new_candidates`
3. Runs optimization on full universe
4. **Applies sector concentration limits** post-optimization
5. Generates trades to transition from old to new portfolio

**Sector Limit Enforcement**:
```python
if sector_exposure > max_sector_exposure:
    scale_factor = max_sector_exposure / sector_exposure
    for stock in sector:
        weight[stock] *= scale_factor
```

**Output**: Same structure as Rebalancer, but may include new symbols

**Use Case**: Portfolio expansion, risk reduction through diversification

---

## Performance Metrics Calculation

All services return comprehensive performance analytics.

### Expected Return
```
E[R] = Σ (w_i × alpha_i)
```
Weighted sum of alpha scores

### Portfolio Risk (Volatility)
```
σ_p = √(wᵀΣw)
```
Standard deviation of portfolio returns

### Sharpe Ratio
```
SR = E[R] / σ_p
```
Risk-adjusted return (assuming rf = 0)

**Calculation Details**:
- Alpha scores act as expected return proxies
- Covariance matrix computed from 60-minute rolling returns
- All metrics rounded to 4 decimal places

---

## Database Schema

### market_data_snapshot
```sql
CREATE TABLE market_data_snapshot (
    symbol TEXT PRIMARY KEY,
    sector TEXT,
    price FLOAT,
    alpha_score FLOAT,
    timestamp TIMESTAMP,
    time BIGINT,
    diff INT
);
```
**Purpose**: Current state of all symbols with latest alpha scores

### returns_history
```sql
CREATE TABLE returns_history (
    symbol TEXT,
    return_value FLOAT,
    timestamp TIMESTAMP,
    time BIGINT,
    diff INT
);
```
**Purpose**: Time-series of calculated returns for covariance estimation

### optimization_results
```sql
CREATE TABLE optimization_results (
    user_id TEXT,
    timestamp TIMESTAMP,
    strategy TEXT,
    service_type TEXT,
    result_json JSONB
);
```
**Purpose**: Audit trail of all optimization runs

---

## Installation

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
- PostgreSQL 13+
- Apache Kafka 2.8+
- Access to Macro API endpoint

### Environment Setup

1. **Configure Environment Variables**

Create a `.env` file in the project root:

```bash
# PostgreSQL Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=portfolio_db
POSTGRES_USER=user
POSTGRES_PASSWORD=your_secure_password

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# Macro API
MACRO_API_URL=http://macro-api:8000
```

2. **Install Dependencies**

```bash
pip install pathway pandas numpy cvxpy psycopg2-binary PyPortfolioOpt requests
```

Or using the requirements file:
```bash
pip install -r requirements.txt
```

3. **Database Initialization**

The system auto-creates tables on first run. To manually initialize:

```bash
python -c "from portfolio import DatabaseManager; DatabaseManager.create_initial_tables()"
```

---

## Usage

### Running the Streaming Pipeline

```bash
python portfolio.py
```

This starts the Pathway pipeline which will:
1. Connect to Kafka topics
2. Process streams in real-time
3. Write to PostgreSQL continuously
4. Generate CSV outputs in `/app/output/`

### Service Invocation Examples

#### 1. Create New Portfolio

```python
from portfolio import CreatorService

config = {
    "strategy_name": "Mean-Variance",
    "risk_params": {
        "hurdle_rate": 0.02,
        "target_beta": 1.0
    },
    "hard_to_borrow": ["GME", "AMC"]
}

result = CreatorService.execute(
    user_id="user_123",
    config=config
)

print(f"Sharpe Ratio: {result['new_portfolio_metrics']['sharpe_ratio']}")
```

#### 2. Rebalance Existing Portfolio

```python
from portfolio import RebalancerService

current_portfolio = [
    {"symbol": "AAPL", "weight": 0.30},
    {"symbol": "MSFT", "weight": 0.25},
    {"symbol": "GOOGL", "weight": 0.20},
    {"symbol": "AMZN", "weight": 0.25}
]

config = {
    "strategy_name": "CVaR",
    "risk_params": {}
}

result = RebalancerService.execute(
    user_id="user_123",
    config=config,
    current_portfolio=current_portfolio
)

for symbol, trade in result['trades'].items():
    print(f"{symbol}: {trade['action']} {abs(trade['delta']):.2%}")
```

#### 3. Diversify Portfolio

```python
from portfolio import DiversifierService

config = {
    "strategy_name": "Omega",
    "risk_params": {
        "hurdle_rate": 0.05,  # 5% annualized
        "max_sector_exposure": 0.30  # 30% max per sector
    },
    "hard_to_borrow": []
}

result = DiversifierService.execute(
    user_id="user_123",
    config=config,
    current_portfolio=current_portfolio
)

print(f"Sector Exposure: {result['sector_exposure']}")
```

---

## API Reference

### OptimizationEngine Methods

#### `calculate_weights(strategy_name, filtered_stocks, risk_params)`
**Returns**: `Dict[str, float]` - Symbol to weight mapping

**Parameters**:
- `strategy_name`: One of ["Mean-Variance", "CVaR", "Omega"]
- `filtered_stocks`: DataFrame with columns [symbol, sector, alpha_score, price]
- `risk_params`: Dict containing strategy-specific parameters

**Example**:
```python
weights = OptimizationEngine.calculate_weights(
    strategy_name="CVaR",
    filtered_stocks=market_df,
    risk_params={"hurdle_rate": 0.03}
)
```

#### `calculate_portfolio_performance(weights)`
**Returns**: `Dict[str, float]` with keys [expected_return, risk, sharpe_ratio]

**Example**:
```python
metrics = OptimizationEngine.calculate_portfolio_performance(
    weights={"AAPL": 0.5, "MSFT": 0.5}
)
# {"expected_return": 0.0234, "risk": 0.0156, "sharpe_ratio": 1.50}
```

#### `calculate_metrics(weights, market_data)`
**Returns**: `Dict[str, Any]` with stock and sector exposures

---

## Configuration Parameters

### Risk Parameters

| Parameter | Type | Used By | Description |
|-----------|------|---------|-------------|
| `hurdle_rate` | float | All strategies | Minimum alpha score for inclusion |
| `target_beta` | float | Mean-Variance | Target portfolio beta (optional constraint) |
| `max_sector_exposure` | float | Diversifier | Maximum weight per sector (default: 0.30) |

### Strategy-Specific Settings

**Mean-Variance**:
- Optimizes Sharpe ratio
- Can add beta neutrality constraint

**CVaR**:
- Target return automatically set to mean alpha
- Focuses on tail risk minimization

**Omega**:
- Requires `hurdle_rate` in risk_params
- Converted to daily rate internally

---

## Monitoring and Logging

The system uses Python's logging module with INFO level by default.

**Log Format**:
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

**Key Log Messages**:
- `♻️  Rebuilding Database Schema...` - Table initialization
- `✅ PostgreSQL tables verified/created.` - Successful setup
- `[CREATOR:user_123] Creating fresh portfolio` - Service execution
- `[REBALANCER:user_456] Reallocating existing assets` - Rebalancing started

**Error Patterns**:
- `❌ Error creating initial tables: ...` - Database connection issues
- `Strategy X crashed: ...` - Optimization solver failure
- `No returns history. Using Equal Weights.` - Fallback triggered

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| **Empty optimization results** | Insufficient returns history or market data | Ensure pipeline has run for at least 60 minutes; check Kafka connectivity |
| **Covariance matrix errors** | Too few stocks or highly correlated returns | Increase universe size; check for duplicate symbols |
| **Solver failures (CVaR/Omega)** | Infeasible constraints or numerical issues | Reduce target return; check data quality; increase lookback window |
| **Database connection timeout** | PostgreSQL not accessible | Verify POSTGRES_HOST and port; check network connectivity |
| **Missing sector information** | Master stock list not loaded | Ensure master_stock_list table is populated in database |

### Data Quality Checks

```python
# Check market data freshness
df = DatabaseManager.fetch_market_data()
latest = df['timestamp'].max()
print(f"Latest data: {latest}")

# Verify returns history depth
returns_df = DatabaseManager.fetch_returns_history(lookback_minutes=60)
print(f"Returns shape: {returns_df.shape}")
print(f"Symbols with data: {len(returns_df.columns)}")
```

### Performance Tuning

**For low-latency requirements**:
- Reduce window sizes in Pathway pipeline
- Use `sample_cov` instead of Ledoit-Wolf shrinkage
- Decrease `lookback_minutes` in returns history fetch

**For stability**:
- Increase window sizes (10-15 seconds)
- Use longer lookback windows (120+ minutes)
- Enable covariance shrinkage

---

## System Requirements

- **CPU**: 4+ cores recommended for parallel stream processing
- **RAM**: 8GB minimum (16GB for large universes >500 stocks)

---

## License

This project is proprietary and confidential.

---

## Support

For technical issues or questions, contact the development team or file an issue in the project repository.