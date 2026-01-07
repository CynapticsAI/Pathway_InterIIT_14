import json
import time
import random
from kafka import KafkaProducer
from datetime import datetime, timezone
import csv

KAFKA_BROKER = "kafka:9092"
TOPIC_NAME = "tweets"
USER_IDS = ["user-a", "user-b", "user-c", "user-d", "user-e"]
PRODUCTS = ["Laptop", "Mouse", "Keyboard", "Monitor", "Webcam"]

print("Waiting for Kafka to be ready...", flush=True)
time.sleep(15) 

print("Initializing Kafka Producer...", flush=True)
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    api_version=(2, 5, 0)
)

print(f"Producer started. Sending messages to topic: '{TOPIC_NAME}'...", flush=True)

csvFilePath = "/app/stock_tweets_sorted.csv"

def parse_time(ts):
    return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S%z")

# Read data from CSV and send to Kafka topic
try:
    with open(csvFilePath) as file:

        reader = list(csv.DictReader(file)) 
        totalrows = len(open(csvFilePath).readlines())
        for i,row in enumerate(reader): 
            tweet = {
                "Date": row["Date"],
                "Tweet": row["Tweet"],
                "Company_Name": row["Company_Name"],
                }        
            producer.send(TOPIC_NAME, value=tweet)
            print(f"Sent: {tweet}", flush=True)

            time.sleep(2.5)
            # #uncomment above and remove below to constant delays
            # # simulate real delays
            # if i + 1 < totalrows:
            #     t1 = parse_time(row["Date"])
            #     t2 = parse_time(reader[i + 1]["Date"])
            #     delta = (t2 - t1).total_seconds()
            #     if delta > 0:
            #         time.sleep(delta)

except KeyboardInterrupt:
    print("\nStopping finnhub_producer...", flush=True)
finally:
    producer.flush()
    producer.close()

