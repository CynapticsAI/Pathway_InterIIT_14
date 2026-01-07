"""
Kafka Consumer Utilities
Helper functions for Kafka operations.
"""
import logging
from typing import Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger('kafka_consumer')


def get_kafka_config(override: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get Kafka configuration from Django settings.
    
    Args:
        override: Optional dictionary to override default settings
        
    Returns:
        Dictionary with Kafka configuration
    """
    config = getattr(settings, 'KAFKA_CONFIG', {}).copy()
    
    if override:
        config.update(override)
    
    return config


def get_kafka_topics() -> Dict[str, str]:
    """
    Get configured Kafka topics from Django settings.
    
    Returns:
        Dictionary mapping topic names to topic identifiers
    """
    return getattr(settings, 'KAFKA_TOPICS', {})


def validate_kafka_connection(bootstrap_servers: str) -> bool:
    """
    Validate connection to Kafka broker.
    
    Args:
        bootstrap_servers: Kafka bootstrap servers string
        
    Returns:
        True if connection successful, False otherwise
    """
    try:
        from confluent_kafka.admin import AdminClient
        
        admin_client = AdminClient({'bootstrap.servers': bootstrap_servers})
        metadata = admin_client.list_topics(timeout=5)
        
        logger.info(f"Successfully connected to Kafka broker: {bootstrap_servers}")
        logger.info(f"Available topics: {list(metadata.topics.keys())}")
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to connect to Kafka broker: {e}")
        return False


def format_message_log(message_info: Dict[str, Any]) -> str:
    """
    Format message information for logging.
    
    Args:
        message_info: Dictionary with message details
        
    Returns:
        Formatted string for logging
    """
    return (
        f"Topic: {message_info.get('topic')} | "
        f"Partition: {message_info.get('partition')} | "
        f"Offset: {message_info.get('offset')} | "
        f"Key: {message_info.get('key')}"
    )
