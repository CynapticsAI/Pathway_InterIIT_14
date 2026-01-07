"""
Base Kafka Consumer Class
Provides generic Kafka consumer functionality with error handling and logging.
"""
import logging
import json
import signal
import sys
from typing import Dict, List, Callable, Optional
from confluent_kafka import Consumer, KafkaError, KafkaException
from django.conf import settings
import base64

logger = logging.getLogger(__name__)


def _safe_decode(raw: Optional[bytes]) -> Optional[str]:
    """Decode bytes to string safely.

    Tries UTF-8 first, falls back to latin-1, and if that fails returns a
    base64-encoded representation prefixed with 'BASE64:'.

    Returns None if input is None.
    """
    if raw is None:
        return None
    if isinstance(raw, str):
        return raw
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError:
        try:
            decoded = raw.decode('latin-1')
            logger.debug("Decoded message using latin-1 fallback")
            return decoded
        except Exception:
            # As a last resort, return a base64 representation so the
            # consumer can still log/inspect the payload without crashing.
            try:
                b64 = base64.b64encode(raw).decode('ascii')
                logger.debug("Returning base64-encoded fallback for non-text payload")
                return f"BASE64:{b64}"
            except Exception:
                # Give up and return a placeholder
                logger.debug("Failed to represent message payload; returning '<binary>'")
                return '<binary>'


class BaseKafkaConsumer:
    """
    Base class for Kafka consumers with common functionality.
    """
    
    def __init__(self, topics: List[str], handler: Callable, group_id: Optional[str] = None):
        """
        Initialize the Kafka consumer.
        
        Args:
            topics: List of Kafka topics to subscribe to
            handler: Callable function to process messages
            group_id: Consumer group ID (optional, uses default from settings)
        """
        self.topics = topics
        self.handler = handler
        self.running = True
        
        # Get Kafka configuration from Django settings
        kafka_config = getattr(settings, 'KAFKA_CONFIG', {})
        
        # Handle bootstrap_servers - can be a list or a string
        bootstrap_servers = kafka_config.get('bootstrap_servers', ['localhost:9092'])
        if isinstance(bootstrap_servers, list):
            bootstrap_servers_str = ','.join(bootstrap_servers)
        else:
            bootstrap_servers_str = bootstrap_servers
        
        # Build consumer configuration
        self.config = {
            'bootstrap.servers': bootstrap_servers_str,
            'group.id': group_id or kafka_config.get('group_id', 'django-backend-consumer'),
            'auto.offset.reset': kafka_config.get('auto_offset_reset', 'earliest'),
            'enable.auto.commit': kafka_config.get('enable_auto_commit', True),
            'session.timeout.ms': kafka_config.get('session_timeout_ms', 45000),
            'heartbeat.interval.ms': kafka_config.get('heartbeat_interval_ms', 3000),
            'max.poll.interval.ms': kafka_config.get('max_poll_interval_ms', 300000),
            'socket.timeout.ms': kafka_config.get('socket_timeout_ms', 60000),
            'connections.max.idle.ms': kafka_config.get('connections_max_idle_ms', 540000),
            'metadata.max.age.ms': kafka_config.get('metadata_max_age_ms', 300000),
        }
        
        # Add security settings if configured
        if kafka_config.get('security_protocol'):
            self.config['security.protocol'] = kafka_config.get('security_protocol')
        if kafka_config.get('sasl_mechanism'):
            self.config['sasl.mechanism'] = kafka_config.get('sasl_mechanism')
        if kafka_config.get('sasl_username'):
            self.config['sasl.username'] = kafka_config.get('sasl_username')
        if kafka_config.get('sasl_password'):
            self.config['sasl.password'] = kafka_config.get('sasl_password')
        
        # Initialize consumer
        self.consumer = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"BaseKafkaConsumer initialized for topics: {topics}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}. Shutting down gracefully...")
        self.running = False
    
    def connect(self):
        """Establish connection to Kafka and subscribe to topics."""
        try:
            self.consumer = Consumer(self.config)
            self.consumer.subscribe(self.topics)
            logger.info(f"Successfully connected to Kafka and subscribed to topics: {self.topics}")
            logger.info(f"Consumer group: {self.config['group.id']}")
            logger.info(f"Bootstrap servers: {self.config['bootstrap.servers']}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise
    
    def consume(self):
        """
        Main consume loop - polls for messages and processes them.
        """
        if not self.consumer:
            raise RuntimeError("Consumer not connected. Call connect() first.")
        
        logger.info("Starting message consumption loop...")
        message_count = 0
        
        try:
            while self.running:
                # Poll for messages (timeout in seconds)
                msg = self.consumer.poll(timeout=1.0)
                
                if msg is None:
                    # No message received within timeout
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition - not an error
                        logger.debug(f"Reached end of partition {msg.partition()} at offset {msg.offset()}")
                    else:
                        # Real error
                        logger.error(f"Consumer error: {msg.error()}")
                        raise KafkaException(msg.error())
                else:
                    # Successfully received a message
                    message_count += 1
                    self._process_message(msg)
                    
                    # Log progress every 100 messages
                    if message_count % 100 == 0:
                        logger.info(f"Processed {message_count} messages...")
        
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received. Shutting down...")
        
        except Exception as e:
            logger.error(f"Error in consume loop: {e}", exc_info=True)
            raise
        
        finally:
            self._close()
    
    def _process_message(self, msg):
        """
        Process a single message.
        
        Args:
            msg: Kafka message object
        """
        try:
            # Extract message details
            topic = msg.topic()
            partition = msg.partition()
            offset = msg.offset()
            key = _safe_decode(msg.key())
            value = _safe_decode(msg.value())
            
            # Log message receipt
            logger.debug(
                f"Received message - Topic: {topic}, "
                f"Partition: {partition}, Offset: {offset}, Key: {key}"
            )
            
            # Parse JSON if applicable
            try:
                if value:
                    data = json.loads(value)
                else:
                    data = None
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse message as JSON: {value}")
                data = value
            
            # Call the handler function
            message_info = {
                'topic': topic,
                'partition': partition,
                'offset': offset,
                'key': key,
                'value': value,
                'data': data,
                'timestamp': msg.timestamp()
            }
            
            self.handler(message_info)
        
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            # Continue processing other messages even if one fails
    
    def _close(self):
        """Close the consumer connection gracefully."""
        if self.consumer:
            logger.info("Closing Kafka consumer...")
            self.consumer.close()
            logger.info("Kafka consumer closed successfully")
    
    def run(self):
        """Convenience method to connect and start consuming."""
        self.connect()
        self.consume()
