"""
Test script to verify Kafka consumer setup
Run: python manage.py shell < kafka_consumer/tests/test_setup.py
"""
import os
import sys
from django.conf import settings

print("=" * 80)
print("🧪 Testing Kafka Consumer Setup")
print("=" * 80)

# Test 1: Check if app is installed
print("\n1️⃣ Checking if kafka_consumer app is installed...")
if 'kafka_consumer' in settings.INSTALLED_APPS:
    print("   ✅ kafka_consumer is in INSTALLED_APPS")
else:
    print("   ❌ kafka_consumer is NOT in INSTALLED_APPS")
    sys.exit(1)

# Test 2: Check Kafka configuration
print("\n2️⃣ Checking Kafka configuration...")
kafka_config = getattr(settings, 'KAFKA_CONFIG', None)
if kafka_config:
    print("   ✅ KAFKA_CONFIG found in settings")
    print(f"   - Bootstrap servers: {kafka_config.get('bootstrap_servers')}")
    print(f"   - Group ID: {kafka_config.get('group_id')}")
else:
    print("   ❌ KAFKA_CONFIG not found in settings")
    sys.exit(1)

# Test 3: Check Kafka topics
print("\n3️⃣ Checking Kafka topics configuration...")
kafka_topics = getattr(settings, 'KAFKA_TOPICS', None)
if kafka_topics:
    print("   ✅ KAFKA_TOPICS found in settings")
    for name, topic in kafka_topics.items():
        print(f"   - {name}: {topic}")
else:
    print("   ❌ KAFKA_TOPICS not found in settings")
    sys.exit(1)

# Test 4: Check if consumer module can be imported
print("\n4️⃣ Testing imports...")
try:
    from kafka_consumer.consumers import BaseKafkaConsumer
    print("   ✅ BaseKafkaConsumer imported successfully")
except ImportError as e:
    print(f"   ❌ Failed to import BaseKafkaConsumer: {e}")
    sys.exit(1)

try:
    from kafka_consumer.handlers import MarketBreadthHandler
    print("   ✅ MarketBreadthHandler imported successfully")
except ImportError as e:
    print(f"   ❌ Failed to import MarketBreadthHandler: {e}")
    sys.exit(1)

# Test 5: Check management command
print("\n5️⃣ Checking management command...")
from django.core.management import get_commands
commands = get_commands()
if 'consume_kafka' in commands:
    print("   ✅ consume_kafka management command is available")
else:
    print("   ❌ consume_kafka management command not found")
    sys.exit(1)

# Test 6: Check logs directory
print("\n6️⃣ Checking logs directory...")
logs_dir = settings.BASE_DIR / 'logs'
if logs_dir.exists():
    print(f"   ✅ Logs directory exists: {logs_dir}")
else:
    print(f"   ⚠️  Logs directory doesn't exist: {logs_dir}")
    print("   Creating logs directory...")
    logs_dir.mkdir(exist_ok=True)
    print("   ✅ Created logs directory")

# Test 7: Try to create handler instance
print("\n7️⃣ Testing handler instantiation...")
try:
    handler = MarketBreadthHandler()
    print("   ✅ MarketBreadthHandler instantiated successfully")
    stats = handler.get_stats()
    print(f"   - Initial stats: {stats}")
except Exception as e:
    print(f"   ❌ Failed to instantiate handler: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ All tests passed! Kafka consumer setup is complete.")
print("=" * 80)
print("\n📝 Next steps:")
print("1. Install dependencies: pip install -r requirements.txt")
print("2. Ensure Kafka is running on localhost:9092")
print("3. Start the consumer: python manage.py consume_kafka")
print("=" * 80)
