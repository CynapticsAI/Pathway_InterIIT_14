"""
Market Breadth Handler
Processes messages from the market_breadth Kafka topic.
"""
import logging
import json
from datetime import datetime
from typing import Dict, Any
from django.utils import timezone
from api.models import MarketBreadth
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


class MarketBreadthHandler:
    """
    Handler for processing market breadth data from Kafka.
    Saves data to database and broadcasts to WebSocket clients.
    """
    
    def __init__(self):
        """Initialize the handler."""
        self.message_count = 0
        self.saved_count = 0
        self.error_count = 0
        self.channel_layer = get_channel_layer()
        logger.info("MarketBreadthHandler initialized")
    
    def process(self, message_info: Dict[str, Any]):
        """
        Process a market breadth message.
        
        Args:
            message_info: Dictionary containing message details:
                - topic: Kafka topic name
                - partition: Partition number
                - offset: Message offset
                - key: Message key
                - value: Raw message value
                - data: Parsed JSON data (if applicable)
                - timestamp: Message timestamp
        """
        self.message_count += 1
        
        try:
            topic = message_info.get('topic')
            data = message_info.get('data')
            timestamp_info = message_info.get('timestamp')
            
            # Extract timestamp (tuple of timestamp_type and timestamp_value)
            if timestamp_info and len(timestamp_info) == 2:
                timestamp_ms = timestamp_info[1]
                timestamp_dt = datetime.fromtimestamp(timestamp_ms / 1000.0)
                timestamp_str = timestamp_dt.strftime('%Y-%m-%d %H:%M:%S')
            else:
                timestamp_str = 'Unknown'
                timestamp_dt = timezone.now()
            
            # Log the received message
            logger.info("=" * 80)
            logger.info(f"📊 MARKET BREADTH MESSAGE #{self.message_count}")
            logger.info(f"Topic: {topic}")
            logger.info(f"Timestamp: {timestamp_str}")
            logger.info(f"Partition: {message_info.get('partition')}")
            logger.info(f"Offset: {message_info.get('offset')}")
            
            if message_info.get('key'):
                logger.info(f"Key: {message_info.get('key')}")
            
            # Log the data content
            if data:
                logger.info("Data:")
                # Pretty print JSON data
                formatted_data = json.dumps(data, indent=2)
                for line in formatted_data.split('\n'):
                    logger.info(f"  {line}")
                
                # Save to database
                self._save_to_database(data, timestamp_dt)
                
                # Broadcast to WebSocket clients
                self._broadcast_to_frontend(data)
            else:
                logger.info(f"Raw Value: {message_info.get('value')}")
            
            logger.info("=" * 80)
            
            # TODO: Future WebSocket broadcast
            # self._broadcast_to_frontend(data)
        
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing market breadth message: {e}", exc_info=True)
    
    def _save_to_database(self, data: Dict[str, Any], timestamp_dt: datetime):
        """
        Save market breadth data to database.
        
        Args:
            data: Parsed message data
            timestamp_dt: Timestamp for the data
        """
        try:
            # Extract data timestamp if available in the message
            if 'timestamp' in data:
                # Handle various timestamp formats
                ts = data['timestamp']
                if isinstance(ts, (int, float)):
                    # Unix timestamp in milliseconds
                    data_timestamp = datetime.fromtimestamp(ts / 1000.0) if ts > 1e10 else datetime.fromtimestamp(ts)
                elif isinstance(ts, str):
                    # ISO format string
                    data_timestamp = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                else:
                    data_timestamp = timestamp_dt
            else:
                data_timestamp = timestamp_dt
            
            # Create MarketBreadth record
            market_breadth = MarketBreadth.objects.create(
                timestamp=data_timestamp,
                advancing_stocks=data.get('advancing_stocks', 0),
                declining_stocks=data.get('declining_stocks', 0),
                unchanged_stocks=data.get('unchanged_stocks', 0),
                total_stocks=data.get('total_stocks', 0),
                advance_decline_line=data.get('advance_decline_line', 0)
            )
            
            self.saved_count += 1
            logger.info(f"✅ Saved MarketBreadth record: {market_breadth.id}")
            
        except Exception as e:
            logger.error(f"Error saving market breadth to database: {e}", exc_info=True)
    
    def _broadcast_to_frontend(self, data: Dict[str, Any]):
        """
        Broadcast data to frontend via WebSocket.
        
        Args:
            data: Parsed message data
        """
        if self.channel_layer:
            try:
                async_to_sync(self.channel_layer.group_send)(
                    'market_breadth',
                    {
                        'type': 'market_breadth_update',
                        'data': data
                    }
                )
                logger.debug("📡 Broadcasted to WebSocket clients")
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get handler statistics.
        
        Returns:
            Dictionary with handler stats
        """
        return {
            'handler': 'MarketBreadthHandler',
            'messages_processed': self.message_count,
            'records_saved': self.saved_count,
            'errors': self.error_count,
        }
