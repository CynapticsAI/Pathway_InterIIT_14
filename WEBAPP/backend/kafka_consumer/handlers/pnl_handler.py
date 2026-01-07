"""
P&L Handler
Processes messages from the pnl Kafka topic.
"""
import logging
import json
from datetime import datetime
from typing import Dict, Any
from django.utils import timezone
from api.models import PnLData
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


class PnLHandler:
    """
    Handler for processing P&L data from Kafka.
    Saves portfolio profit/loss calculations to database.
    """
    
    def __init__(self):
        """Initialize the handler."""
        self.message_count = 0
        self.saved_count = 0
        self.error_count = 0
        self.channel_layer = get_channel_layer()
        logger.info("PnLHandler initialized")
    
    def process(self, message_info: Dict[str, Any]):
        """
        Process a P&L message.
        
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
                # Handle both field names (total_pnl and total_unrealized_pnl)
                total_pnl = data.get('total_pnl') or data.get('total_unrealized_pnl', 0)
                logger.info(f"💰 P&L Update: Total={total_pnl}")
                self._save_to_database(data, timestamp_dt)
                self._broadcast_to_frontend(data)
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing P&L message: {e}", exc_info=True)
    
    def _save_to_database(self, data: Dict[str, Any], timestamp_dt: datetime):
        """
        Save P&L data to database.
        
        Args:
            data: Parsed message data
            timestamp_dt: Timestamp for the data
        """
        try:
            # Extract timestamp from data if available
            if 'timestamp' in data:
                ts = data['timestamp']
                if isinstance(ts, (int, float)):
                    data_timestamp = datetime.fromtimestamp(ts / 1000.0) if ts > 1e10 else datetime.fromtimestamp(ts)
                elif isinstance(ts, str):
                    data_timestamp = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                else:
                    data_timestamp = timestamp_dt
            else:
                data_timestamp = timestamp_dt
            
            # Extract total_pnl (handle both field names from different sources)
            total_pnl = data.get('total_pnl') or data.get('total_unrealized_pnl', 0)
            
            # Store all data as details
            details = {k: v for k, v in data.items() if k not in ['total_pnl', 'total_unrealized_pnl']}
            
            # Create PnLData record
            pnl_data = PnLData.objects.create(
                timestamp=data_timestamp,
                total_pnl=total_pnl,
                details=details
            )
            
            self.saved_count += 1
            logger.info(f"✅ Saved PnLData record: {pnl_data.id}")
            
        except Exception as e:
            logger.error(f"Error saving P&L to database: {e}", exc_info=True)
    
    def _broadcast_to_frontend(self, data: Dict[str, Any]):
        """Broadcast data to frontend via WebSocket."""
        if self.channel_layer:
            try:
                async_to_sync(self.channel_layer.group_send)(
                    'pnl_updates',
                    {
                        'type': 'pnl_update',
                        'data': data
                    }
                )
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get handler statistics."""
        return {
            'handler': 'PnLHandler',
            'messages_processed': self.message_count,
            'records_saved': self.saved_count,
            'errors': self.error_count,
        }
