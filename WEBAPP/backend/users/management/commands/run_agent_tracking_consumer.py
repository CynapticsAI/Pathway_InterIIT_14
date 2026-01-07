"""
Agent Tracking WebSocket Forwarder
Consumes 'track' Kafka topic and forwards agent tracking data to chat websocket clients.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
import logging

try:
    from kafka import KafkaConsumer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Consume 'track' Kafka topic and forward agent tracking to websocket."

    def handle(self, *args, **options):
        if not KAFKA_AVAILABLE:
            self.stdout.write(self.style.ERROR('❌ kafka-python not installed!'))
            self.stdout.write(self.style.WARNING('Install with: pip install kafka-python'))
            return

        kafka_config = getattr(settings, 'KAFKA_CONFIG', {})
        bootstrap_servers = kafka_config.get('bootstrap_servers', ['localhost:9092'])
        if isinstance(bootstrap_servers, str):
            bootstrap_servers = [bootstrap_servers]

        topic = 'track'
        group_id = 'agent-tracking-consumer-group'

        self.stdout.write(self.style.SUCCESS(f"🚀 Starting Agent Tracking Consumer on topic '{topic}'"))
        self.stdout.write(self.style.SUCCESS(f'🔌 Brokers: {", ".join(bootstrap_servers)}'))

        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id=group_id,
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
                api_version=(0, 10, 1)
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed to connect to Kafka: {e}'))
            return

        channel_layer = get_channel_layer()
        try:
            for message in consumer:
                data = message.value
                user_id = data.get('user_id')
                conversation_id = data.get('conversation_id')
                # Forward to chat websocket group
                group = f'chat_{conversation_id}'
                async_to_sync(channel_layer.group_send)(
                    group,
                    {
                        'type': 'agent_tracking',
                        'tracking': data,
                        'conversation_id': conversation_id,
                        'user_id': user_id
                    }
                )
                self.stdout.write(self.style.SUCCESS(f"📡 Forwarded agent tracking for conversation {conversation_id}, user {user_id}"))
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\n⏹️  Consumer stopped by user'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Consumer error: {e}'))
        finally:
            consumer.close()
            self.stdout.write(self.style.SUCCESS('👋 Consumer closed'))
