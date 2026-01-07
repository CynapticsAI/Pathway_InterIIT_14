#!/bin/bash
# =============================================================================
# Start All Services Script
# =============================================================================
# Starts global infrastructure AND all deployments
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$ROOT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Trading System - Full Startup${NC}"
echo -e "${BLUE}========================================${NC}"

# Start global infrastructure first
echo -e "\n${BLUE}[1/4] Starting global infrastructure...${NC}"
./scripts/start-local.sh

# Start AWS Macro Deployment
echo -e "\n${BLUE}[2/4] Starting AWS Macro Deployment...${NC}"
cd aws_macro_deployment && docker compose up -d && cd ..
echo -e "${GREEN}✓ AWS Macro started${NC}"

# Start Chronos Deployment
echo -e "\n${BLUE}[3/4] Starting Chronos Deployment...${NC}"
cd chronos_deploy_main && docker compose up -d && cd ..
echo -e "${GREEN}✓ Chronos started${NC}"

# Start Portfolio Deployment
echo -e "\n${BLUE}[4/4] Starting Portfolio Deployment...${NC}"
cd portfolio_2 && docker compose up -d && cd ..
echo -e "${GREEN}✓ Portfolio started${NC}"

# Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✓ All services started!${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "\n${BLUE}Service URLs:${NC}"
echo -e "  Kafka UI:       ${GREEN}http://localhost:8090${NC}"
echo -e "  AWS Macro API:  ${GREEN}http://localhost:8000${NC}"
echo -e "  Chronos API:    ${GREEN}http://localhost:9000${NC}"
echo -e "  Portfolio API:  ${GREEN}http://localhost:8080${NC}"

echo -e "\n${BLUE}Running containers:${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
