"""
Email Notification Service
Handles sending beautiful HTML emails for notifications
"""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """
    Service for sending notification emails
    """
    
    @staticmethod
    def send_notification_email(notification, user):
        """
        Send an email for a notification
        
        Args:
            notification: Notification object
            user: User object
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Get user's email
            if not user.email:
                logger.warning(f"User {user.username} has no email address")
                return False
            
            # Prepare email context
            context = {
                'user': user,
                'notification': notification,
                'symbol': notification.symbol,
                'title': notification.title,
                'message': notification.message,
                'notification_type': notification.get_notification_type_display(),
                'priority': notification.get_priority_display(),
                'timestamp': notification.timestamp,
                'data': notification.data,
                'app_name': 'Pway Stock',
                'app_url': settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:3000',
                'year': timezone.now().year,
            }
            
            # Select appropriate template based on notification type
            if notification.notification_type == 'NEWS':
                subject = f"📰 News Alert: {notification.symbol}"
                template_name = 'emails/notification_news.html'
            elif notification.notification_type == 'VOLUME_SPIKE':
                subject = f"📊 Volume Spike Alert: {notification.symbol}"
                template_name = 'emails/notification_volume_spike.html'
            else:
                subject = f"🔔 {notification.title}"
                template_name = 'emails/notification_generic.html'
            
            # Render HTML content
            html_content = render_to_string(template_name, context)
            
            # Create plain text version (fallback)
            text_content = EmailNotificationService._create_text_version(notification)
            
            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            
            # Attach HTML content
            email.attach_alternative(html_content, "text/html")
            
            # Send email
            email.send(fail_silently=False)
            
            logger.info(f"Sent notification email to {user.email} for {notification.symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending notification email: {e}", exc_info=True)
            return False
    
    @staticmethod
    def _create_text_version(notification):
        """
        Create a plain text version of the notification email
        
        Args:
            notification: Notification object
            
        Returns:
            str: Plain text content
        """
        text = f"""
{notification.title}

{notification.message}

Stock: {notification.symbol}
Type: {notification.get_notification_type_display()}
Priority: {notification.get_priority_display()}
Time: {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

---
Pway Stock - Your Investment Companion
"""
        return text.strip()
    
    @staticmethod
    def send_bulk_notification_emails(notifications):
        """
        Send emails for multiple notifications
        
        Args:
            notifications: List of Notification objects
            
        Returns:
            dict: Statistics about sent emails
        """
        stats = {
            'total': len(notifications),
            'sent': 0,
            'failed': 0
        }
        
        for notification in notifications:
            try:
                if EmailNotificationService.send_notification_email(notification, notification.user):
                    stats['sent'] += 1
                else:
                    stats['failed'] += 1
            except Exception as e:
                logger.error(f"Error sending email for notification {notification.id}: {e}")
                stats['failed'] += 1
        
        logger.info(f"Bulk email send complete: {stats['sent']} sent, {stats['failed']} failed")
        return stats
