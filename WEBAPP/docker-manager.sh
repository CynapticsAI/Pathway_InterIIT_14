#!/bin/bash

# pway-stock Docker Management Script
# This script helps manage the Docker Compose setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_info "Docker is running"
}

# Function to check if docker-compose is installed
check_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose is not installed. Please install it and try again."
        exit 1
    fi
    print_info "docker-compose is installed"
}

# Function to show usage
show_usage() {
    cat << EOF
pway-stock Docker Management Script

Usage: ./docker-manager.sh [COMMAND]

Commands:
    start           Start all services
    stop            Stop all services
    restart         Restart all services
    build           Build all images
    rebuild         Rebuild and restart all services
    logs            Show logs for all services
    status          Show status of all services
    clean           Stop and remove all containers, networks, and volumes
    
    frontend        Start only frontend and backend
    backend         Start only backend and dependencies
    models          Start only technical analysis models
    
    shell-backend   Open shell in backend container
    shell-frontend  Open shell in frontend container
    
    django [cmd]    Run Django management command (e.g., ./docker-manager.sh django migrate)
    
    help            Show this help message

Examples:
    ./docker-manager.sh start
    ./docker-manager.sh logs
    ./docker-manager.sh django createsuperuser
    ./docker-manager.sh rebuild

EOF
}

# Main script logic
case "$1" in
    start)
        check_docker
        check_compose
        print_info "Starting all services..."
        docker-compose up -d
        print_info "All services started. Access frontend at http://localhost:3000"
        print_info "Backend API available at http://localhost:8000"
        ;;
    
    stop)
        print_info "Stopping all services..."
        docker-compose stop
        print_info "All services stopped"
        ;;
    
    restart)
        print_info "Restarting all services..."
        docker-compose restart
        print_info "All services restarted"
        ;;
    
    build)
        check_docker
        check_compose
        print_info "Building all images..."
        docker-compose build
        print_info "Build complete"
        ;;
    
    rebuild)
        check_docker
        check_compose
        print_info "Rebuilding and restarting all services..."
        docker-compose up -d --build
        print_info "Rebuild and restart complete"
        ;;
    
    logs)
        docker-compose logs -f
        ;;
    
    status)
        docker-compose ps
        ;;
    
    clean)
        print_warning "This will remove all containers, networks, and volumes!"
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Cleaning up..."
            docker-compose down -v
            print_info "Cleanup complete"
        else
            print_info "Cleanup cancelled"
        fi
        ;;
    
    frontend)
        check_docker
        check_compose
        print_info "Starting frontend and backend..."
        docker-compose up -d frontend backend
        print_info "Frontend available at http://localhost:3000"
        ;;
    
    backend)
        check_docker
        check_compose
        print_info "Starting backend and dependencies..."
        docker-compose up -d backend kafka zookeeper
        print_info "Backend available at http://localhost:8000"
        ;;
    
    models)
        check_docker
        check_compose
        print_info "Starting technical analysis models..."
        docker-compose up -d kafka zookeeper finnhub_producer news_producer market_breadth spike_detector pnl sarimax rrg_json
        print_info "Models started"
        ;;
    
    shell-backend)
        docker-compose exec backend bash
        ;;
    
    shell-frontend)
        docker-compose exec frontend sh
        ;;
    
    django)
        shift
        if [ -z "$1" ]; then
            print_error "Please provide a Django command"
            exit 1
        fi
        docker-compose exec backend python manage.py "$@"
        ;;
    
    help|--help|-h|"")
        show_usage
        ;;
    
    *)
        print_error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac
