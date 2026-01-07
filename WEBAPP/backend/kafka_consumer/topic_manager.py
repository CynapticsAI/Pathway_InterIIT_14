"""
Kafka Topic Management Utility
Automatically creates required topics if they don't exist
"""

import logging
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka import KafkaException
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class KafkaTopicManager:
    """Manages Kafka topic creation and validation"""
    
    def __init__(self, bootstrap_servers: str = 'localhost:9092'):
        """
        Initialize Kafka Topic Manager
        
        Args:
            bootstrap_servers: Kafka broker address
        """
        self.bootstrap_servers = bootstrap_servers
        self.admin_client = AdminClient({
            'bootstrap.servers': bootstrap_servers
        })
        
    def list_topics(self) -> List[str]:
        """
        List all existing topics
        
        Returns:
            List of topic names
        """
        try:
            metadata = self.admin_client.list_topics(timeout=10)
            return list(metadata.topics.keys())
        except Exception as e:
            logger.error(f"Failed to list topics: {e}")
            return []
    
    def topic_exists(self, topic_name: str) -> bool:
        """
        Check if a topic exists
        
        Args:
            topic_name: Name of the topic to check
            
        Returns:
            True if topic exists, False otherwise
        """
        topics = self.list_topics()
        return topic_name in topics
    
    def create_topic(
        self, 
        topic_name: str, 
        num_partitions: int = 1, 
        replication_factor: int = 1,
        config: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Create a single topic
        
        Args:
            topic_name: Name of the topic to create
            num_partitions: Number of partitions (default: 1)
            replication_factor: Replication factor (default: 1)
            config: Additional topic configuration
            
        Returns:
            True if created successfully, False otherwise
        """
        if self.topic_exists(topic_name):
            logger.info(f"Topic '{topic_name}' already exists")
            return True
        
        try:
            new_topic = NewTopic(
                topic=topic_name,
                num_partitions=num_partitions,
                replication_factor=replication_factor,
                config=config or {}
            )
            
            # Create topic
            fs = self.admin_client.create_topics([new_topic])
            
            # Wait for operation to complete
            for topic, f in fs.items():
                try:
                    f.result()  # The result itself is None
                    logger.info(f"✅ Created topic '{topic}'")
                    return True
                except KafkaException as e:
                    if e.args[0].code() == 36:  # TOPIC_ALREADY_EXISTS
                        logger.info(f"Topic '{topic}' already exists")
                        return True
                    else:
                        logger.error(f"❌ Failed to create topic '{topic}': {e}")
                        return False
        except Exception as e:
            logger.error(f"❌ Error creating topic '{topic_name}': {e}")
            return False
    
    def create_topics(self, topics: List[Dict[str, any]]) -> Dict[str, bool]:
        """
        Create multiple topics
        
        Args:
            topics: List of topic configurations, each containing:
                - name: Topic name (required)
                - num_partitions: Number of partitions (optional, default: 1)
                - replication_factor: Replication factor (optional, default: 1)
                - config: Additional config (optional)
                
        Returns:
            Dictionary mapping topic names to creation success status
        """
        results = {}
        
        for topic_config in topics:
            topic_name = topic_config.get('name')
            if not topic_name:
                logger.warning("Topic configuration missing 'name' field")
                continue
                
            num_partitions = topic_config.get('num_partitions', 1)
            replication_factor = topic_config.get('replication_factor', 1)
            config = topic_config.get('config', {})
            
            success = self.create_topic(
                topic_name=topic_name,
                num_partitions=num_partitions,
                replication_factor=replication_factor,
                config=config
            )
            results[topic_name] = success
            
        return results
    
    def ensure_topics_exist(self, topic_names: List[str]) -> bool:
        """
        Ensure all specified topics exist, create them if they don't
        
        Args:
            topic_names: List of topic names to ensure
            
        Returns:
            True if all topics exist or were created successfully
        """
        all_success = True
        
        for topic_name in topic_names:
            if not self.create_topic(topic_name):
                all_success = False
                
        return all_success
    
    def delete_topic(self, topic_name: str) -> bool:
        """
        Delete a topic
        
        Args:
            topic_name: Name of the topic to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            fs = self.admin_client.delete_topics([topic_name], operation_timeout=30)
            
            for topic, f in fs.items():
                try:
                    f.result()
                    logger.info(f"✅ Deleted topic '{topic}'")
                    return True
                except Exception as e:
                    logger.error(f"❌ Failed to delete topic '{topic}': {e}")
                    return False
        except Exception as e:
            logger.error(f"❌ Error deleting topic '{topic_name}': {e}")
            return False


def get_default_topics() -> List[Dict[str, any]]:
    """
    Get default topic configurations for the application
    
    Returns:
        List of topic configurations
    """
    return [
        {
            'name': 'market_breadth',
            'num_partitions': 1,
            'replication_factor': 1,
            'config': {
                'retention.ms': '604800000',  # 7 days
                'cleanup.policy': 'delete'
            }
        },
        {
            'name': 'stock_data',
            'num_partitions': 3,  # More partitions for higher throughput
            'replication_factor': 1,
            'config': {
                'retention.ms': '604800000',
                'cleanup.policy': 'delete'
            }
        },
        {
            'name': 'sarimax_forecast',
            'num_partitions': 1,
            'replication_factor': 1,
            'config': {
                'retention.ms': '604800000',
                'cleanup.policy': 'delete'
            }
        },
        {
            'name': 'news_data',
            'num_partitions': 2,
            'replication_factor': 1,
            'config': {
                'retention.ms': '2592000000',  # 30 days for news
                'cleanup.policy': 'delete'
            }
        },
        {
            'name': 'volume_volatility_data',
            'num_partitions': 1,
            'replication_factor': 1,
            'config': {
                'retention.ms': '604800000',
                'cleanup.policy': 'delete'
            }
        },
        {
            'name': 'pnl',
            'num_partitions': 1,
            'replication_factor': 1,
            'config': {
                'retention.ms': '2592000000',  # 30 days for P&L
                'cleanup.policy': 'delete'
            }
        }
    ]


def setup_kafka_topics(bootstrap_servers: str = 'localhost:9092') -> bool:
    """
    Setup all required Kafka topics
    
    Args:
        bootstrap_servers: Kafka broker address
        
    Returns:
        True if all topics were created successfully
    """
    logger.info("🔧 Setting up Kafka topics...")
    
    try:
        manager = KafkaTopicManager(bootstrap_servers)
        topics = get_default_topics()
        
        results = manager.create_topics(topics)
        
        all_success = all(results.values())
        
        if all_success:
            logger.info("✅ All Kafka topics are ready")
        else:
            failed = [name for name, success in results.items() if not success]
            logger.warning(f"⚠️  Some topics failed to create: {failed}")
            
        return all_success
        
    except Exception as e:
        logger.error(f"❌ Failed to setup Kafka topics: {e}")
        return False


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s %(asctime)s %(name)s %(message)s'
    )
    
    # Run setup
    success = setup_kafka_topics()
    
    if success:
        print("\n✅ Kafka topics setup completed successfully!")
    else:
        print("\n❌ Kafka topics setup failed!")
        exit(1)
