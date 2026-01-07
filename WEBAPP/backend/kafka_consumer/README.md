# Kafka Consumer for Django Backend

This Django app provides Kafka consumer functionality to listen to various topics and process real-time data.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Settings

The Kafka configuration is already set up in `config/settings.py`:

```python
KAFKA_CONFIG = {
    'bootstrap_servers': ['localhost:9092'],
    'group_id': 'django-backend-consumer',
    'auto_offset_reset': 'earliest',
    'enable_auto_commit': True,
}

KAFKA_TOPICS = {
    'market_breadth': 'market_breadth',
    # Add more topics here
}
```

### 3. Run the Consumer

```bash
# Start consuming all configured topics
python manage.py consume_kafka

# Consume specific topics
python manage.py consume_kafka --topics market_breadth

# Use custom consumer group
python manage.py consume_kafka --group-id my-consumer-group

# Enable verbose logging
python manage.py consume_kafka --verbose
```

## 📁 Structure

```
kafka_consumer/
├── __init__.py
├── apps.py
├── consumers/
│   ├── __init__.py
│   └── base_consumer.py          # Base Kafka consumer class
├── handlers/
│   ├── __init__.py
│   └── market_breadth_handler.py # Market breadth message handler
├── management/
│   └── commands/
│       └── consume_kafka.py       # Django management command
└── utils.py                       # Utility functions
```

## 🔧 How It Works

1. **Base Consumer** (`consumers/base_consumer.py`):
   - Connects to Kafka broker
   - Subscribes to specified topics
   - Polls for messages
   - Handles errors and reconnection
   - Graceful shutdown on SIGINT/SIGTERM

2. **Message Handlers** (`handlers/`):
   - Process messages from specific topics
   - Currently logs messages (Phase 1)
   - Future: Save to database and broadcast to frontend

3. **Management Command** (`management/commands/consume_kafka.py`):
   - Django command to start the consumer
   - Routes messages to appropriate handlers
   - Provides statistics and monitoring

## 📊 Current Topics

### market_breadth
- **Handler**: `MarketBreadthHandler`
- **Current Action**: Logs incoming messages with formatted output
- **Future**: Save to database, broadcast to WebSocket

## ➕ Adding New Topics

### Step 1: Add Topic to Settings

Edit `config/settings.py`:

```python
KAFKA_TOPICS = {
    'market_breadth': 'market_breadth',
    'sector_predictions': 'sector_predictions',  # New topic
}
```

### Step 2: Create Handler

Create `kafka_consumer/handlers/sector_predictions_handler.py`:

```python
import logging
from typing import Dict, Any

logger = logging.getLogger('kafka_consumer')

class SectorPredictionsHandler:
    def __init__(self):
        self.message_count = 0
        logger.info("SectorPredictionsHandler initialized")
    
    def process(self, message_info: Dict[str, Any]):
        self.message_count += 1
        data = message_info.get('data')
        
        # Process the data
        logger.info(f"Sector Prediction: {data}")
        
        # TODO: Save to database, broadcast to frontend
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            'handler': 'SectorPredictionsHandler',
            'messages_processed': self.message_count,
        }
```

### Step 3: Register Handler

Edit `kafka_consumer/management/commands/consume_kafka.py`:

```python
from kafka_consumer.handlers import MarketBreadthHandler, SectorPredictionsHandler

handlers_map = {
    'market_breadth': MarketBreadthHandler(),
    'sector_predictions': SectorPredictionsHandler(),  # Add here
}
```

### Step 4: Run Consumer

```bash
python manage.py consume_kafka --topics sector_predictions
```

## 🔄 Integration Roadmap

### Phase 1: Logging (✅ Current)
- Receive messages from Kafka
- Log message content
- Basic error handling

### Phase 2: Database Integration (📋 Next)
- Create Django models for data
- Parse and validate messages
- Save to database
- Add data integrity checks

### Phase 3: WebSocket Broadcasting (📋 Future)
- Set up Django Channels
- Broadcast real-time data to frontend
- Handle client subscriptions
- Implement data throttling

### Phase 4: Advanced Features (📋 Future)
- Message queuing and buffering
- Data aggregation and caching
- Health monitoring and alerts
- Performance metrics

## 🛠️ Production Deployment

### Using Supervisor

Create `/etc/supervisor/conf.d/kafka_consumer.conf`:

```ini
[program:kafka_consumer]
command=/path/to/venv/bin/python /path/to/manage.py consume_kafka
directory=/path/to/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/kafka_consumer.log
```

### Using systemd

Create `/etc/systemd/system/kafka_consumer.service`:

```ini
[Unit]
Description=Django Kafka Consumer
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/backend
ExecStart=/path/to/venv/bin/python manage.py consume_kafka
Restart=always

[Install]
WantedBy=multi-user.target
```

### Using Docker

The consumer can run as a separate container alongside your Django web server.

## 📝 Logging

Logs are written to:
- **Console**: Real-time output
- **File**: `backend/logs/kafka_consumer.log` (rotated at 10MB)

Log format:
```
INFO 2025-12-02 10:30:45 market_breadth_handler 📊 MARKET BREADTH MESSAGE #1
```

## 🐛 Troubleshooting

### Consumer Can't Connect to Kafka

```bash
# Check if Kafka is running
docker ps | grep kafka

# Test connection
python -c "from kafka_consumer.utils import validate_kafka_connection; validate_kafka_connection('localhost:9092')"
```

### No Messages Received

1. Check topic exists and has data
2. Verify `auto_offset_reset` setting
3. Check consumer group offset

### Consumer Stops Processing

1. Check Kafka broker health
2. Review error logs in `logs/kafka_consumer.log`
3. Verify network connectivity

## 🔒 Security Notes

- Kafka authentication not yet implemented
- Use VPN or private network for production
- Consider adding SSL/TLS for encryption
- Implement message validation and sanitization

## 📚 Resources

- [Confluent Kafka Python Client](https://docs.confluent.io/kafka-clients/python/current/overview.html)
- [Django Management Commands](https://docs.djangoproject.com/en/stable/howto/custom-management-commands/)
- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
