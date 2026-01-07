import pathway as pw

class TickInputSchema(pw.Schema):
    s: str
    p: float
    t: int
    v: float# Volume

ticks = pw.io.kafka.read(
        rdkafka_settings={
            "bootstrap.servers": "0.0.0.0:9092",
            "group.id": "stock_analyzer_ticks",
            "session.timeout.ms": "6000",
        },
        topic="stock_data",
        schema=TickInputSchema,
        format="json",
        autocommit_duration_ms=1000,
    )

pw.io.jsonlines.write(table = ticks, filename = './tmp-out.jsonl')

pw.run()
