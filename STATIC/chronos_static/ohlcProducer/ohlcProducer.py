import json
import time
import random
from kafka import KafkaProducer
import csv


KAFKA_BROKER = "kafka:9092"
TOPIC_NAME = "ohlc"
print("Waiting for Kafka to be ready...", flush=True)
time.sleep(15) 

print("Initializing Kafka Producer...", flush=True)
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    api_version=(2, 5, 0)
)

print(f"Producer started. Sending messages to topic: '{TOPIC_NAME}'...", flush=True)

csvFilePath = "/app/max_movement_2d_span.csv"

# Read data from CSV and send to Kafka topic
try:
    with open(csvFilePath) as file:
        reader = csv.DictReader(file)
        for i,row in enumerate(reader): 
            ohlc = {
                "timestamp": row["timestamp"],
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
                }        
            producer.send(TOPIC_NAME, value=ohlc)
            print(f"Sent: {ohlc}", flush=True)
            time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping finnhub_producer...", flush=True)
finally:
    producer.flush()
    producer.close()

