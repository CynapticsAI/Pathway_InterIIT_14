"""
Kafka utilities for chat integration
Handles producing messages to 'orch' topic and receiving from 'finalResponse' topic
"""
import json
import uuid
import logging
from typing import Dict, Any, Optional
import time

try:
    from kafka import KafkaProducer
    from kafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logging.warning("kafka-python not installed. Install with: pip install kafka-python")

from django.conf import settings

logger = logging.getLogger(__name__)


class KafkaChatProducer:
    """
    Kafka producer for sending chat messages to 'orch' topic
    Singleton pattern to maintain single producer instance
    """
    _instance = None
    _producer = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KafkaChatProducer, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        if not KAFKA_AVAILABLE:
            logger.error("❌ kafka-python not available. Please install it.")
            self._initialized = True
            return
        
        self.bootstrap_servers = self._get_bootstrap_servers()
        self.orch_topic = 'chat'
        self._initialized = True
        # Try to connect on initialization
        self.connect()
    
    def _get_bootstrap_servers(self) -> list:
        """Get bootstrap servers from Django settings"""
        kafka_config = getattr(settings, 'KAFKA_CONFIG', {})
        servers = kafka_config.get('bootstrap_servers', ['localhost:9092'])
        
        # Handle both list and string formats
        if isinstance(servers, str):
            servers = [servers]
        
        return servers
    
    def connect(self) -> bool:
        """Initialize Kafka producer connection"""
        if not KAFKA_AVAILABLE:
            return False
            
        if self._producer is not None:
            return True
        
        try:
            self._producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if isinstance(k, str) else k,
                acks='all',  # Wait for all replicas
                retries=3,  # Retry failed sends
                max_in_flight_requests_per_connection=1,  # Ensure ordering
                request_timeout_ms=30000,
                api_version=(0, 10, 1)
            )
            logger.info(f"✅ Kafka Producer connected to: {self.bootstrap_servers}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect Kafka Producer: {e}")
            self._producer = None
            return False
    
    def is_connected(self) -> bool:
        """Check if producer is connected"""
        return self._producer is not None
    
    def send_chat_message(
        self,
        user_id: int,
        conversation_id: int,
        content: str,
        agent: str = "Market Analyzer",
        kafka_message_id: Optional[str] = None
    ) -> Optional[str]:
        """
    Send chat message to 'chat' topic
        
        Args:
            user_id: User ID
            conversation_id: Conversation ID
            content: Message content from user
            agent: Agent name (default: "Market Analyzer")
            kafka_message_id: Optional message ID for correlation (generated if not provided)
        
        Returns:
            kafka_message_id if successful, None otherwise
        """
        if not KAFKA_AVAILABLE:
            logger.error("❌ Kafka not available")
            return None
        
        if not self.is_connected():
            logger.warning("⚠️ Producer not connected. Attempting to reconnect...")
            if not self.connect():
                logger.error("❌ Failed to reconnect to Kafka")
                return None
        
        # Generate unique message ID if not provided
        if kafka_message_id is None:
            kafka_message_id = str(uuid.uuid4())
        
        # Construct payload matching the schema
        payload = {
            "user_id": str(user_id),
            "conversation_id": str(conversation_id),
            "messages": [
                {"role": "user", "content": content}
            ],
            "timestamp": int(time.time() * 1000),  # milliseconds
            "agent": agent,
            "kafka_message_id": kafka_message_id  # For correlation
        }
        
        try:
            # Send message with kafka_message_id as key for better partitioning
            future = self._producer.send(
                topic=self.orch_topic,
                value=payload,
                key=kafka_message_id
            )
            
            # Wait for confirmation (with timeout)
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"✅ Message sent to Kafka '{self.orch_topic}' - "
                f"Partition: {record_metadata.partition}, "
                f"Offset: {record_metadata.offset}, "
                f"MessageID: {kafka_message_id}"
            )
            
            return kafka_message_id
            
        except KafkaError as e:
            logger.error(f"❌ Kafka error while sending message: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error while sending message: {e}")
            return None
    
    def flush(self, timeout: int = 5):
        """Flush pending messages"""
        if self._producer:
            try:
                self._producer.flush(timeout=timeout)
                logger.info("✅ Producer flushed")
            except Exception as e:
                logger.error(f"❌ Error flushing producer: {e}")
    
    def close(self):
        """Close producer connection"""
        if self._producer:
            try:
                self._producer.flush()
                self._producer.close()
                self._producer = None
                logger.info("✅ Kafka Producer closed")
            except Exception as e:
                logger.error(f"❌ Error closing producer: {e}")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()


# Singleton instance for global use
chat_producer = KafkaChatProducer()


def get_chat_producer() -> KafkaChatProducer:
    """
    Get the global chat producer instance
    
    Returns:
        KafkaChatProducer singleton instance
    """
    return chat_producer


def send_message_to_kafka(
    user_id: int,
    conversation_id: int,
    content: str,
    agent: str = "Market Analyzer",
    kafka_message_id: Optional[str] = None
) -> Optional[str]:
    """
    Convenience function to send a message to Kafka
    
    Args:
        user_id: User ID
        conversation_id: Conversation ID
        content: Message content
        agent: Agent name
        kafka_message_id: Optional message ID for correlation
    
    Returns:
        kafka_message_id if successful, None otherwise
    """
    producer = get_chat_producer()
    return producer.send_chat_message(
        user_id=user_id,
        conversation_id=conversation_id,
        content=content,
        agent=agent,
        kafka_message_id=kafka_message_id
    )
