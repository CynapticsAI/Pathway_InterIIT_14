#!/bin/bash

# Health Check Script for pway-stock Docker Services
# This script checks if all services are running and accessible

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  pway-stock Health Check${NC}"
echo -e "${BLUE}======================================${NC}\n"

# Function to check if a service is running
check_service() {
    local service=$1
    local status=$(docker-compose ps -q $service 2>/dev/null)
    
    if [ -n "$status" ]; then
        local running=$(docker inspect -f '{{.State.Running}}' $(docker-compose ps -q $service) 2>/dev/null)
        if [ "$running" = "true" ]; then
            echo -e "${GREEN}✓${NC} $service is running"
            return 0
        else
            echo -e "${RED}✗${NC} $service is not running"
            return 1
        fi
    else
        echo -e "${YELLOW}○${NC} $service is not started"
        return 2
    fi
}

# Function to check HTTP endpoint
check_endpoint() {
    local name=$1
    local url=$2
    local response=$(curl -s -o /dev/null -w "%{http_code}" $url 2>/dev/null)
    
    if [ "$response" = "200" ] || [ "$response" = "301" ] || [ "$response" = "302" ]; then
        echo -e "${GREEN}✓${NC} $name is accessible ($url)"
        return 0
    else
        echo -e "${RED}✗${NC} $name is not accessible ($url) - HTTP $response"
        return 1
    fi
}

# Check Docker
echo -e "${BLUE}[Docker Status]${NC}"
if docker info > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Docker is running"
else
    echo -e "${RED}✗${NC} Docker is not running"
    exit 1
fi
echo ""

# Check Core Services
echo -e "${BLUE}[Core Services]${NC}"
check_service "frontend"
check_service "backend"
echo ""

# Check Infrastructure
echo -e "${BLUE}[Infrastructure]${NC}"
check_service "kafka"
check_service "zookeeper"
echo ""

# Check Analysis Services
echo -e "${BLUE}[Analysis Services]${NC}"
check_service "finnhub_producer"
check_service "news_producer"
check_service "market_breadth"
check_service "spike_detector"
check_service "pnl"
check_service "sarimax"
check_service "rrg_json"
echo ""

# Check HTTP Endpoints
echo -e "${BLUE}[HTTP Endpoints]${NC}"
sleep 2  # Give services time to fully start
check_endpoint "Frontend" "http://localhost:3000"
check_endpoint "Backend API" "http://localhost:8000"
check_endpoint "Market Breadth" "http://localhost:8002"
check_endpoint "Spike Detector" "http://localhost:8001"
check_endpoint "SARIMAX" "http://localhost:8007"
echo ""

# Container Resource Usage
echo -e "${BLUE}[Resource Usage]${NC}"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" $(docker-compose ps -q) 2>/dev/null | head -n 10
echo ""

# Summary
echo -e "${BLUE}======================================${NC}"
echo -e "${GREEN}Health check complete!${NC}"
echo ""
echo "Quick commands:"
echo "  View logs:    ./docker-manager.sh logs"
echo "  Restart all:  ./docker-manager.sh restart"
echo "  Stop all:     ./docker-manager.sh stop"
echo -e "${BLUE}======================================${NC}"
