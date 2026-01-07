import pathway as pw
import time
print("Waiting for Kafka to be ready...", flush=True)
time.sleep(20)

class StockAggregates(pw.Schema):
    s: str
    p: float
    t: int 
    v: float  

TOPIC_NAME = "stock_data"

rdkafka_settings = {
    "bootstrap.servers": "kafka:9090",
    "group.id": "pathway_consumer_group",
    "session.timeout.ms": "6000",
}

print("Starting Pathway Kafka consumer...", flush=True)

stocks_stream = pw.io.kafka.read(
    rdkafka_settings=rdkafka_settings,
    topic=TOPIC_NAME,
    schema=StockAggregates,
    format="json",
    autocommit_duration_ms=1000
)
fmt = "%Y-%m-%dT%H:%M:%S.%f"
#stocks_stream = stocks_stream.with_columns(t = stocks_stream.t.dt.strptime(fmt=fmt))

output_path = "/app/output/highValue.jsonl"

pw.io.jsonlines.write(stocks_stream, output_path)

pw.run()

