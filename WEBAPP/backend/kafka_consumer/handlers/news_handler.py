"""
News Handler
Processes messages from the news Kafka topic.
"""
import logging
import json
from datetime import datetime
from typing import Dict, Any
from django.utils import timezone
from api.models import NewsData
from api.services import NotificationService
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)


class NewsHandler:
    """
    Handler for processing news data from Kafka.
    Saves financial news and sentiment analysis to database.
    """
    
    def __init__(self):
        """Initialize the handler."""
        self.message_count = 0
        self.saved_count = 0
        self.error_count = 0
        self.channel_layer = get_channel_layer()
        logger.info("NewsHandler initialized")
    
    def process(self, message_info: Dict[str, Any]):
        """
        Process a news message.
        
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
                logger.info(f"📰 News Update received")
                self._save_to_database(data, timestamp_dt)
                self._broadcast_to_frontend(data)
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing news message: {e}", exc_info=True)
    
    def _save_to_database(self, data: Dict[str, Any], timestamp_dt: datetime):
        """
        Save news data to database and create notifications.
        
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
            
            # Create NewsData record with all data as JSON
            news = NewsData.objects.create(
                timestamp=data_timestamp,
                news_data=data
            )
            
            self.saved_count += 1
            logger.info(f"✅ Saved NewsData record: {news.id}")
            
            # Create notifications for users with relevant stocks
            self._create_notifications(data, data_timestamp)
            
        except Exception as e:
            logger.error(f"Error saving news to database: {e}", exc_info=True)
    
    def _create_notifications(self, data: Dict[str, Any], timestamp_dt: datetime):
        """
        Create notifications for news events.
        
        Args:
            data: News data
            timestamp_dt: Timestamp of the news
        """
        try:
            # Extract symbol(s) from news data
            # News data might have 'symbol', 'symbols', 'ticker', or 'tickers'
            symbols = []
            
            if 'symbol' in data:
                symbols.append(data['symbol'])
            elif 'symbols' in data and isinstance(data['symbols'], list):
                symbols.extend(data['symbols'])
            elif 'ticker' in data:
                symbols.append(data['ticker'])
            elif 'tickers' in data and isinstance(data['tickers'], list):
                symbols.extend(data['tickers'])
            elif 'stock' in data:
                symbols.append(data['stock'])
            elif 'stocks' in data and isinstance(data['stocks'], list):
                symbols.extend(data['stocks'])
            
            # Clean and normalize symbols
            symbols = [str(s).upper().strip() for s in symbols if s]
            
            if not symbols:
                logger.debug("No symbols found in news data, skipping notifications")
                return
            
            # Prepare news data for notification
            news_data = {
                'headline': data.get('headline', data.get('title', 'News Update')),
                'sentiment': data.get('sentiment', 'neutral'),
                'source': data.get('source', 'Unknown'),
                'url': data.get('url', data.get('link', '')),
                'summary': data.get('summary', data.get('description', '')),
                'timestamp': timestamp_dt.isoformat(),
            }
            
            # Create notifications for each symbol
            notification_count = 0
            for symbol in symbols:
                notifications = NotificationService.create_news_notification(
                    news_data,
                    symbol
                )
                notification_count += len(notifications)
            
            if notification_count > 0:
                logger.info(f"📬 Created {notification_count} news notification(s) for {len(symbols)} symbol(s)")
            
        except Exception as e:
            logger.error(f"Error creating news notifications: {e}", exc_info=True)
    
    def _broadcast_to_frontend(self, data: Dict[str, Any]):
        """Broadcast data to frontend via WebSocket."""
        if self.channel_layer:
            try:
                async_to_sync(self.channel_layer.group_send)(
                    'news_updates',
                    {
                        'type': 'news_update',
                        'data': data
                    }
                )
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get handler statistics."""
        return {
            'handler': 'NewsHandler',
            'messages_processed': self.message_count,
            'records_saved': self.saved_count,
            'errors': self.error_count,
        }
