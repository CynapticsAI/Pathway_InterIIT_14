import pathway as pw
import logging
from signals.signals.spike_detector import get_ohlc_agg
logging.basicConfig(level= logging.INFO)

def main(kafka_settings : dict, kafka_topic: str, postgres_settings : dict, pg_table: str):


    class InputSchema(pw.Schema):
        timestamp: pw.DateTimeNaive
        symbol: str
        current_close: float
        current_volume: float
        avg_volume: float
        volume_zscore: float
        current_range: float
        avg_range: float
        volatility_zscore: float


    get_ohlc_agg(kafka_settings, kafka_topic_output = kafka_topic)    
    t = pw.io.kafka.read(
        kafka_settings,
        kafka_topic,
        schema= InputSchema,
        format = 'json'
    )

    t = t.groupby(t.symbol).reduce(
        timestamp          = pw.reducers.latest(t.timestamp),
        symbol             = pw.reducers.latest(t.symbol),
        current_close      = pw.reducers.latest(t.current_close),
        current_volume     = pw.reducers.latest(t.current_volume),
        avg_volume         = pw.reducers.latest(t.avg_volume),
        volume_zscore      = pw.reducers.latest(t.volume_zscore),
        current_range      = pw.reducers.latest(t.current_range),
        avg_range          = pw.reducers.latest(t.avg_range),
        volatility_zscore  = pw.reducers.latest(t.volatility_zscore),
    )

    pw.io.postgres.write(
        t,
        postgres_settings,
        pg_table,
        primary_key= [t.symbol],
        output_table_type= 'snapshot'
    )

    class pathwayLogger(pw.io.python.ConnectorObserver):
        def on_change(self, key, row, time: int, is_addition: bool) -> None:
            logging.warning(f"{row}")
        
    pw.io.python.write(
        t,
        pathwayLogger()
    )


if __name__ == "__main__":
    with open('app.yaml', 'r') as f:
        data = pw.load_yaml(f)
    
    kafka_settings = {
        "bootstrap.servers": "13.50.238.243:29092",
        "group.id" : "random_topic",
        "session.timeout.ms": "6000"
    }

    postgres_settings = {
    "host": "postgres",
    "port": 5432,
    "dbname": "pg_db",
    "user": "postgres",
    "password": "pass"
    }

    kafka_topic = {
        "kafka_topic": "ohlcv"
    }

    pg_table = {
        "pg_table": "ohlc_bars"
    }

    main(kafka_settings= kafka_settings, kafka_topic = 'ohlcv', postgres_settings= postgres_settings, pg_table= 'ohlc_bars')
    pw.run()