#!/bin/bash
# Deploy updated Kafka configuration to remote server

set -e

echo "=================================================="
echo "Kafka External Access Deployment Script"
echo "=================================================="
echo ""

# Configuration
REMOTE_HOST="13.51.109.135"
REMOTE_USER="ubuntu"
PROJECT_DIR="~/pway-stock"

echo "📋 This script will:"
echo "  1. Copy updated docker-compose.yml to remote server"
echo "  2. Restart Kafka with new configuration"
echo "  3. Verify Kafka is accessible externally"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "Step 1: Copying docker-compose.yml to remote server..."
scp docker-compose.yml ${REMOTE_USER}@${REMOTE_HOST}:${PROJECT_DIR}/

echo ""
echo "Step 2: Restarting Kafka with new configuration..."
ssh ${REMOTE_USER}@${REMOTE_HOST} << 'EOF'
    cd ~/pway-stock
    
    echo "Stopping Kafka..."
    docker-compose stop kafka
    
    echo "Removing old Kafka container..."
    docker-compose rm -f kafka
    
    echo "Starting Kafka with new configuration..."
    docker-compose up -d kafka
    
    echo "Waiting for Kafka to start (30 seconds)..."
    sleep 30
    
    echo "Checking Kafka logs..."
    docker logs pway-kafka --tail 20
EOF

echo ""
echo "Step 3: Testing external connection..."
echo "Waiting 10 more seconds for Kafka to be fully ready..."
sleep 10

# Test from local machine
echo ""
echo "Testing connection from local machine..."
python3 backend/test_kafka_connection.py ${REMOTE_HOST}:9092

echo ""
echo "=================================================="
echo "✅ Deployment Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "  1. Update your local .env file:"
echo "     KAFKA_BOOTSTRAP_SERVERS=13.51.109.135:9092"
echo ""
echo "  2. Test local consumer:"
echo "     cd backend"
echo "     ./pway-stock/.venv/bin/python manage.py consume_kafka"
echo ""
echo "  3. (Optional) Restart all services on remote server:"
echo "     ssh ubuntu@13.51.109.135"
echo "     cd ~/pway-stock"
echo "     docker-compose restart"
echo ""
