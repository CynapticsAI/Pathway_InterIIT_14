#!/bin/bash
# Quick start script for Kafka consumer

echo "======================================================================"
echo "🚀 Kafka Consumer Quick Start"
echo "======================================================================"

# Check if we're in the backend directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: Please run this script from the backend directory"
    exit 1
fi

echo ""
echo "Step 1: Installing dependencies..."
pip install confluent-kafka python-decouple

echo ""
echo "Step 2: Running setup tests..."
python manage.py shell < kafka_consumer/tests.py

echo ""
echo "Step 3: Checking Kafka connection (optional)..."
echo "Note: This will fail if Kafka is not running. You can skip this."
echo ""

echo "======================================================================"
echo "✅ Setup complete!"
echo "======================================================================"
echo ""
echo "To start consuming messages:"
echo "  python manage.py consume_kafka"
echo ""
echo "To consume specific topics:"
echo "  python manage.py consume_kafka --topics market_breadth"
echo ""
echo "To see help:"
echo "  python manage.py consume_kafka --help"
echo ""
echo "======================================================================"
