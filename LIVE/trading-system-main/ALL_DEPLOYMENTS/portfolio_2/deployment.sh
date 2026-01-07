#!/bin/bash
# deploy-to-ec2.sh

# Load environment variables from .env file
if [ -f .env ]; then
    source .env
else
    echo "Error: .env file not found!"
    exit 1
fi

echo "Deploying to EC2..."

# Create deployment directory on EC2
ssh -i "$KEY_FILE" "$EC2_HOST" "mkdir -p ~/portfolio-diversification"

# Copy files to EC2
echo "Copying files..."
scp -i "$KEY_FILE" -r \
  consumer \
  data \
  output \
  portfolio \
  docker-compose.yml \
  producer \
  scorer \
  Dockerfile.api \
  .env \
  requirements.txt \
  "$EC2_HOST":~/portfolio-diversification/

# SSH and deploy
ssh -i "$KEY_FILE" "$EC2_HOST" << 'ENDSSH'
cd ~/portfolio-diversification

echo "Setting up environment..."

# Create .env file if not exists
if [ ! -f .env ]; then
  echo "FRED_API_KEY=your_api_key_here" > .env
fi

# Create necessary directories
mkdir -p data models logs

# Start services
echo "Starting services..."
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d

echo "Waiting for services to start..."
sleep 45

echo "Checking service status..."
docker-compose ps

echo "Viewing logs..."
docker-compose logs --tail=50

echo "Deployment complete!"
echo ""
echo "API available at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):6541"
echo "API docs at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):6541/docs"

ENDSSH

echo "Deployment finished!"