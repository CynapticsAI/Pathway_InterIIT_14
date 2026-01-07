#!/bin/bash
# Quick setup script for Chat Backend

set -e  # Exit on error

echo "🚀 Chat Backend Setup Script"
echo "=============================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if in backend directory
if [ ! -f "manage.py" ]; then
    echo -e "${RED}❌ Error: Please run this script from the backend directory${NC}"
    exit 1
fi

echo -e "${YELLOW}📦 Step 1: Installing Python dependencies...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

echo -e "${YELLOW}🗄️  Step 2: Running database migrations...${NC}"
python manage.py makemigrations
python manage.py migrate
echo -e "${GREEN}✅ Migrations complete${NC}"
echo ""

echo -e "${YELLOW}🔍 Step 3: Checking Redis connection...${NC}"
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✅ Redis is running${NC}"
    else
        echo -e "${RED}❌ Redis not responding. Please start Redis:${NC}"
        echo "   docker run -d -p 6379:6379 redis:alpine"
        echo "   or: brew install redis && brew services start redis"
    fi
else
    echo -e "${YELLOW}⚠️  Redis CLI not found. Make sure Redis is running on port 6379${NC}"
fi
echo ""

echo -e "${YELLOW}📡 Step 4: Checking Kafka connection...${NC}"
# Try to check if Kafka is accessible
if command -v nc &> /dev/null; then
    if nc -z localhost 9092 2>/dev/null; then
        echo -e "${GREEN}✅ Kafka is accessible on localhost:9092${NC}"
    else
        echo -e "${YELLOW}⚠️  Kafka not accessible on localhost:9092${NC}"
        echo "   Make sure Kafka is running or update KAFKA_CONFIG in settings.py"
    fi
else
    echo -e "${YELLOW}⚠️  Cannot check Kafka (nc not installed)${NC}"
fi
echo ""

echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "=============================="
echo "🚀 How to Start the Chat System"
echo "=============================="
echo ""
echo "1️⃣  Start Redis (if not running):"
echo "   docker run -d -p 6379:6379 redis:alpine"
echo ""
echo "2️⃣  Start Kafka (if not running):"
echo "   docker-compose up -d kafka"
echo ""
echo "3️⃣  Start Django server (Terminal 1):"
echo "   daphne -b 0.0.0.0 -p 8000 config.asgi:application"
echo ""
echo "4️⃣  Start Kafka consumer (Terminal 2):"
echo "   python manage.py run_chat_consumer"
echo ""
echo "5️⃣  Test the API:"
echo "   curl -X POST http://localhost:8000/api/chat/conversations/1/messages/ \\"
echo "     -H 'Authorization: Bearer YOUR_TOKEN' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"content\": \"What is the price of AAPL?\"}'"
echo ""
echo "📚 Full documentation: CHAT_BACKEND_COMPLETE.md"
echo ""
