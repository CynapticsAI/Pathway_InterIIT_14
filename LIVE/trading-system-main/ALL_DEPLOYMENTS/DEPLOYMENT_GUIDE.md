# Deployment Guide: Local Testing & AWS Deployment

This guide covers how to test the centralized microservice architecture locally and deploy it to AWS.

---

## Part 1: Local Testing

### Prerequisites

- Docker Desktop (v20.10+)
- Docker Compose (v2.0+)
- 8GB+ RAM available for Docker
- API Keys:
  - Finnhub API Key (https://finnhub.io/)
  - FRED API Key (https://fred.stlouisfed.org/docs/api/api_key.html)
  - Finviz Elite API Key (optional, for premium features)

### Step 1: Configure Environment

```bash
cd ALL_DEPLOYMENTS

# Copy environment template
cp .env.example .env

# Edit with your API keys
nano .env  # or use your preferred editor
```

**Required `.env` configuration:**
```bash
# Required API Keys
FINNHUB_API_KEY=your_finnhub_key_here
FRED_API_KEY=your_fred_key_here

# Optional
FINVIZ_API_KEY=your_finviz_key_here

# Symbols to track (customize as needed)
FINNHUB_SYMBOLS=BINANCE:BTCUSDT,AAPL,TSLA,MSFT,NVDA
NEWS_TICKERS=NVDA,AAPL,TSLA,MSFT
SENTIMENT_TICKERS=TSLA,AAPL,MSFT,NVDA
```

### Step 2: Start Global Infrastructure

```bash
# Start Kafka cluster and all shared producers
docker compose -f docker compose.global.yml up -d

# Watch the logs to ensure everything starts correctly
docker compose -f docker compose.global.yml logs -f
```

**Expected startup order:**
1. Zookeeper (10-15 seconds)
2. Kafka (30-40 seconds after Zookeeper)
3. Kafka UI
4. All shared producers

### Step 3: Verify Kafka Cluster

```bash
# Check all containers are running
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Expected output:
# global-zookeeper    Up (healthy)    2181/tcp
# global-kafka        Up (healthy)    9092/tcp, 29092/tcp
# kafka-ui            Up              8080->8090/tcp
# common-finnhub-producer   Up
# common-news-producer      Up
# common-sentiment-producer Up
# common-macro-producer     Up
# common-spike-detector     Up
```

**Access Kafka UI:** http://localhost:8090

In Kafka UI, verify:
- Topics are being created (`stock_data`, `news_data`, `sentiment_scores`, etc.)
- Messages are flowing through topics

### Step 4: Test Individual Producers

```bash
# Check Finnhub producer logs
docker logs -f common-finnhub-producer

# Expected: WebSocket connection messages and trade data

# Check News producer logs
docker logs -f common-news-producer

# Expected: Polling cycle messages and news headlines

# Check Spike detector logs
docker logs -f common-spike-detector

# Expected: Connected to Kafka, processing stock_data
```

### Step 5: Start Individual Deployments

#### Option A: Start All Deployments
```bash
# AWS Macro Deployment
cd aws_macro_deployment && docker compose up -d && cd ..

# Chronos Deployment
cd chronos_deploy_main && docker compose up -d && cd ..

# Portfolio Deployment
cd portfolio_2 && docker compose up -d && cd ..

```

#### Option B: Start Specific Deployment
```bash
# Just Portfolio deployment
cd portfolio_2
docker compose up -d
docker compose logs -f
```

### Step 6: Verify API Endpoints

| Service | URL | Test Command |
|---------|-----|--------------|
| Kafka UI | http://localhost:8090 | Browser |
| AWS Macro API | http://localhost:8000 | `curl http://localhost:8000/predict/Energy` |
| Chronos API | http://localhost:9000 | `curl http://localhost:9000/` |
| Portfolio API | http://localhost:8080 | `curl http://localhost:8080/` |

### Step 7: Monitor Data Flow

```bash
# Watch messages in a specific topic
docker exec global-kafka kafka-console-consumer \
  --bootstrap-server localhost:9090 \
  --topic stock_data \
  --from-beginning \
  --max-messages 10

# List all topics
docker exec global-kafka kafka-topics \
  --bootstrap-server localhost:9090 \
  --list

# Check topic details
docker exec global-kafka kafka-topics \
  --bootstrap-server localhost:9090 \
  --describe --topic stock_data
```

### Step 8: Cleanup (Local)

```bash
# Stop all deployments
cd ALL_DEPLOYMENTS
  (cd $dir && docker compose down)
done

# Stop global services
docker compose -f docker compose.global.yml down

# Remove all data (optional)
docker compose -f docker compose.global.yml down -v
docker system prune -f
```

---

## Part 2: AWS Deployment

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AWS Cloud                                    │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    VPC (10.0.0.0/16)                         │   │
│  │  ┌─────────────────┐  ┌─────────────────┐                   │   │
│  │  │ Public Subnet   │  │ Private Subnet  │                   │   │
│  │  │ (APIs/ALB)      │  │ (Kafka/Workers) │                   │   │
│  │  └─────────────────┘  └─────────────────┘                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  Option A: EC2 with Docker Compose                                  │
│  Option B: ECS/Fargate                                              │
│  Option C: EKS (Kubernetes)                                         │
│  Option D: Amazon MSK (Managed Kafka)                               │
└─────────────────────────────────────────────────────────────────────┘
```

### Option A: EC2 Deployment (Simplest)

#### 1. Launch EC2 Instance

```bash
# Recommended specs:
# - Instance Type: t3.xlarge (4 vCPU, 16GB RAM) or larger
# - AMI: Amazon Linux 2023 or Ubuntu 22.04
# - Storage: 100GB gp3
# - Security Group: Allow ports 22, 80, 443, 8000-8090, 9092
```

#### 2. Install Dependencies on EC2

```bash
# Connect to EC2
ssh -i your-key.pem ec2-user@your-ec2-ip

# Install Docker
sudo yum update -y
sudo yum install -y docker git
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker compose
sudo chmod +x /usr/local/bin/docker compose

# Logout and login to apply docker group
exit
ssh -i your-key.pem ec2-user@your-ec2-ip
```

#### 3. Clone and Configure

```bash
# Clone repository
git clone https://github.com/Harshvardhan-To1/all_deployments.git
cd all_deployments/ALL_DEPLOYMENTS

# Configure environment
cp .env.example .env
nano .env  # Add your API keys
```

#### 4. Start Services

```bash
# Start global infrastructure
docker compose -f docker compose.global.yml up -d

# Wait for Kafka to be healthy (check logs)
docker compose -f docker compose.global.yml logs -f kafka

# Start deployments
cd aws_macro_deployment && docker compose up -d && cd ..
cd chronos_deploy_main && docker compose up -d && cd ..
cd portfolio_2 && docker compose up -d && cd ..
```

#### 5. Configure Security Group

```
Inbound Rules:
- SSH (22) - Your IP
- HTTP (80) - 0.0.0.0/0
- HTTPS (443) - 0.0.0.0/0
- Custom TCP (8000) - 0.0.0.0/0  # Macro API
- Custom TCP (9000) - 0.0.0.0/0  # Chronos API
- Custom TCP (8080) - 0.0.0.0/0  # Portfolio API
- Custom TCP (8090) - Your IP    # Kafka UI (restrict access)
- Custom TCP (9092) - VPC CIDR   # Kafka (internal only)
```

#### 6. Set Up Systemd Service (Auto-restart)

```bash
sudo nano /etc/systemd/system/trading-system-main.service
```

```ini
[Unit]
Description=Trading System Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ec2-user/all_deployments/ALL_DEPLOYMENTS
ExecStart=/usr/local/bin/docker compose -f docker compose.global.yml up -d
ExecStop=/usr/local/bin/docker compose -f docker compose.global.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable trading-system-main
sudo systemctl start trading-system-main
```

---

### Option B: AWS ECS Deployment (Production-Ready)

#### 1. Create ECR Repositories

```bash
# Create repositories for each service
aws ecr create-repository --repository-name trading/kafka
aws ecr create-repository --repository-name trading/finnhub-producer
aws ecr create-repository --repository-name trading/news-producer
aws ecr create-repository --repository-name trading/sentiment-producer
aws ecr create-repository --repository-name trading/macro-producer
aws ecr create-repository --repository-name trading/spike-detector
aws ecr create-repository --repository-name trading/macro-consumer
aws ecr create-repository --repository-name trading/chronos
aws ecr create-repository --repository-name trading/portfolio
```

#### 2. Build and Push Images

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build and push each producer
cd ALL_DEPLOYMENTS/shared_producers/common_finnhub_producer
docker build -t trading/finnhub-producer .
docker tag trading/finnhub-producer:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/trading/finnhub-producer:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/trading/finnhub-producer:latest

# Repeat for other services...
```

#### 3. Create ECS Task Definitions

Create `ecs-task-kafka.json`:
```json
{
  "family": "kafka-cluster",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [
    {
      "name": "zookeeper",
      "image": "confluentinc/cp-zookeeper:7.5.0",
      "essential": true,
      "environment": [
        {"name": "ZOOKEEPER_CLIENT_PORT", "value": "2181"}
      ],
      "portMappings": [
        {"containerPort": 2181, "protocol": "tcp"}
      ]
    },
    {
      "name": "kafka",
      "image": "confluentinc/cp-kafka:7.5.0",
      "essential": true,
      "dependsOn": [{"containerName": "zookeeper", "condition": "START"}],
      "environment": [
        {"name": "KAFKA_BROKER_ID", "value": "1"},
        {"name": "KAFKA_ZOOKEEPER_CONNECT", "value": "localhost:2181"},
        {"name": "KAFKA_ADVERTISED_LISTENERS", "value": "PLAINTEXT://kafka:9090"}
      ],
      "portMappings": [
        {"containerPort": 9092, "protocol": "tcp"}
      ]
    }
  ]
}
```

#### 4. Create ECS Services

```bash
# Create cluster
aws ecs create-cluster --cluster-name trading-cluster

# Register task definitions
aws ecs register-task-definition --cli-input-json file://ecs-task-kafka.json

# Create services
aws ecs create-service \
  --cluster trading-cluster \
  --service-name kafka-service \
  --task-definition kafka-cluster \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}"
```

---

### Option C: Amazon MSK (Managed Kafka)

For production, consider using Amazon MSK instead of self-managed Kafka:

#### 1. Create MSK Cluster

```bash
aws kafka create-cluster \
  --cluster-name trading-kafka \
  --broker-node-group-info file://broker-config.json \
  --kafka-version "3.5.1" \
  --number-of-broker-nodes 3
```

#### 2. Update Environment Variables

```bash
# Get MSK bootstrap servers
BOOTSTRAP_SERVERS=$(aws kafka get-bootstrap-brokers --cluster-arn YOUR_CLUSTER_ARN --query 'BootstrapBrokerString' --output text)

# Update .env
echo "KAFKA_BOOTSTRAP_SERVERS=$BOOTSTRAP_SERVERS" >> .env
```

---

## Monitoring & Maintenance

### CloudWatch Logs

```bash
# Create log group
aws logs create-log-group --log-group-name /trading-system-main/producers

# Configure Docker to send logs to CloudWatch
# Add to docker compose:
# logging:
#   driver: awslogs
#   options:
#     awslogs-group: /trading-system-main/producers
#     awslogs-region: us-east-1
```

### Health Checks

```bash
# Create health check script
cat > /home/ec2-user/health-check.sh << 'EOF'
#!/bin/bash
curl -sf http://localhost:8000/health || exit 1
curl -sf http://localhost:8090/ || exit 1
docker exec global-kafka kafka-broker-api-versions --bootstrap-server localhost:9090 || exit 1
echo "All services healthy"
EOF

chmod +x /home/ec2-user/health-check.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/ec2-user/health-check.sh >> /var/log/health-check.log 2>&1") | crontab -
```

### Backup Kafka Data

```bash
# Create backup script
cat > /home/ec2-user/backup-kafka.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d)
docker exec global-kafka kafka-topics --bootstrap-server localhost:9090 --list > /backup/topics-$DATE.txt
tar -czf /backup/kafka-data-$DATE.tar.gz /var/lib/docker/volumes/all_deployments_kafka_data
aws s3 cp /backup/kafka-data-$DATE.tar.gz s3://your-backup-bucket/kafka/
EOF
```

---

## Troubleshooting

### Common Issues

**1. Kafka not starting**
```bash
# Check Zookeeper first
docker logs global-zookeeper
# Ensure Zookeeper is healthy before Kafka starts
```

**2. Producers not connecting**
```bash
# Verify Kafka is accessible
docker exec common-finnhub-producer nc -zv kafka 9092
# Check producer logs
docker logs common-finnhub-producer
```

**3. Out of memory**
```bash
# Check Docker memory usage
docker stats
# Increase EC2 instance size or add swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**4. Topics not created**
```bash
# Manually create topics
docker exec global-kafka kafka-topics --bootstrap-server localhost:9090 \
  --create --topic stock_data --partitions 3 --replication-factor 1
```

---

## Cost Optimization Tips

1. **Use Spot Instances** for non-critical workers
2. **Right-size instances** based on actual usage
3. **Use Reserved Instances** for steady-state workloads
4. **Enable Auto-Scaling** for variable loads
5. **Use S3 for data archival** instead of keeping in Kafka forever

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `docker compose -f docker compose.global.yml up -d` | Start all global services |
| `docker compose -f docker compose.global.yml logs -f` | View all logs |
| `docker compose -f docker compose.global.yml down` | Stop all services |
| `docker compose -f docker compose.global.yml down -v` | Stop and remove volumes |
| `docker exec global-kafka kafka-topics --list --bootstrap-server localhost:9090` | List Kafka topics |
| `curl http://localhost:8090` | Check Kafka UI |
