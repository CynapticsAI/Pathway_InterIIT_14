# ALL_DEPLOYMENTS - Centralized Microservice Architecture

This repository contains a refactored microservice architecture with a **single shared Kafka cluster** and **centralized producers** that serve all deployments.

## Directory Structure

```
ALL_DEPLOYMENTS/
├── kafka_cluster/                    # Shared Kafka infrastructure
│   ├── docker compose.kafka.yml      # Kafka + Zookeeper
│   └── README.md
│
├── shared_producers/                 # Centralized producers
│   ├── common_finnhub_producer/      # Real-time stock data (Finnhub WebSocket)
│   ├── common_news_producer/         # News headlines (Finviz polling)
│   ├── common_sentiment_producer/    # Sentiment analysis (VADER)
│   ├── common_macro_producer/        # FRED economic data
│   └── common_spike_detector/        # Volume/volatility spike detection
│
├── aws_macro_deployment/             # Macro forecasting deployment
├── chronos_deploy_main/              # Chronos ML forecasting
├── portfolio_2/                      # Portfolio optimization
│
├── docker compose.global.yml         # Master compose for all shared services
└── .env.example                      # Environment variables template
```

## 🚀 Quick Start

### 1. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start Global Infrastructure

```bash
# Start Kafka cluster and all shared producers
docker compose -f docker compose.global.yml up -d
```

### 3. Start Individual Deployments

```bash
# AWS Macro Deployment
cd aws_macro_deployment && docker compose up -d

# Chronos Deployment
cd chronos_deploy_main && docker compose up -d

# Portfolio Deployment
cd portfolio_2 && docker compose up -d

```

## 🔌 Network Architecture

All services connect via the `global_kafka_network` Docker network.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        global_kafka_network                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      KAFKA CLUSTER                                │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐           │   │
│  │  │  Zookeeper  │───▶│    Kafka    │◀───│  Kafka UI   │           │   │
│  │  │  :2181      │    │  :9092      │    │  :8090      │           │   │
│  │  └─────────────┘    └─────────────┘    └─────────────┘           │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                              │                                           │
│  ┌───────────────────────────┼───────────────────────────────────────┐  │
│  │         SHARED PRODUCERS  │                                        │  │
│  │  ┌──────────┐ ┌──────────┐│┌──────────┐ ┌──────────┐ ┌──────────┐ │  │
│  │  │ Finnhub  │ │  News    │││Sentiment │ │  Macro   │ │  Spike   │ │  │
│  │  │ Producer │ │ Producer │││ Producer │ │ Producer │ │ Detector │ │  │
│  │  └────┬─────┘ └────┬─────┘│└────┬─────┘ └────┬─────┘ └────┬─────┘ │  │
│  └───────┼────────────┼──────┼─────┼────────────┼────────────┼───────┘  │
│          │            │      │     │            │            │          │
│          ▼            ▼      │     ▼            ▼            ▼          │
│     stock_data   news_data   │ sentiment   fred_econ   volume_vol      │
│                              │   _scores       _data       _data        │
│                              │                                          │
│  ┌───────────────────────────┼───────────────────────────────────────┐  │
│  │       DEPLOYMENTS         │                                        │  │
│  │  ┌─────────────┐  ┌───────┴─────┐  ┌─────────────┐  ┌──────────┐  │  │
│  │  │ Deployment  │  │  Deploy     │  │  Deploy     │  │ Strat    │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └──────────┘  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## 📊 Kafka Topics

| Topic | Producer | Consumers | Schema |
|-------|----------|-----------|--------|
| `stock_data` | common_finnhub_producer | chronos, sarimax, portfolio, spike_detector | `{s, p, t, v, r}` |
| `news_data` | common_news_producer | chronos, sarimax | `{dt_utc, ticker, source, title, url}` |
| `sentiment_scores` | common_sentiment_producer | portfolio | `{symbol, sentiment_score, t}` |
| `fred_economic_data` | common_macro_producer | aws_macro | `{date, fetch_timestamp, ...FRED series}` |
| `volume_volatility_data` | common_spike_detector | sarimax | `{timestamp, symbol, volume_zscore, volatility_zscore}` |
| `stock_scores` | portfolio/scorer | portfolio | `{symbol, stock_score, latest_price, ...}` |
| `sarimax_forecast` | sarimax | select_model | `{timestamp, symbol, final_combined_signal, ...}` |
| `chronos_infer_preds` | chronos | select_model | `{symbol, windowStart, windowEnd, preds_json}` |

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# API Keys
FINNHUB_API_KEY=your_key
FINVIZ_API_KEY=your_key
FRED_API_KEY=your_key

# Finnhub symbols
FINNHUB_SYMBOLS=BINANCE:BTCUSDT,AAPL,TSLA

# News/Sentiment tickers
NEWS_TICKERS=NVDA,AAPL,TSLA,MSFT
SENTIMENT_TICKERS=TSLA,AAPL,MSFT,NVDA
```

### Ports

| Service | Port | Description |
|---------|------|-------------|
| Kafka | 9092 (internal), 29092 (external) | Message broker |
| Zookeeper | 2181 | Kafka coordination |
| Kafka UI | 8090 | Web monitoring interface |
| AWS Macro API | 8000 | Macro predictions |
| Chronos API | 9000 | ML forecasting |
| Portfolio API | 8080 | Portfolio management |

## 📈 Deployment Details

### AWS Macro Deployment
- **Purpose**: Macroeconomic sector forecasting using FRED data
- **Consumes**: `fred_economic_data`
- **Features**: LSTM-based sector return predictions
- **API**: `/predict/{sector}` - Get sector forecast

### Chronos Deploy Main
- **Purpose**: Real-time stock price forecasting
- **Consumes**: `stock_data`, `news_data`, `volume_volatility_data`
- **Features**: Chronos ML model, SARIMAX, model selection
- **API**: Combined signal and model predictions

### Portfolio 2
- **Purpose**: Portfolio optimization and management
- **Consumes**: `stock_data`, `sentiment_scores`
- **Features**: Mean-Variance, CVaR, Omega optimization
- **Requires**: PostgreSQL database (included)
- **API**: Portfolio creation, rebalancing, diversification

- **Purpose**: Genetic Algorithm/Programming strategy discovery
- **Standalone**: No Kafka dependency (HTTP API only)
- **API**: `/gp` - GP strategy, `/ga` - GA strategy

## 🛠 Development

### Adding a New Deployment

1. Create new directory under `ALL_DEPLOYMENTS/`
2. Create `docker compose.yml` with:
   ```yaml
   networks:
     global_kafka_network:
       external: true
   ```
3. Use `KAFKA_BOOTSTRAP_SERVERS=kafka:9090`

### Adding a New Shared Producer

1. Create directory under `shared_producers/`
2. Include `producer.py`, `Dockerfile`, `requirements.txt`
3. Add to `docker compose.global.yml`
4. Document the topic in this README

## 🔍 Monitoring

### Kafka UI
Access at `http://localhost:8090` to:
- View topics and messages
- Monitor consumer groups
- Check broker health

### Logs
```bash
# View all global service logs
docker compose -f docker compose.global.yml logs -f

# View specific producer
docker logs -f common-finnhub-producer
```

## 🧹 Cleanup

```bash
# Stop all services
docker compose -f docker compose.global.yml down

# Stop and remove volumes
docker compose -f docker compose.global.yml down -v

# Clean up all deployments
  (cd $dir && docker compose down)
done
```

## 📝 Migration Notes

### What Changed

1. **Kafka Centralization**: All deployments now share a single Kafka cluster
2. **Producer Consolidation**: Duplicate producers merged into `shared_producers/`
3. **Network Unification**: All services use `global_kafka_network`
4. **Bootstrap Servers**: All services use `kafka:9090`

### Removed Components

From each deployment, the following were removed:
- Local Zookeeper instances
- Local Kafka brokers
- Duplicate producer services (now in `shared_producers/`)
