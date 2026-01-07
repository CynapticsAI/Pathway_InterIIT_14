"""
Django Management Command to run Kafka Consumer
Usage: python manage.py consume_kafka [--topics topic1 topic2] [--group-id group_name]
"""
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from kafka_consumer.consumers import BaseKafkaConsumer
from kafka_consumer.handlers import (
    MarketBreadthHandler,
    StockTickHandler,
    PnLHandler,
    SarimaxHandler,
    VolumeSpikeHandler,
    NewsHandler,
)
from kafka_consumer.topic_manager import KafkaTopicManager

logger = logging.getLogger('kafka_consumer')


class Command(BaseCommand):
    help = 'Start Kafka consumer to listen to specified topics'
    
    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--topics',
            nargs='+',
            type=str,
            default=None,
            help='Kafka topics to consume (space-separated). Default: all configured topics'
        )
        parser.add_argument(
            '--group-id',
            type=str,
            default=None,
            help='Consumer group ID. Default: from settings'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose logging'
        )
        parser.add_argument(
            '--skip-topic-check',
            action='store_true',
            help='Skip automatic topic creation check'
        )
        parser.add_argument(
            '--bootstrap-servers',
            type=str,
            default='localhost:9092',
            help='Kafka bootstrap servers (default: localhost:9092)'
        )
    
    def handle(self, *args, **options):
        """Main command execution."""
        # Set logging level
        if options['verbose']:
            logger.setLevel(logging.DEBUG)
            logger.debug("Verbose logging enabled")
        
        # Get topics from command line or settings
        topics = options.get('topics')
        if not topics:
            # Use all topics from settings
            kafka_topics = getattr(settings, 'KAFKA_TOPICS', {})
            topics = list(kafka_topics.values())
        
        if not topics:
            self.stdout.write(
                self.style.ERROR('No topics specified. Use --topics or configure KAFKA_TOPICS in settings.')
            )
            return
        
        # Get group ID
        group_id = options.get('group_id')
        bootstrap_servers = options.get('bootstrap_servers', 'localhost:9092')
        skip_topic_check = options.get('skip_topic_check', False)
        
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('🚀 Starting Kafka Consumer'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(f"Topics: {', '.join(topics)}")
        if group_id:
            self.stdout.write(f"Consumer Group: {group_id}")
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        # Auto-create topics if they don't exist
        if not skip_topic_check:
            self.stdout.write(self.style.WARNING('\n🔍 Checking Kafka topics...'))
            try:
                topic_manager = KafkaTopicManager(bootstrap_servers)
                
                # Check which topics need to be created
                missing_topics = []
                for topic in topics:
                    if not topic_manager.topic_exists(topic):
                        missing_topics.append(topic)
                
                if missing_topics:
                    self.stdout.write(self.style.WARNING(f'📝 Creating missing topics: {", ".join(missing_topics)}'))
                    success = topic_manager.ensure_topics_exist(missing_topics)
                    
                    if success:
                        self.stdout.write(self.style.SUCCESS('✅ All topics ready!\n'))
                    else:
                        self.stdout.write(self.style.WARNING('⚠️  Some topics may not have been created\n'))
                else:
                    self.stdout.write(self.style.SUCCESS('✅ All topics already exist!\n'))
                    
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠️  Topic check failed: {e}'))
                self.stdout.write(self.style.WARNING('Continuing anyway... Consumer will fail if topics are missing.\n'))
        
        # Initialize handlers for different topics
        handlers_map = {
            'market_breadth': MarketBreadthHandler(),
            'stock_data': StockTickHandler(),
            'sarimax_forecast': SarimaxHandler(),
            'news_data': NewsHandler(),  # Updated to match actual topic name
            'volume_volatility_data': VolumeSpikeHandler(),  # Reusing handler for volume data
            'pnl': PnLHandler(),  # Topic not yet created in Kafka
        }
        
        # Create a unified handler that routes to specific handlers
        def unified_handler(message_info):
            """Route messages to appropriate handlers based on topic."""
            topic = message_info.get('topic')
            
            # Find the appropriate handler
            handler = handlers_map.get(topic)
            
            if handler:
                handler.process(message_info)
            else:
                logger.warning(f"No handler found for topic: {topic}")
                logger.info(f"Message: {message_info}")
        
        try:
            # Create and run consumer
            consumer = BaseKafkaConsumer(
                topics=topics,
                handler=unified_handler,
                group_id=group_id
            )
            
            self.stdout.write(self.style.SUCCESS('✅ Consumer initialized successfully'))
            self.stdout.write(self.style.WARNING('Press Ctrl+C to stop...'))
            self.stdout.write('')
            
            # Start consuming
            consumer.run()
        
        except KeyboardInterrupt:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('⚠️  Stopping consumer...'))
            
        except Exception as e:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))
            logger.error(f"Fatal error in Kafka consumer: {e}", exc_info=True)
            raise
        
        finally:
            self.stdout.write(self.style.SUCCESS('✅ Consumer stopped'))
            self.stdout.write(self.style.SUCCESS('=' * 80))
            
            # Print statistics
            self.stdout.write(self.style.SUCCESS('📊 Statistics:'))
            for topic, handler in handlers_map.items():
                if hasattr(handler, 'get_stats'):
                    stats = handler.get_stats()
                    self.stdout.write(f"  {topic}: {stats.get('messages_processed', 0)} messages processed")
            self.stdout.write(self.style.SUCCESS('=' * 80))
