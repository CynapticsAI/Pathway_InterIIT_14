import pathway as pw
import math
import pandas as pd
from datetime import datetime

# --- CONFIG ---
RDKAFKA_SETTINGS = {
    "bootstrap.servers": "kafka:9092",
    "group.id": "scorer_group",
    "session.timeout.ms": "6000",
    "auto.offset.reset": "earliest"
}

class TickInputSchema(pw.Schema):
    s: str
    p: float
    t: int
    v: float
    r: float

@pw.udf
def calculate_sigmoid(z):
    if z is None: return 0.5
    z = max(min(z, 10), -10)
    return 1 / (1 + math.exp(-z))

@pw.udf
def calculate_z_score(current_val, mean_val, mean_sq_val):
    if mean_val is None or mean_sq_val is None: return 0.0
    variance = mean_sq_val - (mean_val ** 2)
    if variance <= 1e-9: return 0.0
    return (current_val - mean_val) / math.sqrt(variance)

def main():
    print("🚀 Starting Scorer...", flush=True)
    
    ticks = pw.io.kafka.read(
        RDKAFKA_SETTINGS,
        topic="stock_data",
        schema=TickInputSchema,
        format="json",
        autocommit_duration_ms=1000
    )
    
    # Process for Time-Series Analysis
    processed = ticks.select(
        symbol=ticks.s,
        price=ticks.p,
        return_val=ticks.r,
        timestamp=ticks.t.dt.utc_from_timestamp("ms"),
        raw_ts=ticks.t
    )
    
    # Rolling Statistics Window (1 Day lookback)
    # Using 1-day duration because we are simulating a full year quickly
    stats = processed.windowby(
        processed.timestamp,
        window=pw.temporal.sliding(hop=pw.Duration("1h"), duration=pw.Duration("1d")),
        instance=processed.symbol
    ).reduce(
        symbol=pw.this._pw_instance,
        latest_price=pw.reducers.latest(pw.this.price),
        current_return=pw.reducers.latest(pw.this.return_val),
        mean_r=pw.reducers.avg(pw.this.return_val),
        mean_r_sq=pw.reducers.avg(pw.this.return_val * pw.this.return_val),
        timestamp=pw.reducers.max(pw.this.timestamp),
        raw_ts=pw.reducers.max(pw.this.raw_ts)
    )
    
    scored = stats.select(
        symbol=pw.this.symbol,
        latest_price=pw.this.latest_price,
        timestamp=pw.this.timestamp,
        t=pw.this.raw_ts,
        z_score=calculate_z_score(pw.this.current_return, pw.this.mean_r, pw.this.mean_r_sq)
    )
    
    final_output = scored.select(
        symbol=pw.this.symbol,
        stock_score=calculate_sigmoid(pw.this.z_score),
        latest_price=pw.this.latest_price,
        timestamp=pw.this.timestamp
    )
    
    pw.io.kafka.write(final_output, RDKAFKA_SETTINGS, topic_name="stock_scores", format="json")
    pw.run()

if __name__ == "__main__":
    main()