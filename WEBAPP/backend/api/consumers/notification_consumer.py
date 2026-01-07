"""
Notification WebSocket Consumer
Handles user-specific notification delivery in real-time
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for user-specific notifications
    Endpoint: ws://localhost:8000/ws/notifications/
    
    Each user gets their own notification channel group
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        # Get the authenticated user
        self.user = self.scope.get("user")
        
        # Reject if user is not authenticated
        if self.user is None or not self.user.is_authenticated:
            await self.close(code=4001)
            print(f"❌ Unauthenticated user attempted to connect to notifications WebSocket")
            return
        
        # Create user-specific group name
        self.user_id = self.user.id
        self.group_name = f'notifications_user_{self.user_id}'
        
        # Join the user's notification group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        print(f"✅ User {self.user.username} (ID: {self.user_id}) connected to notifications WebSocket")
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to notification stream',
            'user_id': self.user_id
        }))
        
        # Send unread count on connection
        unread_count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': unread_count
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'group_name'):
            # Leave the user's notification group
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            print(f"❌ User {self.user.username} disconnected from notifications WebSocket (code: {close_code})")
    
    async def receive(self, text_data):
        """
        Handle incoming messages from WebSocket client
        Clients can request unread count or mark notifications as read
        """
        try:
            data = json.loads(text_data)
            action = data.get('action', '')
            
            if action == 'get_unread_count':
                # Send current unread count
                unread_count = await self.get_unread_count()
                await self.send(text_data=json.dumps({
                    'type': 'unread_count',
                    'count': unread_count
                }))
            
            elif action == 'mark_read':
                # Mark notification as read
                notification_id = data.get('notification_id')
                if notification_id:
                    success = await self.mark_notification_read(notification_id)
                    if success:
                        unread_count = await self.get_unread_count()
                        await self.send(text_data=json.dumps({
                            'type': 'notification_marked_read',
                            'notification_id': notification_id,
                            'unread_count': unread_count
                        }))
            
            elif action == 'ping':
                # Respond to ping to keep connection alive
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp', '')
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            print(f"Error in notification WebSocket receive: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Server error'
            }))
    
    async def notification_alert(self, event):
        """
        Receive notification from channel layer and send to WebSocket
        This method is called when NotificationService broadcasts a notification
        """
        notification_data = event['data']
        
        # Send the notification to the WebSocket client
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': notification_data
        }))
        
        # Send updated unread count
        unread_count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': unread_count
        }))
    
    @database_sync_to_async
    def get_unread_count(self):
        """Get count of unread notifications for the user"""
        from api.models import Notification
        return Notification.objects.filter(
            user=self.user,
            status='UNREAD'
        ).count()
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark a notification as read"""
        from api.models import Notification
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user=self.user
            )
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False
