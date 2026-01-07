"""
Volume Spike Handler
Processes messages from the spike_detector Kafka topic.
"""
import logging
import json
from datetime import datetime
from typing import Dict, Any
from django.utils import timezone
from api.models import VolumeSpike
from api.services import NotificationService
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


class VolumeSpikeHandler:
    """
    Handler for processing volume spike detection data from Kafka.
    Saves unusual volume activity alerts to database.
    """
    
    def __init__(self):
        """Initialize the handler."""
        self.message_count = 0
        self.saved_count = 0
        self.error_count = 0
        self.channel_layer = get_channel_layer()
        logger.info("VolumeSpikeHandler initialized")
    
    def process(self, message_info: Dict[str, Any]):
        """
        Process a volume spike message.
        
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
                logger.info(f"🚨 Volume Spike: {data.get('symbol', 'UNKNOWN')}")
                self._save_to_database(data, timestamp_dt)
                self._broadcast_to_frontend(data)
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing volume spike message: {e}", exc_info=True)
    
    def _save_to_database(self, data: Dict[str, Any], timestamp_dt: datetime):
        """
        Save volume spike data to database and create notifications.
        
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
            
            # Extract symbol and store all data as JSON
            symbol = data.get('symbol', 'UNKNOWN')
            
            # Create VolumeSpike record
            spike = VolumeSpike.objects.create(
                symbol=symbol,
                timestamp=data_timestamp,
                spike_data=data
            )
            
            self.saved_count += 1
            logger.info(f"✅ Saved VolumeSpike record: {spike.id}")
            
            # Create notifications for users with this stock
            if symbol != 'UNKNOWN':
                self._create_notifications(data, symbol, data_timestamp)
            
        except Exception as e:
            logger.error(f"Error saving volume spike to database: {e}", exc_info=True)
    
    def _create_notifications(self, data: Dict[str, Any], symbol: str, timestamp_dt: datetime):
        """
        Create notifications for volume spike events.
        
        Args:
            data: Volume spike data
            symbol: Stock symbol
            timestamp_dt: Timestamp of the spike
        """
        try:
            # Prepare spike data for notification
            spike_data = {
                'symbol': symbol,
                'spike_percentage': data.get('spike_percentage', data.get('volume_increase', 0)),
                'current_volume': data.get('current_volume', data.get('volume', 0)),
                'average_volume': data.get('average_volume', data.get('avg_volume', 0)),
                'price_change_percentage': data.get('price_change', data.get('price_change_percentage', 0)),
                'current_price': data.get('price', data.get('current_price', 0)),
                'timestamp': timestamp_dt.isoformat(),
            }
            
            # Create notifications
            notifications = NotificationService.create_volume_spike_notification(
                spike_data,
                symbol
            )
            
            if notifications:
                logger.info(f"📬 Created {len(notifications)} volume spike notification(s) for {symbol}")
            
        except Exception as e:
            logger.error(f"Error creating volume spike notifications: {e}", exc_info=True)
    
    def _broadcast_to_frontend(self, data: Dict[str, Any]):
        """Broadcast data to frontend via WebSocket."""
        if self.channel_layer:
            try:
                async_to_sync(self.channel_layer.group_send)(
                    'volume_spikes',
                    {
                        'type': 'volume_spike_update',
                        'data': data
                    }
                )
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get handler statistics."""
        return {
            'handler': 'VolumeSpikeHandler',
            'messages_processed': self.message_count,
            'records_saved': self.saved_count,
            'errors': self.error_count,
        }
