#!/bin/bash
# deploy-to-ec2.sh

# Configuration
EC2_HOST="ubuntu@ec2-13-51-44-213.eu-north-1.compute.amazonaws.com"
KEY_FILE="New.pem"
FRED_API_KEY="8d64acabb5cbe5d170fb1ecfb73f9257"

echo "🚀 Deploying to EC2..."

# Create deployment directory on EC2
ssh -i $KEY_FILE $EC2_HOST "mkdir -p ~/stock-prediction"

# Copy files to EC2
echo "📦 Copying files..."
scp -i $KEY_FILE -r \
  pathway_fred_producer.py \
  pathway_consumer_training.py \
  api_server.py \
  requirements.txt \
  docker-compose.yaml \
  Dockerfile.producer \
  Dockerfile.consumer \
  Dockerfile.api \
  .env \
  $EC2_HOST:~/stock-prediction/

# SSH and deploy
ssh -i $KEY_FILE $EC2_HOST << 'ENDSSH'
cd ~/stock-prediction

echo "🔧 Setting up environment..."

# Create .env file if not exists
if [ ! -f .env ]; then
  echo "FRED_API_KEY=your_api_key_here" > .env
fi

# Create necessary directories
mkdir -p data models logs

# Start services
echo "🚀 Starting services..."
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d

echo "⏳ Waiting for services to start..."
sleep 45

echo "📊 Checking service status..."
docker-compose ps

echo "📋 Viewing logs..."
docker-compose logs --tail=50

echo "✅ Deployment complete!"
echo ""
echo "🌐 API available at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000"
echo "📚 API docs at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000/docs"

ENDSSH

echo "✅ Deployment finished!"