"""
Kafka News & Volume Spike Simulator
Publishes test messages to Kafka topics for testing the frontend notifications
"""

import json
import time
from datetime import datetime
from confluent_kafka import Producer

# Kafka configuration
KAFKA_BROKER = 'localhost:9092'
NEWS_TOPIC = 'news_data'
VOLUME_TOPIC = 'volume_volatility_data'

# Initialize producer
producer = Producer({
    'bootstrap.servers': KAFKA_BROKER,
    'client.id': 'test-news-simulator'
})

def delivery_report(err, msg):
    """Callback for message delivery reports"""
    if err is not None:
        print(f'   ❌ Message delivery failed: {err}')
    else:
        print(f'   ✅ Published to topic: {msg.topic()}')

# Sample news data
SAMPLE_NEWS = [
    {
        "dt_utc": datetime.utcnow().isoformat() + "+00:00",
        "ticker": "NVDA",
        "source": "(Reuters)",
        "title": "NVIDIA Announces New AI Chip with 50% Performance Boost",
        "url": "https://finance.yahoo.com/news/nvidia-ai-chip-breakthrough",
        "diff": 1,
        "time": int(time.time() * 1000)
    },
    {
        "dt_utc": datetime.utcnow().isoformat() + "+00:00",
        "ticker": "AAPL",
        "source": "(Bloomberg)",
        "title": "Apple Stock Surges on Strong iPhone Sales Report",
        "url": "https://finance.yahoo.com/news/apple-iphone-sales-surge",
        "diff": 1,
        "time": int(time.time() * 1000)
    },
    {
        "dt_utc": datetime.utcnow().isoformat() + "+00:00",
        "ticker": "MSFT",
        "source": "(CNBC)",
        "title": "Microsoft Cloud Revenue Exceeds Wall Street Expectations",
        "url": "https://finance.yahoo.com/news/microsoft-cloud-revenue-beat",
        "diff": 1,
        "time": int(time.time() * 1000)
    },
    {
        "dt_utc": datetime.utcnow().isoformat() + "+00:00",
        "ticker": "GOOGL",
        "source": "(TechCrunch)",
        "title": "Google Unveils Revolutionary Quantum Computing Breakthrough",
        "url": "https://finance.yahoo.com/news/google-quantum-computing",
        "diff": 1,
        "time": int(time.time() * 1000)
    }
]

# Sample volume spike data
SAMPLE_VOLUME_SPIKES = [
    {
        "timestamp": datetime.utcnow().isoformat() + "+0000",
        "symbol": "NVDA",
        "current_close": 181.38,
        "current_volume": 15000000.0,
        "current_range": 0.0003,
        "volume_stats": [395.38, 407.75],
        "range_stats": [0.00015, 0.00016],
        "bar_count": 105,
        "avg_volume": 395.38,
        "std_volume": 407.75,
        "avg_range": 0.00015,
        "std_range": 0.00016,
        "volume_zscore": 3.5,  # HIGH
        "volatility_zscore": 2.8,
        "risk_level": "HIGH",
        "diff": 1,
        "time": int(time.time() * 1000)
    },
    {
        "timestamp": datetime.utcnow().isoformat() + "+0000",
        "symbol": "AAPL",
        "current_close": 195.25,
        "current_volume": 25000000.0,
        "current_range": 0.0005,
        "volume_stats": [400.0, 420.0],
        "range_stats": [0.00018, 0.00019],
        "bar_count": 110,
        "avg_volume": 400.0,
        "std_volume": 420.0,
        "avg_range": 0.00018,
        "std_range": 0.00019,
        "volume_zscore": 4.2,  # CRITICAL
        "volatility_zscore": 3.5,
        "risk_level": "CRITICAL",
        "diff": 1,
        "time": int(time.time() * 1000)
    },
    {
        "timestamp": datetime.utcnow().isoformat() + "+0000",
        "symbol": "MSFT",
        "current_close": 372.50,
        "current_volume": 8000000.0,
        "current_range": 0.0001,
        "volume_stats": [350.0, 360.0],
        "range_stats": [0.00012, 0.00013],
        "bar_count": 100,
        "avg_volume": 350.0,
        "std_volume": 360.0,
        "avg_range": 0.00012,
        "std_range": 0.00013,
        "volume_zscore": 1.5,  # MEDIUM
        "volatility_zscore": 1.2,
        "risk_level": "MEDIUM",
        "diff": 1,
        "time": int(time.time() * 1000)
    },
    {
        "timestamp": datetime.utcnow().isoformat() + "+0000",
        "symbol": "GOOGL",
        "current_close": 142.80,
        "current_volume": 5000000.0,
        "current_range": 0.00008,
        "volume_stats": [380.0, 390.0],
        "range_stats": [0.00014, 0.00015],
        "bar_count": 95,
        "avg_volume": 380.0,
        "std_volume": 390.0,
        "avg_range": 0.00014,
        "std_range": 0.00015,
        "volume_zscore": 0.3,  # LOW
        "volatility_zscore": -0.2,
        "risk_level": "LOW",
        "diff": 1,
        "time": int(time.time() * 1000)
    }
]

def publish_news():
    """Publish news messages one by one with delay"""
    print("\n🔔 Starting News Simulation...\n")
    
    for i, news in enumerate(SAMPLE_NEWS, 1):
        # Update timestamp to current time
        news["dt_utc"] = datetime.utcnow().isoformat() + "+00:00"
        news["time"] = int(time.time() * 1000)
        
        print(f"📰 Publishing News {i}/{len(SAMPLE_NEWS)}: {news['ticker']} - {news['title'][:50]}...")
        
        producer.produce(
            NEWS_TOPIC,
            value=json.dumps(news).encode('utf-8'),
            callback=delivery_report
        )
        producer.flush()
        
        print(f"   ⏰ Waiting 3 seconds before next...\n")
        
        time.sleep(3)  # Wait 3 seconds between news items

def publish_volume_spikes():
    """Publish volume spike messages one by one with delay"""
    print("\n📊 Starting Volume Spike Simulation...\n")
    
    for i, spike in enumerate(SAMPLE_VOLUME_SPIKES, 1):
        # Update timestamp to current time
        spike["timestamp"] = datetime.utcnow().isoformat() + "+0000"
        spike["time"] = int(time.time() * 1000)
        
        print(f"📊 Publishing Volume Spike {i}/{len(SAMPLE_VOLUME_SPIKES)}: {spike['symbol']} - Risk: {spike['risk_level']}")
        print(f"   💰 Price: ${spike['current_close']:.2f} | Volume: {spike['current_volume']:,.0f}")
        print(f"   📈 Volume Z-Score: {spike['volume_zscore']:.2f} | Volatility Z: {spike['volatility_zscore']:.2f}")
        
        producer.produce(
            VOLUME_TOPIC,
            value=json.dumps(spike).encode('utf-8'),
            callback=delivery_report
        )
        producer.flush()
        
        print(f"   ⏰ Waiting 3 seconds before next...\n")
        
        time.sleep(3)  # Wait 3 seconds between volume spikes

def publish_continuous():
    """Publish messages continuously (alternating between news and volume)"""
    print("\n🔄 Starting Continuous Simulation (Ctrl+C to stop)...\n")
    
    news_idx = 0
    volume_idx = 0
    
    try:
        while True:
            # Publish news
            news = SAMPLE_NEWS[news_idx % len(SAMPLE_NEWS)].copy()
            news["dt_utc"] = datetime.utcnow().isoformat() + "+00:00"
            news["time"] = int(time.time() * 1000)
            
            print(f"📰 [{datetime.now().strftime('%H:%M:%S')}] Publishing News: {news['ticker']} - {news['title'][:40]}...")
            producer.produce(
                NEWS_TOPIC,
                value=json.dumps(news).encode('utf-8'),
                callback=delivery_report
            )
            producer.flush()
            
            time.sleep(5)
            
            # Publish volume spike
            spike = SAMPLE_VOLUME_SPIKES[volume_idx % len(SAMPLE_VOLUME_SPIKES)].copy()
            spike["timestamp"] = datetime.utcnow().isoformat() + "+0000"
            spike["time"] = int(time.time() * 1000)
            
            print(f"📊 [{datetime.now().strftime('%H:%M:%S')}] Publishing Volume Spike: {spike['symbol']} - Risk: {spike['risk_level']}")
            producer.produce(
                VOLUME_TOPIC,
                value=json.dumps(spike).encode('utf-8'),
                callback=delivery_report
            )
            producer.flush()
            
            news_idx += 1
            volume_idx += 1
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Simulation stopped by user")

def main():
    print("=" * 60)
    print("📡 Kafka News & Volume Spike Simulator")
    print("=" * 60)
    print(f"\nKafka Broker: {KAFKA_BROKER}")
    print(f"News Topic: {NEWS_TOPIC}")
    print(f"Volume Topic: {VOLUME_TOPIC}\n")
    
    print("Choose simulation mode:")
    print("1. Publish all news items (one-time)")
    print("2. Publish all volume spikes (one-time)")
    print("3. Publish both (one-time)")
    print("4. Continuous simulation (alternating)")
    print("5. Exit")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    try:
        if choice == "1":
            publish_news()
        elif choice == "2":
            publish_volume_spikes()
        elif choice == "3":
            publish_news()
            time.sleep(2)
            publish_volume_spikes()
        elif choice == "4":
            publish_continuous()
        elif choice == "5":
            print("👋 Goodbye!")
            return
        else:
            print("❌ Invalid choice. Please run again and select 1-5.")
            return
        
        print("\n" + "=" * 60)
        print("✅ Simulation Complete!")
        print("=" * 60)
        print("\n💡 Check your frontend for notifications!")
        print("   - News: Blue notifications with article links")
        print("   - Volume: Color-coded by risk level")
        print("   - Auto-dismiss after 5 seconds")
        print("   - Click X to dismiss manually\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("  1. Kafka is running (docker-compose up kafka)")
        print("  2. Topics exist (or auto-create is enabled)")
        print("  3. Kafka is accessible on localhost:9092\n")
    finally:
        producer.close()

if __name__ == "__main__":
    main()
