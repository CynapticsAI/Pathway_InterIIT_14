#!/bin/bash
# =============================================================================
# KAFKA SERVER DEPLOYMENT SCRIPT
# =============================================================================
# Deploys: Kafka Cluster + All Shared Producers
# Run this on Server 1
# =============================================================================

set -e

echo "=========================================="
echo "  KAFKA SERVER DEPLOYMENT"
echo "=========================================="

cd ~/trading-system-main/ALL_DEPLOYMENTS

# Get server's internal IP for Kafka advertised listeners
INTERNAL_IP=$(hostname -I | awk '{print $1}')
echo "Internal IP: $INTERNAL_IP"

# Create docker-compose override for external access
cat > docker-compose.override.yml << EOF
services:
  kafka:
    environment:
      KAFKA_ADVERTISED_LISTENERS: INTERNAL://kafka:9090,EXTERNAL://${INTERNAL_IP}:29092
EOF

# Clean up any existing network with incorrect labels
echo "Cleaning up existing network if needed..."
docker network rm global_kafka_network 2>/dev/null || true

# Start Kafka cluster
echo "Starting Kafka cluster..."
docker compose -f docker-compose.global.yml up -d zookeeper

# Wait for Zookeeper
echo "Waiting for Zookeeper..."
sleep 15

docker compose -f docker-compose.global.yml up -d kafka

# Wait for Kafka
echo "Waiting for Kafka to be ready..."
RETRIES=30
until docker exec global-kafka kafka-broker-api-versions --bootstrap-server localhost:9090 > /dev/null 2>&1; do
    RETRIES=$((RETRIES-1))
    if [ $RETRIES -le 0 ]; then
        echo "ERROR: Kafka failed to start"
        docker compose -f docker-compose.global.yml logs kafka
        exit 1
    fi
    echo "  Waiting... ($RETRIES attempts remaining)"
    sleep 5
done

echo "✓ Kafka is ready"

# Start Kafka UI
echo "Starting Kafka UI..."
docker compose -f docker-compose.global.yml up -d kafka-ui

# Start all shared producers
echo "Starting shared producers..."
docker compose -f docker-compose.global.yml up -d \
    common-finnhub-producer \
    common-news-producer \
    common-sentiment-producer \
    common-macro-producer \
    common-spike-detector

# Wait for producers to start
sleep 10

# Show status
echo ""
echo "=========================================="
echo "  KAFKA SERVER READY"
echo "=========================================="
docker ps --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "Kafka Bootstrap Servers:"
echo "  Internal: kafka:9090"
echo "  External: ${INTERNAL_IP}:29092"
echo ""
echo "Kafka UI: http://${INTERNAL_IP}:8090"

# Create systemd service for auto-restart
sudo tee /etc/systemd/system/kafka-cluster.service > /dev/null << EOF
[Unit]
Description=Kafka Cluster
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/$USER/trading-system-main/ALL_DEPLOYMENTS
ExecStart=/usr/bin/docker compose -f docker-compose.global.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.global.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable kafka-cluster

echo "✓ Systemd service created for auto-restart"
