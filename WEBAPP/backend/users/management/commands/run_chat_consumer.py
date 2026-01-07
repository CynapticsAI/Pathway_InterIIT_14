"""
Django management command to run Kafka consumer for chat responses
Listens to 'finalResponse' topic and updates chat messages in real-time

Usage:
    python manage.py run_chat_consumer
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
import logging
import time

try:
    from kafka import KafkaConsumer
    from kafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

from users.models import ChatMessage, ChatConversation
from users.serializers import ChatMessageSerializer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run Kafka consumer for chat finalResponse topic'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--topic',
            type=str,
            default='finalResponse',
            help='Kafka topic to consume from (default: finalResponse)'
        )
        parser.add_argument(
            '--group-id',
            type=str,
            default='django-chat-consumer-group',
            help='Kafka consumer group ID'
        )
    
    def handle(self, *args, **options):
        if not KAFKA_AVAILABLE:
            self.stdout.write(self.style.ERROR('❌ kafka-python not installed!'))
            self.stdout.write(self.style.WARNING('Install with: pip install kafka-python'))
            return
        
        topic = options['topic']
        group_id = options['group_id']
        
        self.stdout.write(self.style.SUCCESS('🚀 Starting Chat Kafka Consumer...'))
        self.stdout.write(self.style.SUCCESS(f'📡 Topic: {topic}'))
        self.stdout.write(self.style.SUCCESS(f'👥 Group ID: {group_id}'))
        
        # Get Kafka configuration
        kafka_config = getattr(settings, 'KAFKA_CONFIG', {})
        bootstrap_servers = kafka_config.get('bootstrap_servers', ['localhost:29092'])
        
        # Handle both list and string formats
        if isinstance(bootstrap_servers, str):
            bootstrap_servers = [bootstrap_servers]
        
        self.stdout.write(self.style.SUCCESS(f'🔌 Brokers: {", ".join(bootstrap_servers)}'))
        
        # Create Kafka consumer
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                auto_offset_reset='latest',  # Start from latest messages
                enable_auto_commit=True,
                group_id=group_id,
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
                api_version=(0, 10, 1)
            )
            
            logger.info(f"✅ Consumer connected. Listening to topic: {topic}")
            self.stdout.write(self.style.SUCCESS(f'✅ Connected! Listening for messages...'))
            self.stdout.write(self.style.WARNING('Press Ctrl+C to stop'))
            self.stdout.write('')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed to connect to Kafka: {e}'))
            logger.error(f"Failed to connect Kafka consumer: {e}")
            return
        
        # Get channel layer for WebSocket broadcasting
        channel_layer = get_channel_layer()
        
        # Start consuming messages
        try:
            message_count = 0
            for message in consumer:
                message_count += 1
                self.stdout.write(self.style.SUCCESS(f'\n📨 Message #{message_count} received'))
                self.stdout.write(f'   Partition: {message.partition}, Offset: {message.offset}')
                
                # Process the message
                self.process_message(message.value, channel_layer)
                
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\n⏹️  Consumer stopped by user'))
            logger.info("Consumer stopped by user")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Consumer error: {e}'))
            logger.error(f"Consumer error: {e}", exc_info=True)
        finally:
            consumer.close()
            self.stdout.write(self.style.SUCCESS('👋 Consumer closed'))
            logger.info("Consumer closed")
    
    def process_message(self, data, channel_layer):
        """
        Process incoming message from finalResponse topic
        
        Expected format from your example:
        {
            "user_id": "1",
            "conversation_id": "3",
            "messages": "Today's date is 2025-12-06.",
            "timestamp": 0,
            "agent": "None",
            "satisfied": "satisfied",
            "diff": 1,
            "time": 1765053598170
        }
        """
        try:
            conversation_id = data.get('conversation_id')
            user_id = data.get('user_id')
            response_content = data.get('messages', '')
            agent_name = data.get('agent', 'Unknown Agent')
            response_time = data.get('diff', 0)  # Time in seconds
            satisfied = data.get('satisfied', 'unknown')
            kafka_time = data.get('time')
            
            self.stdout.write(f'   Conversation ID: {conversation_id}')
            self.stdout.write(f'   User ID: {user_id}')
            self.stdout.write(f'   Agent: {agent_name}')
            self.stdout.write(f'   Response: {response_content[:100]}...')
            
            logger.info(f"📨 Received response for conversation: {conversation_id}")
            
            # Find the pending assistant message
            # Try to find by conversation and pending status (most recent)
            assistant_message = ChatMessage.objects.filter(
                conversation_id=conversation_id,
                message_type='assistant',
                status='pending'
            ).order_by('-created_at').first()
            
            if assistant_message:
                # Update the assistant message with response
                assistant_message.content = response_content
                assistant_message.status = 'completed'
                assistant_message.agent_name = agent_name if agent_name != "None" else "AI Assistant"
                assistant_message.response_time_ms = int(response_time * 1000) if response_time else 0
                assistant_message.metadata = {
                    'satisfied': satisfied,
                    'kafka_time': kafka_time,
                    'timestamp': data.get('timestamp'),
                    'raw_response': data
                }
                assistant_message.save()
                
                # Update conversation timestamp
                conversation = assistant_message.conversation
                conversation.last_message_at = timezone.now()
                conversation.save()
                
                logger.info(f"✅ Updated assistant message ID: {assistant_message.id}")
                self.stdout.write(self.style.SUCCESS(f'   ✅ Message updated in database (ID: {assistant_message.id})'))
                
                # Broadcast to WebSocket clients
                conversation_group = f'chat_{conversation_id}'
                
                try:
                    # Send completed message notification
                    async_to_sync(channel_layer.group_send)(
                        conversation_group,
                        {
                            'type': 'message_completed',
                            'message': ChatMessageSerializer(assistant_message).data,
                            'conversation_id': conversation_id,
                            'kafka_message_id': assistant_message.kafka_message_id
                        }
                    )
                    
                    logger.info(f"✅ WebSocket notification sent for conversation {conversation_id}")
                    self.stdout.write(self.style.SUCCESS(f'   ✅ WebSocket notification sent'))
                    
                except Exception as e:
                    logger.error(f"❌ Failed to send WebSocket notification: {e}")
                    self.stdout.write(self.style.WARNING(f'   ⚠️  WebSocket notification failed: {e}'))
            
            else:
                logger.warning(f"⚠️ No pending message found for conversation {conversation_id}")
                self.stdout.write(self.style.WARNING(f'   ⚠️  No pending message found'))
                
                # Optionally create a new assistant message if none found
                # This handles cases where the pending message wasn't created
                try:
                    conversation = ChatConversation.objects.get(id=conversation_id)
                    
                    new_message = ChatMessage.objects.create(
                        conversation=conversation,
                        user=conversation.user,
                        message_type='assistant',
                        content=response_content,
                        status='completed',
                        agent_name=agent_name if agent_name != "None" else "AI Assistant",
                        response_time_ms=int(response_time * 1000) if response_time else 0,
                        metadata={
                            'satisfied': satisfied,
                            'kafka_time': kafka_time,
                            'timestamp': data.get('timestamp'),
                            'raw_response': data
                        }
                    )
                    
                    conversation.last_message_at = timezone.now()
                    conversation.save()
                    
                    # Broadcast new message
                    conversation_group = f'chat_{conversation_id}'
                    async_to_sync(channel_layer.group_send)(
                        conversation_group,
                        {
                            'type': 'chat_message',
                            'message': ChatMessageSerializer(new_message).data,
                            'conversation_id': conversation_id,
                            'timestamp': new_message.created_at.isoformat()
                        }
                    )
                    
                    logger.info(f"✅ Created new assistant message ID: {new_message.id}")
                    self.stdout.write(self.style.SUCCESS(f'   ✅ Created new message (ID: {new_message.id})'))
                    
                except ChatConversation.DoesNotExist:
                    logger.error(f"❌ Conversation {conversation_id} not found")
                    self.stdout.write(self.style.ERROR(f'   ❌ Conversation not found'))
                except Exception as e:
                    logger.error(f"❌ Error creating new message: {e}")
                    self.stdout.write(self.style.ERROR(f'   ❌ Error: {e}'))
                
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}", exc_info=True)
            self.stdout.write(self.style.ERROR(f'   ❌ Processing error: {e}'))
