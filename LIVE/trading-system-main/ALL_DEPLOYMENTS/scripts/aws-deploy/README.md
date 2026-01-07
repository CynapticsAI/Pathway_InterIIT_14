# AWS Multi-Server Deployment

Deploy the trading system across 4 AWS EC2 instances using `scp` to upload files directly from your local machine.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AWS VPC                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     SERVER 1: KAFKA CLUSTER                          │    │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────────────────┐│    │
│  │  │ Zookeeper │ │   Kafka   │ │ Kafka UI  │ │   Shared Producers    ││    │
│  │  │   :2181   │ │   :9090   │ │   :8090   │ │ Finnhub,News,Macro... ││    │
│  │  └───────────┘ └─────┬─────┘ └───────────┘ └───────────────────────┘│    │
│  └──────────────────────┼──────────────────────────────────────────────┘    │
│                         │                                                    │
│         ┌───────────────┼───────────────┬───────────────┐                   │
│         │               │               │               │                   │
│         ▼               ▼               ▼               │                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │                   │
│  │  SERVER 2   │ │  SERVER 3   │ │  SERVER 4   │       │                   │
│  │ AWS Macro   │ │  Chronos    │ │  Portfolio  │       │                   │
│  │   :8000     │ │   :9000     │ │   :8080     │       │                   │
│  │             │ │             │ │  +Postgres  │       │                   │
│  └─────────────┘ └─────────────┘ └─────────────┘       │                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

### 1. EC2 Instances

Launch 4 EC2 instances (or 1 for single-server mode):

| Server | Purpose | Recommended Instance | Ports |
|--------|---------|---------------------|-------|
| Server 1 | Kafka + Producers | t3.xlarge (4 vCPU, 16GB) | 2181, 9090, 8090 |
| Server 2 | Macro API | t3.medium (2 vCPU, 4GB) | 8000 |
| Server 3 | Chronos API | t3.large (2 vCPU, 8GB) | 9000 |
| Server 4 | Portfolio API | t3.large (2 vCPU, 8GB) | 8080, 5433 |

### 2. Security Groups

**Kafka Server (Server 1):**
```
Inbound:
- SSH (22) from your IP
- Zookeeper (2181) from VPC CIDR
- Kafka (9090) from VPC CIDR
- Kafka External (29092) from VPC CIDR
- Kafka UI (8090) from your IP
```

**API Servers (Servers 2-4):**
```
Inbound:
- SSH (22) from your IP
- API Port (8000/9000/8080) from 0.0.0.0/0 or ALB
```

### 3. SSH Key

Ensure you have the SSH key (.pem file) for all instances.

## Deployment

### Quick Start

1. **Create configuration file:**

```bash
cd ALL_DEPLOYMENTS/scripts/aws-deploy

# Copy the template
cp servers.env.example servers.env

# Edit with your values
nano servers.env
```

2. **Configure `servers.env`:**

```bash
# SSH Configuration
SSH_KEY=~/.ssh/your-key.pem
SSH_USER=ubuntu

# Server IPs (for single-server, set all to the same IP)
KAFKA_SERVER=10.0.1.10
MACRO_SERVER=10.0.1.11
CHRONOS_SERVER=10.0.1.12
PORTFOLIO_SERVER=10.0.1.13

# API Keys
FINNHUB_API_KEY=your_finnhub_key
FRED_API_KEY=your_fred_key
FINVIZ_API_KEY=your_finviz_key

# Producer Configuration
FINNHUB_SYMBOLS=BINANCE:BTCUSDT,AAPL,TSLA,MSFT,NVDA
NEWS_TICKERS=NVDA,AAPL,TSLA,MSFT
SENTIMENT_TICKERS=TSLA,AAPL,MSFT,NVDA
```

3. **Run deployment:**

```bash
./deploy-all.sh                    # Uses servers.env
./deploy-all.sh production.env     # Or specify a different file
```

### Single-Server Mode

To deploy everything on one server, set all IPs to the same value:

```bash
KAFKA_SERVER=13.50.238.243
MACRO_SERVER=13.50.238.243
CHRONOS_SERVER=13.50.238.243
PORTFOLIO_SERVER=13.50.238.243
```

The script will automatically detect this and:
- Upload files only once
- Install Docker only once
- Deploy all services sequentially

## How It Works

The deployment script uses `scp` to copy files directly from your local machine:

1. **Upload**: Copies `ALL_DEPLOYMENTS/` folder to each server via `scp -r`
2. **Install**: Installs Docker and docker compose on each server
3. **Configure**: Creates `.env` file with API keys
4. **Deploy**: Runs the appropriate deployment script for each service

No GitHub access or tokens required!

## Configuration Reference

### servers.env Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `SSH_KEY` | Path to SSH private key | `~/.ssh/my-key.pem` |
| `SSH_USER` | SSH username | `ubuntu` or `ec2-user` |
| `KAFKA_SERVER` | Kafka server IP | `10.0.1.10` |
| `MACRO_SERVER` | Macro API server IP | `10.0.1.11` |
| `CHRONOS_SERVER` | Chronos server IP | `10.0.1.12` |
| `PORTFOLIO_SERVER` | Portfolio server IP | `10.0.1.13` |
| `FINNHUB_API_KEY` | Finnhub API key | Your API key |
| `FRED_API_KEY` | FRED API key | Your API key |
| `FINVIZ_API_KEY` | Finviz API key | Your API key |
| `FINNHUB_SYMBOLS` | Symbols for Finnhub | `AAPL,TSLA,MSFT` |
| `NEWS_TICKERS` | Tickers for news | `NVDA,AAPL,TSLA` |
| `SENTIMENT_TICKERS` | Tickers for sentiment | `TSLA,AAPL,MSFT` |

## Verification

### Check Kafka
```bash
# SSH to Kafka server
ssh -i your-key.pem ubuntu@KAFKA_SERVER

# List topics
docker exec global-kafka kafka-topics --bootstrap-server localhost:9090 --list

# Check producers are running
docker ps
```

### Check APIs
```bash
# From any machine with access
curl http://MACRO_SERVER:8000/predict/Energy
curl http://CHRONOS_SERVER:9000/
curl http://PORTFOLIO_SERVER:8080/
```

## Files

| File | Description |
|------|-------------|
| `servers.env.example` | Template configuration file |
| `deploy-all.sh` | Master script - deploys everything via scp |
| `server-kafka.sh` | Kafka server deployment |
| `server-macro.sh` | Macro API deployment |
| `server-chronos.sh` | Chronos API deployment |
| `server-portfolio.sh` | Portfolio API deployment |

## Troubleshooting

### SCP/SSH issues
```bash
# Test SSH connection
ssh -i your-key.pem ubuntu@SERVER_IP "echo OK"

# Check SSH key permissions
chmod 400 your-key.pem
```

### Kafka connection issues
```bash
# On API servers, verify Kafka connectivity
nc -zv KAFKA_SERVER_IP 9090

# Check if Kafka is accessible
docker exec -it container-name bash
apt-get update && apt-get install -y netcat
nc -zv kafka 9090
```

### Services not starting
```bash
# Check logs
docker compose logs -f

# Restart services
docker compose down && docker compose up -d
```

### Systemd services
```bash
# Check service status
sudo systemctl status kafka-cluster  # or macro-api, chronos-api, etc.

# View logs
sudo journalctl -u kafka-cluster -f

# Restart
sudo systemctl restart kafka-cluster
```

### Configuration issues
```bash
# Verify env file is loaded
cat ~/trading-system-main/ALL_DEPLOYMENTS/.env

# Check Docker environment
docker compose config
```
