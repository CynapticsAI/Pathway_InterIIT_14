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
MIN_BARS_FOR_STATS = 5  # Need at least 30 bars to get a stable std. dev.
SPIKE_THRESHOLD = 3.0  # Z-Score threshold (3.0 = "3-sigma" event)


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

def detect_spikes(ohlc_bars: pw.Table) -> pw.Table:
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
            timestamp=pw.this._pw_window_end,
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
    output_path2 = "/app/output/volume_volatility.jsonl"
    pw.io.jsonlines.write(stats_unpacked, output_path2)

    zscore_stats = stats_unpacked.with_columns(
        volume_zscore=pw.if_else(
            pw.this.std_volume > 1e-6,  # Avoid division by zero
            (pw.this.current_volume - pw.this.avg_volume) / pw.this.std_volume,
            0.0
        ),
        volatility_zscore=pw.if_else(
            pw.this.std_range > 1e-9,  # Avoid division by zero
            (pw.this.current_range - pw.this.avg_range) / pw.this.std_range,
            0.0
        ),
    ).with_columns(
        risk_level=pw.if_else(
            (pw.this.volume_zscore > 5.0) | (pw.this.volatility_zscore > 5.0),
            "CRITICAL",
            pw.if_else(
                (pw.this.volume_zscore > SPIKE_THRESHOLD) & (pw.this.volatility_zscore > SPIKE_THRESHOLD),
                "HIGH",
                pw.if_else(
                    (pw.this.volume_zscore > SPIKE_THRESHOLD) | (pw.this.volatility_zscore > SPIKE_THRESHOLD),
                    "MEDIUM",
                    "LOW"
                )
            )
        ))

    vol_data = zscore_stats.with_columns(timestamp = pw.this.timestamp, symbol = pw.this.symbol, volume_zscore = pw.this.volume_zscore, volatility_zscore = pw.this.volatility_zscore)
    output_path2 = "/app/output/vol_data.jsonl"
    pw.io.jsonlines.write(vol_data, output_path2)
    pw.io.kafka.write(vol_data,
     rdkafka_settings={
         "bootstrap.servers": "kafka:9092",
         "group.id": "market_ticks_vol",
         "session.timeout.ms": "6000",
     }, topic_name="volume_volatility_data", format="json")

    spike_alerts = zscore_stats.filter(
        pw.this.risk_level != "LOW"
    )
    final = spike_alerts.select(
        pw.this.timestamp,
        pw.this.risk_level,
        pw.this.symbol,
        pw.this.current_close,
        pw.this.current_volume,
        pw.this.avg_volume,
        pw.this.volume_zscore,
        pw.this.current_range,
        pw.this.avg_range,
        pw.this.volatility_zscore
    )
    output_path2 = "/app/output/spike_alerts.jsonl"
    pw.io.jsonlines.write(final, output_path2)

def main():
    fmt = "%Y-%m-%d %H:%M:%S"
    print("Connecting to Kafka for tick data...")
    ticks = pw.io.kafka.read(
        rdkafka_settings={
            "bootstrap.servers": "kafka:9092",
            "group.id": "stock_analyzer_ticks_vol",
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
        timestamp=pw.this.t.dt.utc_from_timestamp("ms"),  # Convert int (ms) to datetime
        price=ticks.p,
        volume=ticks.v
    ).select(pw.this.symbol, pw.this.timestamp, pw.this.price, pw.this.volume)

    ohlc_bars = ticks_processed.windowby(
        ticks_processed.timestamp,
        window=pw.temporal.tumbling(duration=pw.Duration("15s")),
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
    output_path1 = "/app/output/ohlc_bars.jsonl"
    pw.io.jsonlines.write(ohlc_bars, output_path1)
    #ohlc_bars = pw.io.csv.read("/app/output/ohlc_bars.csv", schema=TickInputSchema, mode="static")
    #ohlc_bars = ohlc_bars.with_columns(timestamp=ohlc_bars.timestamp.dt.strptime(fmt=fmt))
    spike_alerts_stream = detect_spikes(ohlc_bars)
    pw.run()

if __name__ == "__main__":
    main()
