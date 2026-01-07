import pathway as pw
import math
import pandas as pd
import time
from datetime import datetime, timezone

# ---------------------------------------------------------
# 1. Schemas
# ---------------------------------------------------------
NEW_TIMEFRAME = "1m"

class TickInputSchema(pw.Schema):
    s: str
    p: float
    t: int
    v: float
    r: float  # Volume

class HeartbeatSchema(pw.Schema):
    s: str
    t: int

# ---------------------------------------------------------
# 2. Heartbeat Connector
# ---------------------------------------------------------
class HeartbeatSubject(pw.io.python.ConnectorSubject):
    def __init__(self, tickers):
        super().__init__()
        self.tickers = tickers

    def run(self):
        time.sleep(10)
        print(f"Starting Scorer Heartbeat for {len(self.tickers)} stocks...", flush=True)
        while True:
            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
            for ticker in self.tickers:
                self.next_json({"s": ticker, "t": now_ms})
            time.sleep(10)

# ---------------------------------------------------------
# 3. UDFs
# ---------------------------------------------------------
@pw.udf
def calculate_sigmoid(z):
    if z is None: return 0.5
    z = max(min(z, 10), -10)
    return 1 / (1 + math.exp(-z))

@pw.udf
def get_status(z):
    if z is None: return "initializing"
    if abs(z) >= 2.0: return "spike_detected"
    return "normal"

@pw.udf
def calculate_z_score(current_val, mean_val, mean_sq_val):
    if mean_val is None or mean_sq_val is None: return 0.0
    variance = mean_sq_val - (mean_val ** 2)
    if variance <= 1e-9: return 0.0
    return (current_val - mean_val) / math.sqrt(variance)

# ---------------------------------------------------------
# 4. Main Logic
# ---------------------------------------------------------
def main():
    print("Starting Scorer (Dual Stream Logic)...", flush=True)
    
    rdkafka_settings = {
        "bootstrap.servers": "kafka:9090",
        "group.id": "scorer_group_persistent",
        "session.timeout.ms": "6000",
        "auto.offset.reset": "earliest" 
    }

    # --- A. Load Stock List ---
    try:
        df = pd.read_csv("master_stock_list.csv")
        col = 'symbol' if 'symbol' in df.columns else df.columns[0]
        tickers = df[col].str.strip().unique().tolist()
        print(f"Scorer loaded {len(tickers)} tickers.", flush=True)
    except:
        tickers = ["TSLA", "AAPL", "MSFT", "NVDA", "JPM"]

    # --- B. Input Streams ---
    # 1. Real Data Stream (from raw ticks)
    ticks = pw.io.kafka.read(
        rdkafka_settings={
            "bootstrap.servers": "kafka:9090",
            "group.id": "stock_calculator_ticks_infer",
            "session.timeout.ms": "6000",
        },
        topic="stock_data",
        schema=TickInputSchema,
        format="json",
        autocommit_duration_ms=1000
    )
    
    ticks_processed = ticks.with_columns(
        symbol=ticks.s,
        timestamp=pw.this.t.dt.utc_from_timestamp("ms"),
        price=ticks.p,
        volume=ticks.v
    ).select(pw.this.symbol, pw.this.timestamp, pw.this.price, pw.this.volume)
    
    # Create OHLC bars
    ohlc_bars = ticks_processed.windowby(
        ticks_processed.timestamp,
        window=pw.temporal.tumbling(duration=pw.Duration(NEW_TIMEFRAME)),
        behavior=pw.temporal.exactly_once_behavior(),
        instance=ticks_processed.symbol
    ).reduce(
        symbol=pw.this._pw_instance,
        timestamp=pw.reducers.min(pw.this.timestamp),
        open=pw.reducers.argmin(pw.this.timestamp, pw.this.price),
        high=pw.reducers.max(pw.this.price),
        low=pw.reducers.min(pw.this.price),
        close=pw.reducers.argmax(pw.this.timestamp, pw.this.price),
        volume=pw.reducers.sum(pw.this.volume)
    )
    
    # Calculate returns based on OHLC
    real_stream = ohlc_bars.with_columns(
        r=pw.if_else(
            pw.this.open != 0,
            (pw.this.close - pw.this.open) / pw.this.open,
            0.0
        )
    )
    real_stream = real_stream.with_columns(r_sq=pw.this.r * pw.this.r)
    pw.io.csv.write(real_stream, "/app/output/real_table.csv")
    
    # Convert timestamp back to milliseconds for consistency
    real_stream = real_stream.with_columns(
        t=pw.this.timestamp.dt.timestamp(unit="ms")
    )

    # 2. Heartbeat Stream
    heartbeat_subject = HeartbeatSubject(tickers)
    heartbeat_stream = pw.io.python.read(
        heartbeat_subject,
        schema=HeartbeatSchema,
        format="json"
    )

    # --- C. Separate Reductions ---
    
    # 1. Stats Table (Price/Returns) - using OHLC columns
    stats_table = real_stream.groupby(pw.this.symbol).reduce(
        symbol=pw.this.symbol,
        latest_price=pw.reducers.latest(pw.this.close),  # Use close price
        current_return=pw.reducers.latest(pw.this.r),
        mean_r=pw.reducers.avg(pw.this.r),     
        mean_r_sq=pw.reducers.avg(pw.this.r_sq),
        last_trade_time=pw.reducers.max(pw.this.t)
    )
    pw.io.csv.write(stats_table, "/app/output/stats_table.csv")

    # 2. Time Table (Heartbeats)
    time_table = heartbeat_stream.groupby(pw.this.s).reduce(
        symbol=pw.this.s,
        heartbeat_time=pw.reducers.max(pw.this.t)
    )
    pw.io.csv.write(time_table, "/app/output/time_table.csv")
    # --- D. Join (State Persistence) ---
    
    merged = stats_table.join(
        time_table,
        stats_table.symbol == time_table.symbol,
        how=pw.JoinMode.OUTER
    ).select(
        symbol=pw.coalesce(stats_table.symbol, time_table.symbol),
        
        latest_price=stats_table.latest_price,
        current_return=stats_table.current_return,
        mean_r=stats_table.mean_r,
        mean_r_sq=stats_table.mean_r_sq,
        
        # Use coalesce - prioritize heartbeat time
        raw_time=pw.coalesce(time_table.heartbeat_time, stats_table.last_trade_time)
    )
    pw.io.csv.write(merged, "/app/output/m_table.csv")
    # Safety Filter: Ensure we have a valid time
    final_prep = merged.filter(pw.this.raw_time.is_not_none())
    
    # Convert time
    final_prep = final_prep.with_columns(
        timestamp=pw.this.raw_time.dt.from_timestamp("ms")
    )

    # --- E. Scoring ---
    scored = final_prep.select(
        symbol=pw.this.symbol,
        timestamp=pw.this.timestamp,
        latest_price=pw.this.latest_price,
        z_score=calculate_z_score(pw.this.current_return, pw.this.mean_r, pw.this.mean_r_sq)
    )

    final_output = scored.select(
        symbol=pw.this.symbol,
        timestamp=pw.this.timestamp,
        latest_price=pw.this.latest_price,
        stock_score=calculate_sigmoid(pw.this.z_score),
        z_score=pw.this.z_score,
        status=get_status(pw.this.z_score)
    )

    # Output only valid rows
    live_output = final_output.filter(pw.this.latest_price.is_not_none())

    # --- F. Output ---
    pw.io.jsonlines.write(live_output, "/app/output/newvalues.jsonl")
    
    pw.io.kafka.write(
        live_output,
        rdkafka_settings,
        topic_name="stock_scores",
        format="json"
    )

    pw.run()

if __name__ == "__main__":
    main()