NOTE : ADD A key.pem FILE IN THE TECHNICAL ANALYSIS FOLDER IN ORDER TO EXECUTE.

<div align="center">
  <p><strong>Real-time Market Analysis and Forecasting with Pathway, SARIMAX, and Kubernetes</strong></p>
</div>

<p align="center">
    <a href="#overview">Overview</a> |
    <a href="#architecture">Architecture</a> |
    <a href="#sarimax--exogenous-forecast-consumer">SARIMAX + Exogenous Forecasting</a> |
    <a href="#kubernetes-implementation">Kubernetes Implementation</a> |
    <a href="#installation">Installation</a> |
    <a href="#usage">Usage</a> |
    <a href="#troubleshooting">Troubleshooting</a>
</p>

---

## Overview

We have built a containerized, streaming data pipeline to perform comprehensive, real-time analysis and forecasting on live stock market data.

This system uses a central Kafka producer to ingest live data from **Finnhub** and **FinViz**. This data is then consumed by a suite of parallel, independent streaming applications built with [Pathway](https://pathway.com). The key enhancement is the new **Kubernetes Job** workflow for the SARIMAX model, dynamically triggered to ensure scalable, on-demand forecasting.

### Key Features

-   **Live Data Ingestion**: Kafka producer fetches live stock (OHLC) from Finnhub and news headlines from FinViz.
-   **Multi-Consumer Analysis**: Run multiple analyses in parallel: **PnL tracking**, and **Market Breadth**, **Volume-Volatility Spike Detection** calculation.
-   **Hybrid Forecasting with Z-Scores**: The core **SARIMAX** time-series model now uses **Volume and Volatility Z-Scores** (derived from the Spike Detector) as robust **Exogenous Variables (X)**.
-   **Kubernetes-Native Scaling**: The SARIMAX model which is natively a univariate analysis model, is deployed as a **K8s Job**, enabling external API calls to trigger isolated, on-demand forecast instances for specific stock lists. 
-   **Real-time Stream Processing**: Powered by Pathway's high-performance Rust engine for stateful stream processing and temporal data fusion.

---

## Architecture

The system uses a one-to-many (fan-out) architecture. The Kafka cluster acts as the central message bus, and all consumers process streams independently. 

### 1. Data Producers (`producer.py`, `news_producer.py`)

-   **`producer.py`**: Connects to the **Finnhub API** for live time-series price data. Publishes to the **`stock_data`** Kafka topic.
-   **`news_producer.py`**: Connects to the **FinViz API** for real-time news headlines. Publishes to the **`news_data`** Kafka topic.

### 2. Streaming Consumers (Powered by Pathway)

All consumers are self-contained Pathway applications that take a Kafka stream as input and output live minute data.

| Folder Name | Input Topic                                                   | Key Functionality | Output |
| :--- |:--------------------------------------------------------------| :--- | :--- |
| **spike\_detector** | `stock_data`                                                  | Calculates rolling mean/standard deviation and outputs **Volume and Volatility Z-Scores**. These Z-Scores are the primary **exogenous variable** for SARIMAX. | `spike_detector_output` (Kafka Topic) |
| **pnl** | `stock_data`                                                  | Calculates real-time **Profit & Loss** for a defined portfolio. | `pnl_output` (Kafka Topic) |
| **market\_breadth** | `stock_data`                                                  | Calculates A/D ratios and other breadth indicators. | `breadth_output` (Kafka Topic) |
| **sarimaxConsumer** | `stock_data` + <br/>`spike_detector_output`+ <br/>`news_data` | Performs hybrid SARIMAX forecasting using price and Z-Scores. | `sarimax_forecast` (Kafka Topic) |

---

## The SARIMAX + Exogenous Forecast Consumer

This pipeline is the analytical heart, designed to fuse price data with real-time market activity metrics to produce forecasts.

It consumes two streams: **`stock_data`** (the endogenous price data) and **`spike_detector_output`** (the exogenous Z-Scores).

### 1. Volume and Volatility Z-Scores as Exogenous Variables (X)

We leverage the **Z-Score** as a powerful, normalized measure of unusual market activity, directly driving the SARIMAX model.

* **Z-Score Calculation**: The **Spike Detector** calculates Z-Scores of volume and volatility across 1 minute data. Where standard deviation and mean of volume and volatility are calculated in those 1 minute windows.
* **Model Input**: These standardized scores Z_Volume and Z_Volatility are used as the exogenous variables in the SARIMAX model, where SARIMAX predicts scaled prices = (prices - mean)/std dev. A high Z-Score indicates a statistically significant spike in trading interest or market uncertainty, providing the model with real-time explanatory power. 

### 2. Temporal Data Fusion (Pathway)

The key to combining the streams is **Pathway's temporal `asof_join`**.

* This join aligns the price data with the Z-Scores by time, ensuring each price observation is matched with the **most recent** Z-Score available *at or before* that time.
* This method guarantees **no look-ahead bias** and correctly simulates a real-world predictive scenario.

### 3. Continuous Learning and Rolling Forecasts

The model runs on a **rolling time window** of fused data. The SARIMAX parameters are fit on the most recent data segment (e.g., the last 3 hours), ensuring the forecast is continuously adapted to the market's evolving structural patterns and recent exogenous influences.

---

## ☁️ Kubernetes Implementation

The forecasting consumer is deployed as a **Kubernetes Job** to handle dynamic scaling and isolated execution.

### The Trigger Workflow

1.  **Client Request**: A user sends a `POST` request to the **FastAPI API** (`sarimax_api`) with a list of tickers to forecast.
2.  **ConfigMap Update**: The API first updates the **K8s ConfigMap (`stock-list.yaml`)** with the new list of tickers.
3.  **Job Creation**: The API uses `kubectl` to dynamically launch a new Kubernetes Job (e.g., `manual-test-run-0`). This job uses the **SARIMAX Docker image** and reads the stock list from the updated ConfigMap.
4.  **Job Execution**: The Pod runs, connects to Kafka, performs the forecast, publishes results to the **`sarimax_forecast`** topic, and then terminates.

### Why K8s Jobs?

-   **On-Demand Processing**: Forecasting is resource-intensive and does not need to run constantly. Jobs spin up, do the work, and shut down, saving cost and resources.
-   **Isolation**: Each forecast request runs in its own dedicated Pod, preventing resource contention.
-   **Reproducibility**: K8s Jobs track execution details, status, and logs, simplifying auditing and debugging of individual forecast runs.

---

## Installation

### Prerequisites

-   Python 3.10+
-   **Docker** and **Docker Compose**
-   **Kubernetes (K3s, Minikube, etc.)** installed and configured.
-   **`kubectl`** access on the machine running the **`sarimax_api`** (typically the host EC2 instance).

### Setup

1.  **Configure environment**: Complete the `.env` file with your **`FINNHUB_API_KEY`**, **`FINVIZ_API_KEY`**, and correct pathing for `kubeconfig` used by the FastAPI service.
2.  **Build Core Images**: Build the Docker images for the producer and core Pathway consumers.
    ```bash
    docker compose build
    ```
3.  **Start Core Stack**: Start Kafka, Zookeeper, and the main Pathway services (including the **Spike Detector** to generate $X_t$).
    ```bash
    docker compose up -d
    ```
4.  **Deploy K8s Resources**: Apply the job/cronjob template to your Kubernetes cluster.
    ```bash
    kubectl apply -f market-cronjob.yaml
    ```

---

## Usage: Triggering a Forecast

Forecasting is initiated via the FastAPI endpoint running on your server.

1.  **Trigger the Forecast Job**:

    ```bash
    Invoke-RestMethod -Uri "http://<YOUR_AWS_IP>:8888/forecast" `
      -Method POST `
      -ContentType "application/json" `
      -Body '{"stocks": ["TSLA", "AAPL", "MSFT"], "run_immediately": true}'
    ```

2.  **Monitor the Job**: Observe the Pod spin-up and execution using `kubectl`.

    ```bash
    kubectl get pods
    # Then view the logs:
    kubectl logs <manual-test-run-pod-name>
    ```

---

## Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **K8s Job Pod is `Terminating`** | The application inside the Pod (the SARIMAX script) crashed immediately. | Use `kubectl logs <pod-name>` to find the specific Python traceback (e.g., Kafka connection errors, misread ConfigMap). |
| **FastAPI returns `Command timed out`** | The Job creation or Docker image import process exceeded the API's timeout (usually 120s) due to a slow network or server. | **Increase the timeout** in the `run_command` function within your `sarimax_api` code to 600 seconds. |
| **Job creates 5+ Pods** | The job YAML has `parallelism` or `completions` set too high. | Edit `market-cronjob.yaml` and set `spec.jobTemplate.spec.parallelism: 1` and `completions: 1`. |
| **SARIMAX fails to fit (NaN)** | Insufficient data or data quality issues in the fused stream. | Ensure the **`spike_detector_output`** topic is actively receiving data. Check that the rolling window size provides enough observations for the model's complexity. |