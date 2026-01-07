#!/bin/bash
# =============================================================================
# Local Development Shutdown Script
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$ROOT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Trading System - Shutdown${NC}"
echo -e "${BLUE}========================================${NC}"

# Stop individual deployments
echo -e "\n${BLUE}Stopping individual deployments...${NC}"
for dir in aws_macro_deployment chronos_deploy_main portfolio_2; do
    if [ -f "$dir/docker-compose.yml" ] || [ -f "$dir/docker-compose.yaml" ]; then
        echo -e "  Stopping $dir..."
        (cd "$dir" && docker compose down 2>/dev/null) || true
    fi
done

# Stop global services
echo -e "\n${BLUE}Stopping global services...${NC}"
docker compose -f docker-compose.global.yml down

echo -e "\n${GREEN}✓ All services stopped${NC}"

# Ask about volumes
echo -e "\n${BLUE}Do you want to remove data volumes? (y/N)${NC}"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    docker compose -f docker-compose.global.yml down -v
    echo -e "${GREEN}✓ Volumes removed${NC}"
fi
