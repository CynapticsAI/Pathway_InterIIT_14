# 🚀 Quick Reference - Django Trading API

## 📦 Project Structure
```
technical_analysis/
├── django_api/              ← NEW! Complete Django REST API
│   ├── apps/
│   │   ├── market_data/    → OHLC, Market Breadth
│   │   ├── signals/        → Spike Alerts, SARIMAX, Combined Signals
│   │   ├── portfolio/      → Positions, P&L
│   │   ├── sentiment/      → News, Sentiment Scores
│   │   └── rrg/            → RRG Coordinates
│   ├── config/             → Django settings
│   └── manage.py
├── finnhub_producer/       → Live tick data from Finnhub
├── market_breadth/         → Advance/Decline calculator
├── spike_detector/         → Volume/Volatility alerts
├── pnl/                    → Portfolio P&L tracker
├── sarimaxConsumer/        → SARIMAX + VADER forecasting
├── news_producer/          → FinViz news scraper
└── rrg/                    → RRG calculator
```

## 🎯 Key Features You Built

### ✅ All Data Sources Centralized
- **11 Database Models** storing all Pathway output
- **30+ REST API Endpoints** for querying data
- **Real-time JSONL monitoring** with auto-updates
- **Auto-generated API docs** (Swagger + ReDoc)

### ✅ Complete API Coverage

| Feature | REST Endpoint | Description |
|---------|--------------|-------------|
| **OHLC Bars** | `/api/market-data/ohlc/` | 1-min candlesticks |
| **Market Breadth** | `/api/market-data/breadth/` | Advance/Decline stats |
| **Spike Alerts** | `/api/signals/spike-alerts/` | Volume/Volatility spikes |
| **SARIMAX** | `/api/signals/sarimax/` | Price forecasts |
| **Combined Signals** | `/api/signals/combined/` | SARIMAX + Sentiment |
| **Portfolio** | `/api/portfolio/positions/` | Holdings (CRUD) |
| **Position P&L** | `/api/portfolio/position-pnl/` | Per-position P&L |
| **Total P&L** | `/api/portfolio/total-pnl/` | Portfolio-wide P&L |
| **News** | `/api/sentiment/news/` | Headlines |
| **Sentiment** | `/api/sentiment/scores/` | VADER scores |
| **RRG** | `/api/rrg/coordinates/` | Relative Rotation |

## 🚀 Getting Started (3 Commands)

```bash
# 1. Run setup script
./setup_django_api.sh

# 2. Create admin user
docker-compose exec django_api python manage.py createsuperuser

# 3. Open API docs
open http://localhost:8000/api/docs/
```

## 🔗 Important URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **API Docs** | http://localhost:8000/api/docs/ | Swagger UI |
| **Admin** | http://localhost:8000/admin/ | Django admin |
| **API Root** | http://localhost:8000/api/ | Browsable API |
| **ReDoc** | http://localhost:8000/api/redoc/ | Alternative docs |
| **Spike Dashboard** | http://localhost:8001 | Pathway/Bokeh |
| **Market Breadth** | http://localhost:8002 | Pathway/Panel |
| **SARIMAX** | http://localhost:8007 | Pathway output |

## 📊 Example API Calls

### Get Latest Data
```bash
# Latest OHLC for all symbols
curl http://localhost:8000/api/market-data/ohlc/latest/

# Latest combined signals
curl http://localhost:8000/api/signals/combined/latest/

# Latest portfolio P&L
curl http://localhost:8000/api/portfolio/total-pnl/latest/

# Latest RRG by quadrant
curl http://localhost:8000/api/rrg/coordinates/by_quadrant/
```

### Filter Data
```bash
# NVDA spike alerts with high z-score
curl "http://localhost:8000/api/signals/spike-alerts/?symbol=NVDA&min_volume_zscore=3.0"

# AAPL combined signals above 0.3
curl "http://localhost:8000/api/signals/combined/?symbol=AAPL&min_signal=0.3"

# OHLC bars in time range
curl "http://localhost:8000/api/market-data/ohlc/?start_time=2025-11-18T09:00:00Z&end_time=2025-11-18T10:00:00Z"
```

## 🐳 Docker Commands

```bash
# Start everything
docker-compose up -d

# Stop everything
docker-compose down

# View logs
docker-compose logs -f django_api
docker-compose logs -f django_consumer

# Check status
docker-compose ps

# Restart consumer
docker-compose restart django_consumer

# Run migrations
docker-compose exec django_api python manage.py migrate

# Shell access
docker-compose exec django_api python manage.py shell
```

## 🛠️ Management Commands

```bash
# Main consumer (monitors all JSONL files)
docker-compose exec django_api python manage.py consume_all_jsonl

# Individual consumers
docker-compose exec django_api python manage.py consume_ohlc_jsonl
docker-compose exec django_api python manage.py consume_breadth_jsonl
docker-compose exec django_api python manage.py consume_stock_data
```

## 📁 Data Flow

```
Pathway Consumers → JSONL Files → Django Consumer → PostgreSQL → REST API
```

**Monitored Files:**
- `/data/spike_detector/spike_alerts.jsonl`
- `/data/sarimax/final_combined_signal.jsonl`
- `/data/sarimax/sarimax_signal.jsonl`
- `/data/pnl/positions_pnl.jsonl`
- `/data/pnl/total_portfolio_pnl.jsonl`
- `/data/rrg/rrg_output.jsonl`

## 🎨 Response Examples

### Combined Signal Response
```json
{
  "id": 1,
  "timestamp": "2025-11-18T10:30:00Z",
  "symbol": "AAPL",
  "final_combined_signal": 0.45,
  "sarimax_signal": 0.52,
  "sentiment_score": 0.31,
  "last_seen_headline": "Apple announces new product",
  "current_price": 175.50,
  "forecast_price": 176.25,
  "signal_interpretation": "STRONG BUY"
}
```

### RRG by Quadrant Response
```json
{
  "Leading": [
    {"symbol": "NVDA", "rs_ratio": 105.2, "rs_momentum": 103.5}
  ],
  "Improving": [
    {"symbol": "AAPL", "rs_ratio": 98.5, "rs_momentum": 101.2}
  ],
  "Lagging": [
    {"symbol": "TSLA", "rs_ratio": 95.3, "rs_momentum": 97.8}
  ],
  "Weakening": [
    {"symbol": "AMZN", "rs_ratio": 102.1, "rs_momentum": 99.5}
  ]
}
```

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| **Port 8000 in use** | `docker-compose down` or change port in docker-compose.yml |
| **Database error** | `docker-compose restart db` |
| **Consumer not updating** | Check file paths: `docker-compose exec django_consumer ls -la /data/` |
| **Migration issues** | `docker-compose exec django_api python manage.py migrate` |

## 📚 Documentation Files

- **`django_api/README.md`** - Full Django API documentation
- **`DJANGO_API_SUMMARY.md`** - Complete implementation summary
- **This file** - Quick reference guide

## 🎯 Next Steps

1. **Test the API** - Visit http://localhost:8000/api/docs/
2. **Create Admin User** - `docker-compose exec django_api python manage.py createsuperuser`
3. **Monitor Data Flow** - Check logs: `docker-compose logs -f django_consumer`
4. **Build Frontend** - Use any framework (React, Vue, etc.) to consume the API
5. **Add WebSocket** - Implement real-time broadcasting (marked as TODO)

## 📊 Database Schema

```
OHLCBar          → symbol, timestamp, open, high, low, close, volume
MarketBreadth    → timestamp, advancing, declining, ad_line
SpikeAlert       → symbol, timestamp, volume_zscore, volatility_zscore
SarimaxSignal    → symbol, timestamp, signal, forecast_price
CombinedSignal   → symbol, timestamp, combined_signal, sentiment
PortfolioPosition → symbol, quantity, cost_basis
PositionPnL      → symbol, timestamp, unrealized_pnl, pnl_pct
TotalPortfolioPnL → timestamp, total_pnl, pnl_pct
NewsItem         → ticker, timestamp, title, url
SentimentScore   → symbol, timestamp, score, headline
RRGCoordinate    → symbol, timestamp, rs_ratio, rs_momentum
```

---

**🎉 You're all set! Happy trading!** 📈
