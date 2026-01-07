#!/bin/bash
# =============================================================================
# MACRO SERVER DEPLOYMENT SCRIPT
# =============================================================================
# Deploys: AWS Macro Deployment (Consumer + API)
# Run this on Server 2
# Requires: KAFKA_SERVER environment variable
# =============================================================================

set -e

echo "=========================================="
echo "  MACRO SERVER DEPLOYMENT"
echo "=========================================="

KAFKA_SERVER="${KAFKA_SERVER:-kafka}"

echo "Kafka Server: $KAFKA_SERVER"

cd ~/trading-system-main/ALL_DEPLOYMENTS/aws_macro_deployment

# Remove the health check that depends on local Kafka
cat > docker-compose.yml << EOF
networks:
  macro-network:
    driver: bridge

services:
  consumer:
    build:
      context: .
      dockerfile: Dockerfile.consumer
    container_name: macro-model-trainer
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=${KAFKA_SERVER}:9090
    extra_hosts:
      - "kafka:${KAFKA_SERVER}"
    volumes:
      - ./models:/app/models
      - ./data:/app/data
    networks:
      - macro-network
    restart: unless-stopped

  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: macro-prediction-api
    depends_on:
      - consumer
    ports:
      - "8000:8000"
    environment:
      - FRED_API_KEY=\${FRED_API_KEY}
    volumes:
      - ./models:/app/models
      - ./data:/app/data
    networks:
      - macro-network
    restart: unless-stopped
EOF

# Build and start
echo "Building and starting services..."
docker compose up -d --build

# Wait for services
sleep 10

# Show status
echo ""
echo "=========================================="
echo "  MACRO SERVER READY"
echo "=========================================="
docker ps --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "API URL: http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "Test: curl http://localhost:8000/predict/Energy"

# Create systemd service
sudo tee /etc/systemd/system/macro-api.service > /dev/null << EOF
[Unit]
Description=Macro API
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/$USER/trading-system-main/ALL_DEPLOYMENTS/aws_macro_deployment
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable macro-api

echo "✓ Deployment complete"
