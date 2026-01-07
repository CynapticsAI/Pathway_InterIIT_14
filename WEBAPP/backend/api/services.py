"""
Notification Service
Centralized service for creating and managing notifications
"""
from django.utils import timezone
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from datetime import datetime, timedelta
from .models import Notification, NotificationPreference, Stock, Portfolio
from .email_service import EmailNotificationService
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service class for handling notification creation and delivery
    """
    
    @staticmethod
    def create_news_notification(news_data, symbol):
        """
        Create notifications for news events
        
        Args:
            news_data (dict): News data from Kafka containing headline, sentiment, etc.
            symbol (str): Stock symbol
            
        Returns:
            list: List of created Notification objects
        """
        notifications_created = []
        
        try:
            # Find all users who have this stock in their portfolio
            users_with_stock = NotificationService._get_users_with_stock(symbol)
            
            if not users_with_stock:
                logger.debug(f"No users have {symbol} in their portfolio")
                return notifications_created
            
            # Extract news details
            headline = news_data.get('headline', 'News Update')
            sentiment = news_data.get('sentiment', 'neutral')
            source = news_data.get('source', 'Unknown')
            timestamp = news_data.get('timestamp', timezone.now())
            
            # Ensure timestamp is a datetime object
            if isinstance(timestamp, str):
                try:
                    # Try ISO format parsing
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except Exception:
                    timestamp = timezone.now()
            elif not isinstance(timestamp, datetime):
                timestamp = timezone.now()
            
            # Determine priority based on sentiment
            priority = NotificationService._determine_news_priority(sentiment)
            
            # Create title and message
            title = f"📰 News: {symbol}"
            message = f"{headline[:200]}"  # Limit message length
            
            # Create notifications for each user
            for user in users_with_stock:
                # Check user preferences
                if not NotificationService._should_send_news_notification(user):
                    continue
                
                # Check for duplicate recent notifications
                if NotificationService._is_duplicate_notification(
                    user, 'NEWS', symbol, timestamp
                ):
                    logger.debug(f"Skipping duplicate news notification for {user.username}")
                    continue
                
                notification = Notification.objects.create(
                    user=user,
                    notification_type='NEWS',
                    symbol=symbol,
                    title=title,
                    message=message,
                    data=news_data,
                    timestamp=timestamp,
                    priority=priority,
                    status='UNREAD'
                )
                
                notifications_created.append(notification)
                
                # Send real-time notification via WebSocket
                NotificationService._send_websocket_notification(user.id, notification)
                
                # Send email notification
                try:
                    EmailNotificationService.send_notification_email(notification, user)
                except Exception as e:
                    logger.error(f"Failed to send email notification: {e}", exc_info=True)
                
            logger.info(f"Created {len(notifications_created)} news notifications for {symbol}")
            
        except Exception as e:
            logger.error(f"Error creating news notifications: {e}", exc_info=True)
        
        return notifications_created
    
    @staticmethod
    def create_volume_spike_notification(spike_data, symbol):
        """
        Create notifications for volume spike events
        
        Args:
            spike_data (dict): Volume spike data from Kafka
            symbol (str): Stock symbol
            
        Returns:
            list: List of created Notification objects
        """
        notifications_created = []
        
        try:
            # Find all users who have this stock in their portfolio
            users_with_stock = NotificationService._get_users_with_stock(symbol)
            
            if not users_with_stock:
                logger.debug(f"No users have {symbol} in their portfolio")
                return notifications_created
            
            # Extract spike details
            spike_percentage = spike_data.get('spike_percentage', 0)
            current_volume = spike_data.get('current_volume', 0)
            avg_volume = spike_data.get('average_volume', 0)
            timestamp = spike_data.get('timestamp', timezone.now())
            price_change = spike_data.get('price_change_percentage', 0)
            
            # Ensure timestamp is a datetime object
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except Exception:
                    timestamp = timezone.now()
            elif not isinstance(timestamp, datetime):
                timestamp = timezone.now()
            
            # Determine priority based on spike magnitude
            priority = NotificationService._determine_spike_priority(spike_percentage)
            
            # Create title and message
            title = f"📊 Volume Spike: {symbol}"
            message = (
                f"Volume increased by {spike_percentage:.1f}%! "
                f"Current: {current_volume:,.0f} | Avg: {avg_volume:,.0f}"
            )
            if price_change:
                message += f" | Price: {price_change:+.2f}%"
            
            # Create notifications for each user
            for user in users_with_stock:
                # Check user preferences and threshold
                if not NotificationService._should_send_spike_notification(
                    user, spike_percentage
                ):
                    continue
                
                # Check for duplicate recent notifications
                if NotificationService._is_duplicate_notification(
                    user, 'VOLUME_SPIKE', symbol, timestamp, minutes=30
                ):
                    logger.debug(f"Skipping duplicate spike notification for {user.username}")
                    continue
                
                notification = Notification.objects.create(
                    user=user,
                    notification_type='VOLUME_SPIKE',
                    symbol=symbol,
                    title=title,
                    message=message,
                    data=spike_data,
                    timestamp=timestamp,
                    priority=priority,
                    status='UNREAD'
                )
                
                notifications_created.append(notification)
                
                # Send real-time notification via WebSocket
                NotificationService._send_websocket_notification(user.id, notification)
                
                # Send email notification
                try:
                    EmailNotificationService.send_notification_email(notification, user)
                except Exception as e:
                    logger.error(f"Failed to send email notification: {e}", exc_info=True)
                
            logger.info(f"Created {len(notifications_created)} volume spike notifications for {symbol}")
            
        except Exception as e:
            logger.error(f"Error creating volume spike notifications: {e}", exc_info=True)
        
        return notifications_created
    
    @staticmethod
    def _get_users_with_stock(symbol):
        """
        Get all users who have a specific stock in their portfolio
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            QuerySet: Users with the stock
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Get user IDs from stocks
        user_ids = Stock.objects.filter(
            symbol=symbol
        ).values_list('portfolio__user_id', flat=True).distinct()
        
        # Return User objects
        return User.objects.filter(id__in=user_ids)
    
    @staticmethod
    def _should_send_news_notification(user):
        """
        Check if user wants to receive news notifications
        
        Args:
            user: User object
            
        Returns:
            bool: True if notification should be sent
        """
        try:
            prefs = user.notification_preferences
            return prefs.news_alerts_enabled and prefs.web_notifications_enabled
        except NotificationPreference.DoesNotExist:
            # Default to True if preferences don't exist
            return True
    
    @staticmethod
    def _should_send_spike_notification(user, spike_percentage):
        """
        Check if user wants to receive volume spike notifications
        
        Args:
            user: User object
            spike_percentage (float): Volume spike percentage
            
        Returns:
            bool: True if notification should be sent
        """
        try:
            prefs = user.notification_preferences
            return (
                prefs.volume_spike_alerts_enabled and
                prefs.web_notifications_enabled and
                spike_percentage >= float(prefs.min_volume_spike_threshold)
            )
        except NotificationPreference.DoesNotExist:
            # Default threshold of 50%
            return spike_percentage >= 50.0
    
    @staticmethod
    def _is_duplicate_notification(user, notification_type, symbol, timestamp, minutes=5):
        """
        Check if a similar notification was recently sent to avoid spam
        
        Args:
            user: User object
            notification_type (str): Type of notification
            symbol (str): Stock symbol
            timestamp (datetime): Event timestamp
            minutes (int): Time window to check for duplicates
            
        Returns:
            bool: True if duplicate exists
        """
        from datetime import timedelta
        
        cutoff_time = timestamp - timedelta(minutes=minutes)
        
        exists = Notification.objects.filter(
            user=user,
            notification_type=notification_type,
            symbol=symbol,
            timestamp__gte=cutoff_time
        ).exists()
        
        return exists
    
    @staticmethod
    def _determine_news_priority(sentiment):
        """
        Determine notification priority based on news sentiment
        
        Args:
            sentiment (str): News sentiment (positive, negative, neutral)
            
        Returns:
            str: Priority level (HIGH, MEDIUM, LOW)
        """
        sentiment_lower = str(sentiment).lower()
        
        if sentiment_lower in ['very_positive', 'very_negative', 'breaking']:
            return 'HIGH'
        elif sentiment_lower in ['positive', 'negative']:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    @staticmethod
    def _determine_spike_priority(spike_percentage):
        """
        Determine notification priority based on volume spike magnitude
        
        Args:
            spike_percentage (float): Volume spike percentage
            
        Returns:
            str: Priority level (HIGH, MEDIUM, LOW)
        """
        if spike_percentage >= 100:
            return 'HIGH'
        elif spike_percentage >= 50:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    @staticmethod
    def _send_websocket_notification(user_id, notification):
        """
        Send notification via WebSocket to user
        
        Args:
            user_id (int): User ID
            notification (Notification): Notification object
        """
        try:
            channel_layer = get_channel_layer()
            group_name = f'notifications_user_{user_id}'
            
            # Prepare notification data
            notification_data = {
                'id': notification.id,
                'type': notification.notification_type,
                'symbol': notification.symbol,
                'title': notification.title,
                'message': notification.message,
                'priority': notification.priority,
                'timestamp': notification.timestamp.isoformat(),
                'created_at': notification.created_at.isoformat(),
                'data': notification.data,
            }
            
            # Send to channel layer
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'notification_alert',
                    'data': notification_data
                }
            )
            
            logger.debug(f"Sent WebSocket notification to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending WebSocket notification: {e}", exc_info=True)
    
    @staticmethod
    def mark_all_as_read(user):
        """
        Mark all unread notifications as read for a user
        
        Args:
            user: User object
            
        Returns:
            int: Number of notifications marked as read
        """
        count = Notification.objects.filter(
            user=user,
            status='UNREAD'
        ).update(
            status='READ',
            read_at=timezone.now()
        )
        
        logger.info(f"Marked {count} notifications as read for {user.username}")
        return count
    
    @staticmethod
    def get_unread_count(user):
        """
        Get count of unread notifications for a user
        
        Args:
            user: User object
            
        Returns:
            int: Count of unread notifications
        """
        return Notification.objects.filter(
            user=user,
            status='UNREAD'
        ).count()
    
    @staticmethod
    def cleanup_old_notifications(days=30):
        """
        Archive notifications older than specified days
        
        Args:
            days (int): Number of days to keep notifications
            
        Returns:
            int: Number of notifications archived
        """
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        count = Notification.objects.filter(
            created_at__lt=cutoff_date,
            status__in=['READ', 'UNREAD']
        ).update(status='ARCHIVED')
        
        logger.info(f"Archived {count} notifications older than {days} days")
        return count
