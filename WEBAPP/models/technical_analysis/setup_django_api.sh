#!/bin/bash
# Quick setup script for Django Trading API

echo "🚀 Django Trading API Setup"
echo "============================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

cd django_api

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Go back to root
cd ..

# Start infrastructure services
echo -e "\n${YELLOW}Starting infrastructure services (PostgreSQL, Redis, Kafka)...${NC}"
docker compose up -d zookeeper kafka db redis

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 10

# Build Django API
echo -e "\n${YELLOW}Building Django API...${NC}"
docker compose build django_api django_consumer

# Run migrations
echo -e "\n${YELLOW}Running database migrations...${NC}"
docker compose run --rm django_api python manage.py migrate

# Collect static files
echo -e "\n${YELLOW}Collecting static files...${NC}"
docker compose run --rm django_api python manage.py collectstatic --noinput

# Start Django services
echo -e "\n${YELLOW}Starting Django API and consumer...${NC}"
docker compose up -d django_api django_consumer

# Start Pathway services
echo -e "\n${YELLOW}Starting Pathway data processors...${NC}"
docker compose up -d finnhub_producer market_breadth spike_detector pnl sarimax news rrg_json

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n📊 Services:"
echo -e "  • Django API:        http://localhost:8000"
echo -e "  • API Docs:          http://localhost:8000/api/docs/"
echo -e "  • Admin Panel:       http://localhost:8000/admin/"
echo -e "  • Spike Dashboard:   http://localhost:8001"
echo -e "  • Market Breadth:    http://localhost:8002"
echo -e "  • SARIMAX:           http://localhost:8007"
echo -e "\n📝 Next steps:"
echo -e "  1. Create admin user: docker compose exec django_api python manage.py createsuperuser"
echo -e "  2. View logs:         docker compose logs -f django_api"
echo -e "  3. Check status:      docker compose ps"
echo -e "\n🛑 To stop all services: docker compose down"
