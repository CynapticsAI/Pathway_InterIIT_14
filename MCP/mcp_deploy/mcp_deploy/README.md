# MCP Deploy - Financial AI Agent Platform

A comprehensive Model Context Protocol (MCP) server that provides AI agents with powerful financial analysis tools, including live RAG (Retrieval-Augmented Generation), portfolio management, web search, market data access, and strategy optimization capabilities.

## 🌟 Features

### Core Capabilities
- **Live RAG Systems**: Dual RAG endpoints for SEC filings and tax documents
- **Portfolio Management**: Create, rebalance, and diversify portfolios using advanced strategies (CVaR, Omega, Mean-Variance)
- **Market Data**: Real-time OHLC data and predictions for cryptocurrencies
- **Web Search**: Intelligent web search with domain whitelisting for financial sources
- **Strategy Optimization**: Genetic Programming and Genetic Algorithm-based trading strategy optimization
- **Macro Analysis**: Sector-specific macroeconomic data retrieval

### MCP Tools Available
- `get_portfolio` - Retrieve user portfolio allocations
- `get_ohlc` - Get OHLC data for crypto tickers
- `get_preds` - Retrieve price predictions
- `get_macro` - Fetch macroeconomic data by sector
- `live_rag_sec` - Query SEC documents via RAG
- `live_rag_tax` - Query tax documents via RAG
- `list_documents_sec` - List available SEC documents
- `list_documents_tax` - List available tax documents
- `search_web` - General web search with content extraction
- `search_web_whitelist` - Search restricted to trusted financial domains
- `rebalance_portfolio` - Rebalance existing portfolio
- `diversify_portfolio` - Diversify portfolio with constraints
- `create_portfolio` - Create new portfolio from scratch
- `get_backtest_data` - Retrieve historical backtest datasets
- `create_strategy` - Generate trading strategies using GP
- `optimize_strategy` - Optimize strategies using GA

## 📋 Prerequisites

- **Docker** and **Docker Compose** installed
- **Python 3.9+** (for local development)
- Required API keys (see below)

## 🔑 Required API Keys

You need to set up the following API keys as environment variables:

### 1. SERPER_API_KEY
**Purpose**: Web search functionality via Google Serper API  
**Get it from**: [https://serper.dev](https://serper.dev)  
**Used by**: `search_web` and `search_web_whitelist` tools

### 2. PATHWAY_LICENSE_KEY
**Purpose**: Pathway framework for RAG systems  
**Get it from**: [https://pathway.com](https://pathway.com)  
**Used by**: `multi_rag` and `tax_rag` services

### 3. GEMINI_API_KEY
**Purpose**: Google Gemini API for embeddings and AI features  
**Get it from**: [https://ai.google.dev](https://ai.google.dev)  
**Used by**: RAG services for document processing

### 4. OPENAI_API_KEY
**Purpose**: OpenAI API (optional, for alternative embeddings)  
**Get it from**: [https://platform.openai.com](https://platform.openai.com)  
**Used by**: RAG services as fallback option

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd mcp_deploy
```

### 2. Set Up Environment Variables

Create a `.env` file in the root directory:

```bash
# Required API Keys
SERPER_API_KEY=your_serper_api_key_here
PATHWAY_LICENSE_KEY=your_pathway_license_key_here
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Pathway port configuration
PATHWAY_PORT=6060
```

### 3. Start the Services

Using Docker Compose (recommended):

```bash
docker-compose up -d
```

This will start all services:
- **tools**: MCP server (port 1234)
- **multi_rag**: SEC documents RAG service
- **tax_rag**: Tax documents RAG service
- **ohlc**: OHLC data service
- **postgres**: PostgreSQL database

### 4. Verify Services are Running

```bash
docker-compose ps
```

All services should show as "Up" or "healthy".

### 5. Test the MCP Server

The MCP server will be available at:
```
http://localhost:1234
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      MCP Server (app.py)                     │
│                         Port: 1234                           │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐     ┌──────────────┐
│  multi_rag   │      │   tax_rag    │     │     ohlc     │
│  (SEC docs)  │      │ (Tax docs)   │     │  (Market)    │
└──────────────┘      └──────────────┘     └──────────────┘
                                                   │
                                                   ▼
                                           ┌──────────────┐
                                           │  PostgreSQL  │
                                           └──────────────┘
```

## 📁 Project Structure

```
mcp_deploy/
├── app.py                    # Main MCP server implementation
├── app.yaml                  # Configuration file
├── requirements.txt          # Python dependencies
├── Dockerfile               # Docker image for MCP server
├── compose.yaml             # Docker Compose orchestration
├── pathway_backend/         # Backend services
│   ├── live_rag/           # RAG services
│   │   ├── multimodal_rag/ # SEC documents RAG
│   │   └── tax_rag/        # Tax documents RAG
│   ├── ohlc/               # OHLC data service
│   ├── macrodata/          # Macro data service
│   └── postgres_init/      # Database initialization
└── consumer/               # Data consumers
```

## ⚙️ Configuration

The `app.yaml` file contains all service endpoints and timeout configurations:

```yaml

### Timeout Settings

Each service has configurable timeouts in `app.yaml`:
- `timeout_macro`: Macroeconomic data requests
- `timeout_preds`: Prediction requests
- `timeout_rag`: RAG retrieval requests
- `timeout_port`: Portfolio operations
- `timeout_strat`: Strategy optimization

## 🔧 Development Setup

### Local Development (without Docker)

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set environment variables**:
```bash
export SERPER_API_KEY=your_key_here
export PATHWAY_LICENSE_KEY=your_key_here
export GEMINI_API_KEY=your_key_here
export OPENAI_API_KEY=your_key_here
```

3. **Run the server**:
```bash
python app.py
```


## 🛠️ Troubleshooting

### Services Won't Start

1. **Check Docker is running**:
```bash
docker --version
docker-compose --version
```

2. **Check environment variables**:
```bash
docker-compose config
```

3. **View service logs**:
```bash
docker-compose logs -f tools
docker-compose logs -f multi_rag
```

### Database Connection Issues

```bash
# Restart PostgreSQL
docker-compose restart postgres

# Check database logs
docker-compose logs postgres
```

### RAG Services Not Responding

```bash
# Check if data directories exist
ls -la pathway_backend/live_rag/multimodal_rag/data
ls -la pathway_backend/live_rag/tax_rag/data

# Restart RAG services
docker-compose restart multi_rag tax_rag
```

## 🔒 Security Notes

- **Never commit API keys** to version control
- Use `.env` file for local development
- Use secrets management in production (e.g., AWS Secrets Manager, HashiCorp Vault)
- The whitelisted domains in `search_web_whitelist` are pre-configured for trusted financial sources


**Built with**: FastMCP, Pathway, PostgreSQL, Docker, and various AI/ML services
