<div align="center">
  <p><strong>Real-time Market Analysis and Forecasting with Pathway, SARIMAX, and VADER</strong></p>
</div>

<p align="center">
    <a href="#overview">Overview</a> |
    <a href="#architecture">Architecture</a> |
    <a href="#focus-the-sarimax--vader-forecast-consumer">SARIMAX+VADER</a> |
    <a href="#installation">Installation</a> |
    <a href="#usage">Usage</a> |
    <a href="#configuration">Configuration</a> |
    <a href="#deployment">Deployment</a>
</p>

## Overview

We have built a containerized, streaming data pipeline to perform comprehensive, real-time analysis and forecasting on live stock market data.

This system uses a central Kafka producer to ingest live ticker and news data from **Finnhub** and **FinViz** respectively. This data is then consumed by a suite of parallel, independent streaming applications built with [Pathway](https://pathway.com). These consumers perform specialized tasks ranging from technical analysis and market breadth calculation to sophisticated time-series forecasting.

### Key Features

-   **Live Data Ingestion**: Kafka producer fetches live stock (OHLC) from Finnhub and stock-wise news headlines from FinViz using Pathway-Kafka connectors.
-   **Multi-Consumer Architecture**: Run multiple analyses in parallel:
    -   Sector-Wise Relative Rotation Graph (RRG) plotting
    -   Real-time volume and volatility detection
    -   Market breadth calculation (e.g., Advance/Decline line)
    -   Profit & Loss (PnL) tracking
-   **Hybrid Forecasting**: A dedicated forecasting pipeline that combines **SARIMAX** time-series models with **VADER** sentiment scores as an exogenous variable.
-   **Real-time Stream Processing**: Powered by Pathway's high-performance Rust engine for stateful stream processing and temporal joins.
-   **Containerized & Scalable**: Entire application stack (producer, consumers, Kafka) is managed via **Docker Compose** for easy setup and deployment.

---

## Architecture

The system is designed with a one-to-many (fan-out) architecture. A single producer feeds data into Kafka, and multiple Pathway consumers process these streams independently, using Pathways high speed connectors for data ingestion.



### 1. Data Producers (`producer.py`, `news_producer.py`)

-   producer.py connects to the Finnhub API using a dedicated API key.
-   news_producer.py connects to the FinViz API.
-   Fetches live time-series data price data and news headlines stock symbol-wise .
-   Publishes data to distinct Kafka topics `stock_data` and `news_data` respectively.

### 2. Streaming Consumers (Powered by Pathway)

All consumers are built as Pathway applications that connect to Kafka topics for input.

-   **RRG Consumer ( `rrg_calculator.py`)**:
    -   Consumes `stock_data` stream.
    -   Calculates relative strength and momentum for a basket of stocks.
    -   Outputs RRG coordinate data points to `rrg_output.jsonl` for plotting.

-   **Volatility and Volume Spike Detector (`spike_detector.py`)**:
    -   Consumes `stock_data` stream.
    -   Uses Pathway's temporal windowby's and custom UDF-reducers to output live volume and volatility.
    -   **Volume Detection**: Monitors for unusual volume spikes (e.g., > 3x rolling average).
    -   **Volatility Detector**: Calculates rolling volatility and flags unusual changes.
    
-   **Live PnL and Risk Assessment ( `pnl.py`)**:
    -   Consumes `stock_data` stream and user's current portfolio.
    -   Calculates overall PnL of portfolio , and percent changes in the portfolios' profits.
    -   Can detect sudden unexpected changes in portfolio PnL to alert the user.
-   **Market Breadth Calculation (`breadth.py`)**:
    -   Consumes `stock_data` stream.
    -   **Volume Detector**: Monitors for unusual volume spikes (e.g., > 3x rolling average).
    -   **Volatility Detector**: Calculates rolling volatility (e.g., ATR) and flags unusual changes.
    -   **Market Breadth**: Calculates A/D ratios or other breadth indicators.
---

## The SARIMAX + VADER Forecast Consumer

This consumer is the analytical core of the pipeline, designed to generate high-frequency price forecasts by merging classical time-series analysis with real-time news sentiment.

It operates by consuming two distinct Kafka streams in parallel:
1.  `stock_data`: The high-frequency (e.g., 1-minute) price data.
2.  `news_data`: The real-time stream of financial news headlines.

### 1. Sentiment as an Exogenous Variable (VADER)

Before a model can use news, it must be quantified. We use **VADER** (Valence Aware Dictionary and sEntiment Reasoner) for this task.

* **Why VADER?**: VADER is a lexicon-based, rules-based sentiment analysis tool. Unlike models that require heavy training (like BERT), VADER is extremely lightweight and fast, making it perfect for a real-time streaming pipeline. It's also specifically tuned for social media and short-text formats, which share characteristics with financial news headlines.
* **Process**:
    1.  The `sarimax_forecast` application ingests a news item from the `news_data` topic.
    2.  VADER's `SentimentIntensityAnalyzer` is immediately applied to the headline text.
    3.  This outputs a `compound` score, a single metric from -1.0 (most negative) to +1.0 (most positive).
    4.  This timestamped sentiment score is now a new, quantified data stream.

### 2. Temporal Data Fusion (Pathway)

A key challenge is aligning the two different data types: price data (which arrives on a regular clock, e.g., every minute) and news data (which arrives sporadically).

This is solved using **Pathway's temporal `asof_join`**:

* The pipeline maintains tables of both the price stream and the sentiment stream.
* The `asof_join` aligns these streams by time, ensuring that each price bar (e.g., the 10:30 AM bar) is joined with the **most recent sentiment score** that occurred *at or before* 10:30 AM.
* This is crucial for preventing look-ahead bias, as it correctly simulates a real-world scenario where you are making a prediction based only on information available at that exact moment.
* We also added a sentiment decay mechanism where if news for a stock is not refreshed for a long period of time the score linear decays to 0 proportional to time since last news.
---

### 3. SARIMAX Seasonality: The `(P, D, Q, m)` Parameters

The "S" in SARIMAX is what makes it so powerful for financial data, which often has clear, repeating patterns (seasonality).

The model takes a second set of parameters for this: `(P, D, Q, m)`.

* `P`: The seasonal AutoRegressive order.
* `D`: The seasonal Integrated (differencing) order.
* `Q`: The seasonal Moving Average order.
* `m`: **The Seasonal Period**. This is the most important one. It's the number of time steps it takes for a full seasonal cycle to repeat.

By setting these parameters (e.g., `SARIMAX(order=(p,d,q), seasonal_order=(P,D,Q,m))`), the model can account for *both* the short-term price-to-price movements *and* the broader, repeating seasonal patterns, all while being influenced by the **VADER sentiment score** as an external factor.

### 4. Continuous Learning

The model isn't static. The `sarimax_forecast` pipeline runs this process on a **rolling window**. For example, it might retrain the SARIMAX model every 15 minutes using the last 2 hours of fused data. This ensures the model is constantly adapting to the latest market structure and sentiment-price relationship.

---

## Installation

### Prerequisites

-   Python 3.10 or above
-   Docker and Docker Compose
-   An **Finnhub API Key**
-   A **FinViz API Key**

### Setup

1.  **Configure environment**:
    In respective directory with .env.sample add necessary API keys specified such as:
    ```.env
    FINNHUB_API_KEY = "YOUR_FINNHUB_API_KEY"
    FINVIZ_API = "YOUR_FINVIZ_API_KEY"
    ```
2.  **Build the containers**:
    This command will build the Docker images for the producer and all consumers defined in your `docker-compose.yml`.
    ```bash
    docker-compose build
    ```

---

## Usage

### Running the System

Start the entire pipeline (Kafka, Zookeeper, Producer, and all Consumers) in detached mode:

```bash
docker-compose up -d
```



### Monitoring Logs

To monitor individual containers and isolate issues use the following command:

```bash
docker logs -f <container_name>
```

### Stopping Individual Containers

To stop running individual containers or the entire pipeline:

```bash
#individual container
docker stop <container_name>

#all containers
docker-compose down 
```
## Troubleshooting

**Issue : Consumers are not receiving data** 
**Solution**: 
- Check the `producer` logs (`docker-compose logs producer`) for API key errors or connection issues with Finnhub. 
- Ensure Kafka is running and topics are created.

**Issue : SARIMAX model fails to fit or gives NaN predictions**  
**Solution**: 
- Ensure data is being joined correctly. Check that `news_data` topic is receiving data for VADER. 
- The (p,d,q) `SARIMAX_ORDER` may need tuning. 
- The model requires a "burn-in" period to collect enough data. Check for errors related to insufficient data.


