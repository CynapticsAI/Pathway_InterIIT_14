#!/bin/bash
# deploy-ga-strat.sh

# Load environment variables
if [ -f .env ]; then
    source .env
else
    echo "Error: .env file not found!"
    exit 1
fi

echo "=================================================="
echo " Deploying GA Strategy FastAPI Service to EC2"
echo "=================================================="

# Create directory on EC2
ssh -i "$KEY_FILE" "$EC2_HOST" "mkdir -p ~/ga-strat-app"

echo "Copying project files to EC2..."
scp -i "$KEY_FILE" -r \
  api_server \
  chronos_consumer \
  finnhub_producer \
  news_producer \
  output \
  spike_detector \
  selection \
  sarimaxConsumer \
  docker-compose.yml \
  .env \
  "$EC2_HOST":~/ga-strat-app/

# SSH into EC2 and deploy
# Note: 'ENDSSH' in quotes prevents local variable expansion
ssh -i "$KEY_FILE" "$EC2_HOST" << 'ENDSSH'
cd ~/ga-strat-app

echo "--------------------------------------------------"
echo " Setting up deployment environment..."
echo "--------------------------------------------------"

# Ensure Docker is installed
if ! command -v docker &> /dev/null
then
    echo "Docker not found. Installing..."
    sudo apt-get update -y
    sudo apt-get install -y docker.io docker-compose-plugin
    sudo systemctl enable docker
    sudo systemctl start docker
fi

# Ensure docker-compose exists
if ! command -v docker-compose &> /dev/null
then
    echo "Installing docker-compose..."
    sudo apt-get install -y docker-compose
fi

echo "Creating required directories..."
mkdir -p logs data

echo "--------------------------------------------------"
echo " Building and launching Docker containers..."
echo "--------------------------------------------------"

docker-compose down -v
docker-compose build --no-cache
docker-compose up -d

echo "Waiting for FastAPI service to initialize..."
sleep 20

echo "--------------------------------------------------"
echo " Checking service status..."
echo "--------------------------------------------------"
docker-compose ps

echo "--------------------------------------------------"
echo " Last 50 log lines..."
echo "--------------------------------------------------"
docker-compose logs --tail=50

echo "--------------------------------------------------"
echo " Deployment Successful!"
echo "--------------------------------------------------"

PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
echo "API available at: http://$PUBLIC_IP:8000"
echo "Docs:            http://$PUBLIC_IP:8000/docs"
ENDSSH

echo "=================================================="
echo " Deployment finished!"
echo "=================================================="