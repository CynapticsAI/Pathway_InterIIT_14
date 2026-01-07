#!/usr/bin/env python
"""
Simple script to test Kafka connection.
Run this to verify your remote Kafka broker is accessible.
"""
import sys
from confluent_kafka.admin import AdminClient
from confluent_kafka import KafkaException

def test_kafka_connection(bootstrap_servers):
    """Test connection to Kafka broker."""
    print(f"Testing connection to Kafka broker: {bootstrap_servers}")
    print("-" * 60)
    
    # Create admin client with extended timeout
    admin_config = {
        'bootstrap.servers': bootstrap_servers,
        'socket.timeout.ms': 60000,
        'api.version.request.timeout.ms': 10000,
    }
    
    try:
        admin_client = AdminClient(admin_config)
        print("✓ Admin client created successfully")
        
        # Try to get cluster metadata
        print("Fetching cluster metadata...")
        metadata = admin_client.list_topics(timeout=10)
        
        print("\n✅ Successfully connected to Kafka!")
        print(f"Cluster ID: {metadata.cluster_id}")
        print(f"Controller ID: {metadata.controller_id}")
        print(f"\nBrokers ({len(metadata.brokers)}):")
        for broker_id, broker in metadata.brokers.items():
            print(f"  - Broker {broker_id}: {broker.host}:{broker.port}")
        
        print(f"\nAvailable Topics ({len(metadata.topics)}):")
        for topic_name, topic in metadata.topics.items():
            if not topic_name.startswith('__'):  # Skip internal topics
                print(f"  - {topic_name} ({len(topic.partitions)} partitions)")
        
        return True
        
    except KafkaException as e:
        print(f"\n❌ Kafka Error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        print("\nPossible issues:")
        print("1. Firewall blocking port 9092")
        print("2. Kafka broker not running or not accessible")
        print("3. Network connectivity issues")
        print("4. Security configuration required (SASL/SSL)")
        return False

if __name__ == "__main__":
    # Use command line argument or default
    if len(sys.argv) > 1:
        broker = sys.argv[1]
    else:
        broker = "13.51.109.135:9092"
    
    success = test_kafka_connection(broker)
    sys.exit(0 if success else 1)
