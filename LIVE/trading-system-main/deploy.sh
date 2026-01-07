#!/bin/bash
# =============================================================================
# PORTFOLIO SERVER DEPLOYMENT SCRIPT
# =============================================================================
# Deploys: Portfolio Deployment (Consumers + API + PostgreSQL)
# Run this on Server 4
# Requires: KAFKA_SERVER, MACRO_SERVER environment variables
# =============================================================================

set -e

echo "=========================================="
echo "  PORTFOLIO SERVER DEPLOYMENT"
echo "=========================================="

KAFKA_SERVER="${KAFKA_SERVER:-kafka}"
MACRO_SERVER="${MACRO_SERVER:-localhost}"

echo "Kafka Server: $KAFKA_SERVER"
echo "Macro Server: $MACRO_SERVER"

cd ~/trading-system-main/ALL_DEPLOYMENTS/portfolio_2

# Create updated docker-compose to connect to remote Kafka
cat > docker-compose.yml << EOF
networks:
  portfolio-network:
    driver: bridge

volumes:
  pgdata:

services:
  postgres:
    image: postgres:15
    container_name: portfolio-postgres
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: portfolio_db
    networks:
      - portfolio-network
    ports:
      - "5433:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 10s
      retries: 10
    restart: unless-stopped

  scorer:
    build:
      context: ./scorer
    container_name: portfolio-scorer
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=${KAFKA_SERVER}:9090
    extra_hosts:
      - "kafka:${KAFKA_SERVER}"
    volumes:
      - ./output:/app/output
      - ./data:/app/data
    networks:
      - portfolio-network
    restart: unless-stopped

  consumer:
    build:
      context: ./consumer
    container_name: portfolio-consumer
    depends_on:
      - scorer
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=${KAFKA_SERVER}:9090
    extra_hosts:
      - "kafka:${KAFKA_SERVER}"
    volumes:
      - ./output:/app/output
      - ./data:/app/data
    networks:
      - portfolio-network
    restart: unless-stopped

  portfolio:
    build:
      context: ./portfolio
    container_name: portfolio-main
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      POSTGRES_HOST: portfolio-postgres
      POSTGRES_DB: portfolio_db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      KAFKA_BOOTSTRAP_SERVERS: ${KAFKA_SERVER}:9090
      MACRO_API_URL: http://${MACRO_SERVER}:8000
    extra_hosts:
      - "kafka:${KAFKA_SERVER}"
    volumes:
      - ./output:/app/output
      - ./data:/app/data
    networks:
      - portfolio-network
    restart: unless-stopped

  portfolio-api:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: portfolio-api
    depends_on:
      - portfolio
    ports:
      - "8080:8080"
    volumes:
      - ./output:/app/output
      - ./data:/app/data
    environment:
      - POSTGRES_HOST=portfolio-postgres
      - POSTGRES_DB=portfolio_db
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    networks:
      - portfolio-network
    restart: unless-stopped
EOF

# Build and start
echo "Building and starting services..."
docker compose up -d --build

# Wait for services
sleep 20

# Show status
echo ""
echo "=========================================="
echo "  PORTFOLIO SERVER READY"
echo "=========================================="
docker ps --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "API URL: http://$(hostname -I | awk '{print $1}'):8080"
echo "PostgreSQL: localhost:5433"
echo ""
echo "Test: curl http://localhost:8080/"

# Create systemd service
sudo tee /etc/systemd/system/portfolio-api.service > /dev/null << EOF
[Unit]
Description=Portfolio API
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/$USER/trading-system-main/ALL_DEPLOYMENTS/portfolio_2
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable portfolio-api

echo "✓ Deployment complete"
