#!/bin/bash
# =============================================================================
# Test All Services Script
# =============================================================================
# Run this after start-all.sh to verify everything is working
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Trading System - Service Tests${NC}"
echo -e "${BLUE}========================================${NC}"

PASS=0
FAIL=0

test_endpoint() {
    local name=$1
    local url=$2
    local expected=$3
    
    echo -e "\n${BLUE}Testing: $name${NC}"
    echo -e "  URL: $url"
    
    response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "$expected" ] || [ "$response" = "200" ]; then
        echo -e "  Status: ${GREEN}✓ PASS${NC} (HTTP $response)"
        PASS=$((PASS+1))
        return 0
    else
        echo -e "  Status: ${RED}✗ FAIL${NC} (HTTP $response, expected $expected)"
        FAIL=$((FAIL+1))
        return 1
    fi
}

test_endpoint_json() {
    local name=$1
    local url=$2
    
    echo -e "\n${BLUE}Testing: $name${NC}"
    echo -e "  URL: $url"
    
    response=$(curl -s --max-time 10 "$url" 2>/dev/null)
    http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" 2>/dev/null || echo "000")
    
    if [ "$http_code" = "200" ]; then
        echo -e "  Status: ${GREEN}✓ PASS${NC} (HTTP $http_code)"
        echo -e "  Response: ${YELLOW}$(echo $response | head -c 200)${NC}"
        PASS=$((PASS+1))
        return 0
    else
        echo -e "  Status: ${RED}✗ FAIL${NC} (HTTP $http_code)"
        FAIL=$((FAIL+1))
        return 1
    fi
}

# =============================================================================
# KAFKA CLUSTER TESTS
# =============================================================================
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}KAFKA CLUSTER${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

test_endpoint "Kafka UI" "http://localhost:8090" "200"

echo -e "\n${BLUE}Testing: Kafka Broker${NC}"
if docker exec global-kafka kafka-broker-api-versions --bootstrap-server localhost:9090 > /dev/null 2>&1; then
    echo -e "  Status: ${GREEN}✓ PASS${NC} (Broker responding)"
    PASS=$((PASS+1))
else
    echo -e "  Status: ${RED}✗ FAIL${NC} (Broker not responding)"
    FAIL=$((FAIL+1))
fi

echo -e "\n${BLUE}Testing: Kafka Topics${NC}"
topics=$(docker exec global-kafka kafka-topics --bootstrap-server localhost:9090 --list 2>/dev/null)
if [ -n "$topics" ]; then
    echo -e "  Status: ${GREEN}✓ PASS${NC}"
    echo -e "  Topics: ${YELLOW}$(echo $topics | tr '\n' ' ')${NC}"
    PASS=$((PASS+1))
else
    echo -e "  Status: ${YELLOW}⚠ WARNING${NC} (No topics yet - may need more time)"
fi

# =============================================================================
# SHARED PRODUCERS TESTS
# =============================================================================
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}SHARED PRODUCERS${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

for producer in common-finnhub-producer common-news-producer common-sentiment-producer common-macro-producer common-spike-detector; do
    echo -e "\n${BLUE}Testing: $producer${NC}"
    status=$(docker inspect -f '{{.State.Status}}' $producer 2>/dev/null || echo "not found")
    if [ "$status" = "running" ]; then
        echo -e "  Status: ${GREEN}✓ RUNNING${NC}"
        PASS=$((PASS+1))
    else
        echo -e "  Status: ${RED}✗ $status${NC}"
        FAIL=$((FAIL+1))
    fi
done

# =============================================================================
# AWS MACRO DEPLOYMENT TESTS
# =============================================================================
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}AWS MACRO DEPLOYMENT (Port 8000)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

test_endpoint "Macro API Root" "http://localhost:8000/" "200"
test_endpoint_json "Macro API - Energy Prediction" "http://localhost:8000/predict/Energy"
test_endpoint_json "Macro API - Technology Prediction" "http://localhost:8000/predict/Information_Technology"
test_endpoint_json "Macro API - Financials Prediction" "http://localhost:8000/predict/Financials"

# =============================================================================
# CHRONOS DEPLOYMENT TESTS
# =============================================================================
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}CHRONOS DEPLOYMENT (Port 9000)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

test_endpoint "Chronos API Root" "http://localhost:9000/" "200"
test_endpoint_json "Chronos API - Status" "http://localhost:9000/status"

# =============================================================================
# PORTFOLIO DEPLOYMENT TESTS
# =============================================================================
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}PORTFOLIO DEPLOYMENT (Port 8080)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

test_endpoint "Portfolio API Root" "http://localhost:8080/" "200"
test_endpoint_json "Portfolio API - Health" "http://localhost:8080/health"

# =============================================================================
# KAFKA TOPIC MESSAGE TESTS
# =============================================================================
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}KAFKA TOPIC MESSAGES${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

for topic in stock_data news_data sentiment_scores; do
    echo -e "\n${BLUE}Testing: $topic topic${NC}"
    count=$(docker exec global-kafka kafka-run-class kafka.tools.GetOffsetShell \
        --broker-list localhost:9090 \
        --topic $topic 2>/dev/null | awk -F: '{sum += $3} END {print sum}' || echo "0")
    if [ "$count" -gt "0" ] 2>/dev/null; then
        echo -e "  Status: ${GREEN}✓ PASS${NC} ($count messages)"
        PASS=$((PASS+1))
    else
        echo -e "  Status: ${YELLOW}⚠ No messages yet${NC} (may need more time)"
    fi
done

# =============================================================================
# SUMMARY
# =============================================================================
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}TEST SUMMARY${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "  ${GREEN}Passed: $PASS${NC}"
echo -e "  ${RED}Failed: $FAIL${NC}"

if [ $FAIL -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "\n${YELLOW}Some tests failed. Check the services above.${NC}"
    exit 1
fi
