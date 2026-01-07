#!/bin/bash

# Kafka Topic Setup Script
# Creates all required Kafka topics automatically

set -e  # Exit on error

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🔧 Kafka Topic Setup"
echo "════════════════════════════════════════════════════════════════════════════════"

# Check if Kafka is running
echo "📡 Checking Kafka connection..."
if ! nc -z localhost 9092 2>/dev/null; then
    echo "❌ Error: Kafka is not running on localhost:9092"
    echo "Please start Kafka first:"
    echo "  cd /path/to/kafka"
    echo "  bin/zookeeper-server-start.sh config/zookeeper.properties &"
    echo "  bin/kafka-server-start.sh config/server.properties &"
    exit 1
fi

echo "✅ Kafka is running"
echo ""

# Navigate to backend directory
cd "$(dirname "$0")/backend"

# Activate virtual environment if it exists
if [ -d "../.venv" ]; then
    echo "🐍 Activating virtual environment..."
    source ../.venv/bin/activate
elif [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
fi

# Run the Django management command
echo "🚀 Creating Kafka topics..."
echo ""

python manage.py setup_kafka_topics

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ Kafka topics setup complete!"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "You can now run the Kafka consumer:"
echo "  python manage.py consume_kafka"
echo ""
