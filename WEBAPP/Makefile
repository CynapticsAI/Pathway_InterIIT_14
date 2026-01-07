.PHONY: help build start stop restart logs status clean shell-backend shell-frontend test health setup-kafka-topics

# Default target
help:
	@echo "pway-stock Docker Management"
	@echo ""
	@echo "Available targets:"
	@echo "  make build         - Build all Docker images"
	@echo "  make start         - Start all services"
	@echo "  make stop          - Stop all services"
	@echo "  make restart       - Restart all services"
	@echo "  make logs          - Show logs (all services)"
	@echo "  make status        - Show status of all services"
	@echo "  make clean         - Stop and remove all containers, networks, and volumes"
	@echo "  make shell-backend - Open shell in backend container"
	@echo "  make shell-frontend- Open shell in frontend container"
	@echo "  make test          - Run backend tests"
	@echo "  make health        - Run health check"
	@echo "  make migrate       - Run Django migrations"
	@echo "  make superuser     - Create Django superuser"
	@echo "  make frontend-only - Start only frontend and backend"
	@echo "  make models-only   - Start only analysis models"
	@echo "  make setup-kafka-topics - Setup Kafka topics automatically"

# Build all images
build:
	docker-compose build

# Start all services
start:
	docker-compose up -d
	@echo "Services started. Access:"
	@echo "  Frontend:  http://localhost:3000"
	@echo "  Backend:   http://localhost:8000"
	@echo "  API Docs:  http://localhost:8000/api/schema/swagger-ui/"

# Stop all services
stop:
	docker-compose stop

# Restart all services
restart:
	docker-compose restart

# Show logs
logs:
	docker-compose logs -f

# Show status
status:
	docker-compose ps

# Clean up everything
clean:
	@echo "Warning: This will remove all containers, networks, and volumes!"
	@read -p "Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		echo "Cleanup complete"; \
	fi

# Open shell in backend
shell-backend:
	docker-compose exec backend bash

# Open shell in frontend
shell-frontend:
	docker-compose exec frontend sh

# Run backend tests
test:
	docker-compose exec backend python manage.py test

# Run health check
health:
	./health-check.sh

# Run Django migrations
migrate:
	docker-compose exec backend python manage.py migrate

# Create superuser
superuser:
	docker-compose exec backend python manage.py createsuperuser

# Start only frontend and backend
frontend-only:
	docker-compose up -d frontend backend

# Start only analysis models
models-only:
	docker-compose up -d kafka zookeeper finnhub_producer news_producer market_breadth spike_detector pnl sarimax rrg_json

# Rebuild and start
rebuild:
	docker-compose up -d --build

# View logs for specific service
logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

logs-kafka:
	docker-compose logs -f kafka

# Setup Kafka topics
setup-kafka-topics:
	@echo "Setting up Kafka topics..."
	cd backend && python manage.py setup_kafka_topics
