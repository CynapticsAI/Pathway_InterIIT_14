from pathlib import Path
from typing import Tuple
import time
import pathway as pw
import warnings
from datetime import datetime


# --- 1. CONFIGURATION ---

# Define the input schema for your 1-minute OHLC CSV data
class TickInputSchema(pw.Schema):
    s: str
    p: float
    t: int
    v: float# Volume


# Define the parameters for the rolling analysis window
ROLLING_WINDOW_DURATION = "60m"  # Use a 60-minute baseline
ROLLING_WINDOW_HOP = "1m"  # Check for spikes every 1 minute
MIN_BARS_FOR_STATS = 1  # Need at least 30 bars to get a stable std. dev.
SPIKE_THRESHOLD = 0.0001  # Z-Score threshold (3.0 = "3-sigma" event)


class CustomStatsAccumulator(pw.BaseCustomAccumulator):
    def __init__(self, sum: float, sum_sq: float, cnt: int):
        self.sum = sum
        self.sum_sq = sum_sq  # sum of squares
        self.cnt = cnt

    @classmethod
    def from_row(cls, row):
        [val] = row
        if val is None:
            return CustomStatsAccumulator(0.0, 0.0, 0)
        return CustomStatsAccumulator(val, val * val, 1)

    def update(self, other: 'CustomStatsAccumulator'):
        self.sum += other.sum
        self.sum_sq += other.sum_sq
        self.cnt += other.cnt

    def compute_result(self) -> Tuple[float, float]:
        """
        Computes the final (average, standard_deviation) tuple.
        """
        avg = 0.0
        std = 0.0

        if self.cnt > 0:
            avg = self.sum / self.cnt

        if self.cnt > 1:  # Std dev requires at least 2 data points
            # Calculate variance: E[X^2] - (E[X])^2
            variance = (self.sum_sq / self.cnt) - (avg * avg)
            # Clamp variance at 0 to avoid sqrt(-ve) due to float precision
            std = max(0.0, variance) ** 0.5

        return (avg, std)
custom_stats = pw.reducers.udf_reducer(CustomStatsAccumulator)

# --- 2. CORE FUNCTION ---
def aggregate_ticks_to_ohlc(ticks: pw.Table) -> pw.Table:
    """
    Aggregates a stream of tick data into 1-minute OHLCV bars using Pathway.
    """
    print("Aggregating ticks into 1-minute OHLC bars...")
    ohlc = ticks.windowby(
        ticks.timestamp,
        window=pw.temporal.tumbling(duration=pw.Duration("1m")),
        behavior = pw.temporal.exactly_once_behavior(),# 1-minute windows
        instance=ticks.symbol
    ).reduce(
        symbol=pw.this._pw_instance,
        timestamp=pw.reducers.min(pw.this.timestamp),
        open=pw.reducers.argmin(pw.this.timestamp, pw.this.price),
        high=pw.reducers.max(pw.this.price),
        low=pw.reducers.min(pw.this.price),
        close=pw.reducers.argmax(pw.this.timestamp, pw.this.price),
        volume=pw.reducers.sum(pw.this.volume)
    )
    print("✅ Tick aggregation complete.")
    return ohlc

def _detect_spikes(ohlc_bars: pw.Table) -> pw.Table:
    """
    Analyzes a stream of 1-minute OHLC bars to detect
    volume and volatility spikes.
    """
    ohlc_with_range = ohlc_bars.with_columns(
        price_range=pw.if_else(
            pw.this.close != 0,
            (pw.this.high - pw.this.low) / pw.this.close,
            0.0
        )
    )
    rolling_stats = ohlc_with_range.windowby(
            ohlc_with_range.timestamp,
            window=pw.temporal.sliding(
                duration=pw.Duration(ROLLING_WINDOW_DURATION),
                hop=pw.Duration(ROLLING_WINDOW_HOP),
            ),
            behavior = pw.temporal.exactly_once_behavior(),
            instance = ohlc_with_range.symbol
        ).reduce(
            # Get data for the *most recent bar* in the window
            timestamp=pw.reducers.max(pw.this.timestamp),
            symbol=pw.this._pw_instance,
            current_close=pw.reducers.argmax(
                pw.this.timestamp, id = pw.this.close
            ),
            current_volume=pw.reducers.argmax(
                pw.this.timestamp, id = pw.this.volume
            ),
            current_range=pw.reducers.argmax(
                pw.this.timestamp, id = pw.this.price_range
            ),
            volume_stats=custom_stats(pw.this.volume),
            range_stats=custom_stats(pw.this.price_range),
            bar_count=pw.reducers.count()
        )

    stable_stats = rolling_stats.filter(
        pw.this.bar_count >= MIN_BARS_FOR_STATS
    )

    stats_unpacked = stable_stats.with_columns(
        avg_volume=pw.this.volume_stats[0],
        std_volume=pw.this.volume_stats[1],
        avg_range=pw.this.range_stats[0],
        std_range=pw.this.range_stats[1]
    )

    ohlc_bars = stats_unpacked.with_columns(
        volume_zscore=pw.if_else(
            pw.this.std_volume > 1e-6,  # Avoid division by zero
            (pw.this.current_volume - pw.this.avg_volume) / pw.this.std_volume,
            0.0
        ),
        volatility_zscore=pw.if_else(
            pw.this.std_range > 1e-9,  # Avoid division by zero
            (pw.this.current_range - pw.this.avg_range) / pw.this.std_range,
            0.0
        )
    )

    final = ohlc_bars.select(
        pw.this.timestamp,
        pw.this.symbol,
        pw.this.current_close,
        pw.this.current_volume,
        pw.this.avg_volume,
        pw.this.volume_zscore,
        pw.this.current_range,
        pw.this.avg_range,
        pw.this.volatility_zscore
    )
    return final


def get_market_stream(kafka_settings : dict, kafka_topic : str, InputSchema = TickInputSchema) -> pw.Table:
    ticks =pw.io.kafka.read(
        rdkafka_settings= kafka_settings,
        topic= kafka_topic,
        schema = InputSchema,
        format= 'json',
        autocommit_duration_ms=1000,
    )
    ticks_processed = ticks.with_columns(
        symbol=ticks.s,
        timestamp=pw.this.t.dt.from_timestamp("ms"),  # Convert int (ms) to datetime
        price=ticks.p,
        volume=ticks.v
    ).select(pw.this.symbol, pw.this.timestamp, pw.this.price, pw.this.volume)

    ohlc_bars = ticks_processed.windowby(
        ticks_processed.timestamp,
        window=pw.temporal.tumbling(duration=pw.Duration("1m")),
        behavior = pw.temporal.exactly_once_behavior(),# 1-minute windows
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
    out = _detect_spikes(ohlc_bars)
    out = out.groupby(pw.this.symbol).reduce(time = pw.reducers.max(pw.this.timestamp))
    return out


def get_ohlc_agg(kafka_settings : dict, kafka_topic_output: str = 'ohlcv', kafka_topic_input : str = 'stock_data', InputSchema = TickInputSchema) -> None:
    ticks =pw.io.kafka.read(
        rdkafka_settings= kafka_settings,
        topic= kafka_topic_input,
        schema = InputSchema,
        format= 'json',
        autocommit_duration_ms=1000,
    )
    ticks_processed = ticks.with_columns(
        produced_timestamp = pw.this.t.dt.from_timestamp("ms"),
        symbol=ticks.s,
        timestamp=pw.this.t.dt.from_timestamp("ms"),  # Convert int (ms) to datetime
        price=ticks.p,
        volume=ticks.v
    ).select(pw.this.symbol, pw.this.timestamp, pw.this.price, pw.this.volume)

    ohlc_bars = ticks_processed.windowby(
        ticks_processed.timestamp,
        window=pw.temporal.tumbling(duration=pw.Duration("1m")),
        behavior = pw.temporal.exactly_once_behavior(),# 1-minute windows
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

    ohlc_bars = _detect_spikes(ohlc_bars)
    final = ohlc_bars.groupby(ohlc_bars.symbol).reduce(
        timestamp          = pw.reducers.latest(ohlc_bars.timestamp),
        symbol             = pw.reducers.latest(ohlc_bars.symbol),
        current_close      = pw.reducers.latest(ohlc_bars.current_close),
        current_volume     = pw.reducers.latest(ohlc_bars.current_volume),
        avg_volume         = pw.reducers.latest(ohlc_bars.avg_volume),
        volume_zscore      = pw.reducers.latest(ohlc_bars.volume_zscore),
        current_range      = pw.reducers.latest(ohlc_bars.current_range),
        avg_range          = pw.reducers.latest(ohlc_bars.avg_range),
        volatility_zscore  = pw.reducers.latest(ohlc_bars.volatility_zscore),
    )

    pw.io.kafka.write(
        final,
        kafka_settings,
        kafka_topic_output,
        format = 'json',
    )

def main():
    """Main function to run the spike detection pipeline"""
    print("=" * 80)
    print("LIVE VOLATILITY & VOLUME SPIKE DETECTOR")
    print("=" * 80)

    fmt = "%Y-%m-%d %H:%M:%S"
    print("Connecting to Kafka for tick data...")
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
    print("✅ Kafka tick stream connected.")

    ticks_processed = ticks.with_columns(
        symbol=ticks.s,
        timestamp=pw.this.t.dt.from_timestamp("ms"),  # Convert int (ms) to datetime
        price=ticks.p,
        volume=ticks.v
    ).select(pw.this.symbol, pw.this.timestamp, pw.this.price, pw.this.volume)

    ohlc_bars = ticks_processed.windowby(
        ticks_processed.timestamp,
        window=pw.temporal.tumbling(duration=pw.Duration("1m")),
        behavior = pw.temporal.exactly_once_behavior(),# 1-minute windows
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
    output_path1 = "./output/ohlc_bars.jsonl"
    # ohlc_bars = pw.io.csv.read("/app/output/ohlc_bars.csv", schema=TickInputSchema, mode="static")
    #ohlc_bars = ohlc_bars.with_columns(timestamp=ohlc_bars.timestamp.dt.strptime(fmt=fmt))
    latest_ohlc = ohlc_bars.groupby(ohlc_bars.symbol).reduce(
    timestamp = pw.reducers.max(ohlc_bars.timestamp),
    symbol = pw.reducers.argmax(ohlc_bars.timestamp, ohlc_bars.symbol),
    open  = pw.reducers.argmax(ohlc_bars.timestamp, ohlc_bars.open),
    high  = pw.reducers.argmax(ohlc_bars.timestamp, ohlc_bars.high),
    low   = pw.reducers.argmax(ohlc_bars.timestamp, ohlc_bars.low),
    close = pw.reducers.argmax(ohlc_bars.timestamp, ohlc_bars.close),
    volume = pw.reducers.argmax(ohlc_bars.timestamp, ohlc_bars.volume)
    )
    pw.io.jsonlines.write(latest_ohlc, "./output/spike_alerts.jsonl")
    # pw.io.jsonlines.write(ohlc_bars, output_path1)


    #output_path2 = "/app/output/spike_alerts.jsonl"
    #pw.io.jsonlines.write(spike_alerts_stream, output_path2)

    pw.run()

if __name__ == "__main__":
    main()
