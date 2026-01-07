#!/bin/bash
# =============================================================================
# CHRONOS SERVER DEPLOYMENT SCRIPT
# =============================================================================
# Deploys: Chronos Deployment (Consumers + API)
# Run this on Server 3
# Requires: KAFKA_SERVER environment variable
# =============================================================================

set -e

echo "=========================================="
echo "  CHRONOS SERVER DEPLOYMENT"
echo "=========================================="

KAFKA_SERVER="${KAFKA_SERVER:-kafka}"

echo "Kafka Server: $KAFKA_SERVER"

cd ~/trading-system-main/ALL_DEPLOYMENTS/chronos_deploy_main

# Create updated docker-compose to connect to remote Kafka
cat > docker-compose.yml << EOF
networks:
  chronos-network:
    driver: bridge

services:
  sarimax:
    build:
      context: ./sarimaxConsumer
    container_name: chronos-sarimax
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=${KAFKA_SERVER}:9090
    extra_hosts:
      - "kafka:${KAFKA_SERVER}"
    volumes:
      - ./sarimaxConsumer:/app/output
    networks:
      - chronos-network
    restart: unless-stopped

  chronos_consumer:
    build:
      context: ./chronos_consumer
    container_name: chronos-consumer
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=${KAFKA_SERVER}:9090
    extra_hosts:
      - "kafka:${KAFKA_SERVER}"
    volumes:
      - ./output:/app/chronos_output
      - ./chronos_consumer/heartbeat:/app/heartbeat
      - ./chronos_consumer/chronos2_stream_ckpts_latest:/app/chronos2_stream_ckpts_latest
    networks:
      - chronos-network
    restart: unless-stopped

  select_model:
    build:
      context: ./selection
    container_name: chronos-select-model
    depends_on:
      - sarimax
      - chronos_consumer
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=${KAFKA_SERVER}:9090
    extra_hosts:
      - "kafka:${KAFKA_SERVER}"
    volumes:
      - ./selection/s_output:/app/s_output
    networks:
      - chronos-network
    restart: unless-stopped

  api_server:
    build:
      context: ./api_server
    container_name: chronos-api
    ports:
      - "9000:8000"
    volumes:
      - ./spike_detector:/app/spike_detector
      - ./sarimaxConsumer:/app/sarimaxConsumer
      - ./selection:/app/selection
    depends_on:
      - select_model
    networks:
      - chronos-network
    restart: unless-stopped
EOF

# Build and start
echo "Building and starting services..."
docker compose up -d --build

# Wait for services
sleep 15

# Show status
echo ""
echo "=========================================="
echo "  CHRONOS SERVER READY"
echo "=========================================="
docker ps --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "API URL: http://$(hostname -I | awk '{print $1}'):9000"
echo ""
echo "Test: curl http://localhost:9000/"

# Create systemd service
sudo tee /etc/systemd/system/chronos-api.service > /dev/null << EOF
[Unit]
Description=Chronos API
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/$USER/trading-system-main/ALL_DEPLOYMENTS/chronos_deploy_main
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable chronos-api

echo "✓ Deployment complete"
