"""
Stock Tick Handler
Processes messages from the stock_data Kafka topic.
"""
import logging
import json
from datetime import datetime
from typing import Dict, Any
from django.utils import timezone
from api.models import StockTick
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


class StockTickHandler:
    """
    Handler for processing stock tick data from Kafka.
    Saves real-time price and volume updates to database.
    """
    
    def __init__(self):
        """Initialize the handler."""
        self.message_count = 0
        self.saved_count = 0
        self.error_count = 0
        self.channel_layer = get_channel_layer()
        logger.info("StockTickHandler initialized")
    
    def process(self, message_info: Dict[str, Any]):
        """
        Process a stock tick message.
        
        Args:
            message_info: Dictionary containing message details
        """
        self.message_count += 1
        
        try:
            data = message_info.get('data')
            timestamp_info = message_info.get('timestamp')
            
            # Extract timestamp
            if timestamp_info and len(timestamp_info) == 2:
                timestamp_ms = timestamp_info[1]
                timestamp_dt = datetime.fromtimestamp(timestamp_ms / 1000.0)
            else:
                timestamp_dt = timezone.now()
            
            if data:
                logger.debug(f"📈 Stock Tick: {data.get('s')} @ {data.get('p')}")
                self._save_to_database(data, timestamp_dt)
                self._broadcast_to_frontend(data)
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing stock tick message: {e}", exc_info=True)
    
    def _save_to_database(self, data: Dict[str, Any], timestamp_dt: datetime):
        """
        Save stock tick data to database.
        
        Args:
            data: Parsed message data with keys: s (symbol), p (price), v (volume), t (timestamp)
            timestamp_dt: Fallback timestamp
        """
        try:
            # Extract timestamp from data or use fallback
            if 't' in data:
                ts = data['t']
                data_timestamp = datetime.fromtimestamp(ts / 1000.0) if ts > 1e10 else datetime.fromtimestamp(ts)
            else:
                data_timestamp = timestamp_dt
            
            # Create StockTick record
            stock_tick = StockTick.objects.create(
                symbol=data.get('s', 'UNKNOWN'),
                price=data.get('p', 0.0),
                volume=data.get('v', 0.0),
                timestamp=data_timestamp
            )
            
            self.saved_count += 1
            if self.saved_count % 100 == 0:  # Log every 100 records
                logger.info(f"✅ Saved {self.saved_count} StockTick records")
            
        except Exception as e:
            logger.error(f"Error saving stock tick to database: {e}", exc_info=True)
    
    def _broadcast_to_frontend(self, data: Dict[str, Any]):
        """Broadcast data to frontend via WebSocket."""
        if self.channel_layer:
            try:
                async_to_sync(self.channel_layer.group_send)(
                    'stock_ticks',
                    {
                        'type': 'stock_tick_update',
                        'data': data
                    }
                )
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get handler statistics."""
        return {
            'handler': 'StockTickHandler',
            'messages_processed': self.message_count,
            'records_saved': self.saved_count,
            'errors': self.error_count,
        }
