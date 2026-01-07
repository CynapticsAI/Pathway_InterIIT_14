"""
Django management command to setup Kafka topics
Usage: python manage.py setup_kafka_topics
"""

from django.core.management.base import BaseCommand
from kafka_consumer.topic_manager import setup_kafka_topics
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Setup Kafka topics automatically'

    def add_arguments(self, parser):
        parser.add_argument(
            '--bootstrap-servers',
            type=str,
            default='localhost:9092',
            help='Kafka bootstrap servers (default: localhost:9092)'
        )

    def handle(self, *args, **options):
        bootstrap_servers = options['bootstrap_servers']
        
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("🔧 Kafka Topic Setup"))
        self.stdout.write("=" * 80)
        self.stdout.write(f"Bootstrap servers: {bootstrap_servers}")
        self.stdout.write("=" * 80)
        
        try:
            success = setup_kafka_topics(bootstrap_servers)
            
            if success:
                self.stdout.write(self.style.SUCCESS("\n✅ All topics setup successfully!"))
                return
            else:
                self.stdout.write(self.style.WARNING("\n⚠️  Some topics failed to setup"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Error: {e}"))
            raise
