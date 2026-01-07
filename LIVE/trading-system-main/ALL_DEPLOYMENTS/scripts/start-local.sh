#!/bin/bash
# =============================================================================
# Local Development Startup Script
# =============================================================================
# This script starts all services in the correct order for local development.
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$ROOT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Trading System - Local Startup${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}No .env file found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${RED}Please edit .env with your API keys before continuing.${NC}"
    echo -e "${RED}Run: nano .env${NC}"
    exit 1
fi

# Check for required API keys
source .env
if [ -z "$FINNHUB_API_KEY" ] || [ "$FINNHUB_API_KEY" = "your_finnhub_api_key_here" ]; then
    echo -e "${RED}ERROR: FINNHUB_API_KEY not set in .env${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Environment configured${NC}"

# Start global infrastructure
echo -e "\n${BLUE}Starting Kafka cluster and shared producers...${NC}"
docker compose -f docker-compose.global.yml up -d

# Wait for Kafka to be healthy
echo -e "\n${YELLOW}Waiting for Kafka to be ready...${NC}"
RETRIES=30
until docker exec global-kafka kafka-broker-api-versions --bootstrap-server localhost:9090 > /dev/null 2>&1; do
    RETRIES=$((RETRIES-1))
    if [ $RETRIES -le 0 ]; then
        echo -e "${RED}ERROR: Kafka failed to start${NC}"
        docker compose -f docker-compose.global.yml logs kafka
        exit 1
    fi
    echo -e "  Waiting... ($RETRIES attempts remaining)"
    sleep 5
done
echo -e "${GREEN}✓ Kafka is ready${NC}"

# Wait a bit more for producers to connect
sleep 5

# Show status
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Global services started successfully!${NC}"
echo -e "${BLUE}========================================${NC}"

# Show running containers
echo -e "\n${BLUE}Running containers:${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "global|common|kafka"

echo -e "\n${BLUE}Access points:${NC}"
echo -e "  Kafka UI:     ${GREEN}http://localhost:8090${NC}"
echo -e "  Kafka:        ${GREEN}localhost:29092${NC} (external) / ${GREEN}kafka:9090${NC} (internal)"

echo -e "\n${BLUE}To start individual deployments:${NC}"
echo -e "  cd aws_macro_deployment && docker compose up -d"
echo -e "  cd chronos_deploy_main && docker compose up -d"
echo -e "  cd portfolio_2 && docker compose up -d"
echo -e "  cd harshu_strat && docker compose up -d"

echo -e "\n${BLUE}To view logs:${NC}"
echo -e "  docker compose -f docker-compose.global.yml logs -f"

echo -e "\n${BLUE}To stop all services:${NC}"
echo -e "  ./scripts/stop-local.sh"
