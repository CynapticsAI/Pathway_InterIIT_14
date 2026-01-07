#!/bin/bash
# Quick Django-only setup (no Pathway services)

echo "🚀 Django API Quick Start (Lightweight)"
echo "========================================="

cd django_api

# Check if .env exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env file"
fi

cd ..

# Start only infrastructure + Django
echo -e "\nStarting infrastructure services..."
docker compose up -d zookeeper kafka db redis

echo -e "\nWaiting for services..."
sleep 10

echo -e "\nBuilding Django API..."
docker compose build django_api django_consumer

echo -e "\nRunning migrations..."
docker compose run --rm django_api python manage.py migrate

echo -e "\nCollecting static files..."
docker compose run --rm django_api python manage.py collectstatic --noinput

echo -e "\nStarting Django services..."
docker compose up -d django_api django_consumer

echo -e "\n✅ Django API is ready!"
echo "📊 Django API:   http://localhost:8000"
echo "📚 API Docs:     http://localhost:8000/api/docs/"
echo "👤 Admin:        http://localhost:8000/admin/"
echo ""
echo "💡 To start Pathway services later:"
echo "   docker compose up -d finnhub_producer market_breadth spike_detector pnl sarimax news rrg_json"
echo ""
echo "🛑 To stop: docker compose down"
