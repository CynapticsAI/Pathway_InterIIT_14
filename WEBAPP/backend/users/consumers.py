"""
WebSocket consumer for real-time chat updates
Handles bidirectional communication for chat messages
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for chat messages
    
    URL: ws://<host>/ws/chat/<conversation_id>/
    
    Features:
    - Real-time message updates
    - User authentication required
    - Group-based messaging (per conversation)
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.conversation_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope.get('user')
        
        # Check authentication
        if not self.user or isinstance(self.user, AnonymousUser):
            logger.warning(f"❌ Unauthorized WebSocket connection attempt for conversation {self.conversation_id}")
            await self.close(code=4001)
            return
        
        # Verify user has access to this conversation
        has_access = await self.verify_conversation_access()
        if not has_access:
            logger.warning(f"❌ User {self.user.id} denied access to conversation {self.conversation_id}")
            await self.close(code=4003)
            return
        
        # Join conversation group
        await self.channel_layer.group_add(
            self.conversation_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"✅ User {self.user.id} connected to conversation {self.conversation_id}")
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to chat',
            'conversation_id': self.conversation_id,
            'user_id': self.user.id
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave conversation group
        if hasattr(self, 'conversation_group_name'):
            await self.channel_layer.group_discard(
                self.conversation_group_name,
                self.channel_name
            )
        
        if hasattr(self, 'user') and self.user:
            logger.info(f"👋 User {self.user.id} disconnected from conversation {self.conversation_id}")
    
    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages from client
        Currently, messages are sent via REST API, so this is for future use
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'unknown')
            
            if message_type == 'ping':
                # Handle ping/pong for connection keep-alive
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            
            elif message_type == 'typing':
                # Broadcast typing indicator to other users in conversation
                await self.channel_layer.group_send(
                    self.conversation_group_name,
                    {
                        'type': 'typing_indicator',
                        'user_id': self.user.id,
                        'is_typing': data.get('is_typing', False)
                    }
                )
            
            else:
                logger.warning(f"⚠️ Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("❌ Invalid JSON received from client")
        except Exception as e:
            logger.error(f"❌ Error handling WebSocket message: {e}")
    
    # ========================================================================
    # Group message handlers (called by channel layer)
    # ========================================================================
    
    async def chat_message(self, event):
        """
        Handle chat message broadcast to group
        Sent when new message is created (user or assistant)
        """
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'conversation_id': event.get('conversation_id'),
            'timestamp': event.get('timestamp')
        }))
    
    async def message_pending(self, event):
        """
        Handle message pending status
        Sent when user message is sent to Kafka and waiting for response
        """
        await self.send(text_data=json.dumps({
            'type': 'message_pending',
            'message': event['message'],
            'conversation_id': event.get('conversation_id'),
            'kafka_message_id': event.get('kafka_message_id')
        }))
    
    async def message_completed(self, event):
        """
        Handle message completion
        Sent when assistant response is received from Kafka
        """
        await self.send(text_data=json.dumps({
            'type': 'message_completed',
            'message': event['message'],
            'conversation_id': event.get('conversation_id'),
            'kafka_message_id': event.get('kafka_message_id')
        }))
    
    async def message_failed(self, event):
        """
        Handle message failure
        Sent when message processing fails
        """
        await self.send(text_data=json.dumps({
            'type': 'message_failed',
            'message': event.get('message'),
            'error': event.get('error'),
            'conversation_id': event.get('conversation_id'),
            'kafka_message_id': event.get('kafka_message_id')
        }))
    
    async def typing_indicator(self, event):
        """
        Handle typing indicator broadcast
        """
        # Don't send typing indicator to the user who is typing
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'user_id': event['user_id'],
                'is_typing': event['is_typing']
            }))
    
    async def agent_tracking(self, event):
        """
        Handle agent tracking updates from Kafka and forward to frontend
        """
        await self.send(text_data=json.dumps({
            'type': 'agent_tracking',
            'tracking': event.get('tracking'),
            'conversation_id': event.get('conversation_id'),
            'user_id': event.get('user_id')
        }))
    
    # ========================================================================
    # Database queries (run in sync context)
    # ========================================================================
    
    @database_sync_to_async
    def verify_conversation_access(self):
        """
        Verify user has access to the conversation
        Returns True if user owns the conversation, False otherwise
        """
        from .models import ChatConversation
        
        try:
            conversation = ChatConversation.objects.get(
                id=self.conversation_id,
                user=self.user
            )
            return True
        except ChatConversation.DoesNotExist:
            return False


class ChatListConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for chat list updates
    
    URL: ws://<host>/ws/chat/list/
    
    Features:
    - Real-time updates for conversation list
    - Notifications when new conversations are created
    - Updates when conversation metadata changes
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope.get('user')
        
        # Check authentication
        if not self.user or isinstance(self.user, AnonymousUser):
            logger.warning("❌ Unauthorized WebSocket connection attempt for chat list")
            await self.close(code=4001)
            return
        
        # Create user-specific group
        self.user_group_name = f'chat_list_{self.user.id}'
        
        # Join user's chat list group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"✅ User {self.user.id} connected to chat list")
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to chat list updates'
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
        
        if hasattr(self, 'user') and self.user:
            logger.info(f"👋 User {self.user.id} disconnected from chat list")
    
    async def receive(self, text_data):
        """Handle incoming messages (ping/pong)"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'unknown')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
        except Exception as e:
            logger.error(f"❌ Error handling chat list message: {e}")
    
    # ========================================================================
    # Group message handlers
    # ========================================================================
    
    async def conversation_created(self, event):
        """Broadcast when new conversation is created"""
        await self.send(text_data=json.dumps({
            'type': 'conversation_created',
            'conversation': event['conversation']
        }))
    
    async def conversation_updated(self, event):
        """Broadcast when conversation is updated"""
        await self.send(text_data=json.dumps({
            'type': 'conversation_updated',
            'conversation': event['conversation']
        }))
    
    async def conversation_deleted(self, event):
        """Broadcast when conversation is deleted"""
        await self.send(text_data=json.dumps({
            'type': 'conversation_deleted',
            'conversation_id': event['conversation_id']
        }))
