import json
import time
import random
from kafka import KafkaProducer
from datetime import datetime, timezone
import csv

KAFKA_BROKER = "kafka:9092"
TOPIC_NAME = "reddit"

print("Waiting for Kafka to be ready...", flush=True)
time.sleep(15) 

print("Initializing Kafka Producer...", flush=True)
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    api_version=(2, 5, 0)
)

print(f"Producer started. Sending messages to topic: '{TOPIC_NAME}'...", flush=True)

csvFilePath = "reddit_tesla.csv"

def parse_time(ts):
    return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S%z")

# Read data from CSV and send to Kafka topic
try:
    with open(csvFilePath) as file:

        reader = list(csv.DictReader(file)) 
        totalrows = len(open(csvFilePath).readlines())
        for i,row in enumerate(reader): 
            post = {
                "Date": row["created"],
                "Post": row["selftext"],
                }        
            producer.send(TOPIC_NAME, value=post)
            print(f"Sent: {post}", flush=True)

            time.sleep(2.5)
            #uncomment above and remove below to constant delays
            # simulate real delays
            # if i + 1 < totalrows:
            #     t1 = parse_time(row["Date"])
            #     t2 = parse_time(reader[i + 1]["Date"])
            #     delta = (t2 - t1).total_seconds()
            #     if delta > 0:
            #         time.sleep(delta)

except KeyboardInterrupt:
    print("\nStopping producer...", flush=True)
finally:
    producer.flush()
    producer.close()

