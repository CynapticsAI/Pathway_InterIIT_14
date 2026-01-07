"""
Common Spike Detector

This unified producer consumes stock data and detects volume/volatility spikes.
It merges functionality from:
- chronos_deploy_main/spike_detector/spike_detector.py

Features:
- Consumes from 'stock_data' Kafka topic
- Calculates rolling volume and volatility statistics
- Detects spikes using Z-score threshold
- Publishes to 'volume_volatility_data' Kafka topic

Output Schema (JSON):
{
    "timestamp": str,        # ISO format datetime
    "symbol": str,           # stock symbol
    "volume_zscore": float,  # volume Z-score
    "volatility_zscore": float  # volatility Z-score
}
"""

import os
import time
import logging
from typing import Tuple
from datetime import datetime

import pathway as pw
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9090")
ROLLING_WINDOW_DURATION = os.getenv("ROLLING_WINDOW_DURATION", "5m")
ROLLING_WINDOW_HOP = os.getenv("ROLLING_WINDOW_HOP", "10s")
MIN_BARS_FOR_STATS = int(os.getenv("MIN_BARS_FOR_STATS", "5"))
SPIKE_THRESHOLD = float(os.getenv("SPIKE_THRESHOLD", "3.0"))

# Kafka settings
RDKAFKA_CONSUMER_SETTINGS = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
    "group.id": "common_spike_detector",
    "session.timeout.ms": "6000",
}

RDKAFKA_PRODUCER_SETTINGS = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
    "group.id": "spike_detector_out",
    "session.timeout.ms": "6000",
}

INPUT_TOPIC = "stock_data"
OUTPUT_TOPIC = "volume_volatility_data"


class TickInputSchema(pw.Schema):
    """Schema for input stock data."""
    s: str      # symbol
    p: float    # price
    t: int      # timestamp (ms)
    v: float    # volume


class CustomStatsAccumulator(pw.BaseCustomAccumulator):
    """Custom accumulator for calculating rolling mean and std."""
    
    def __init__(self, sum: float, sum_sq: float, cnt: int):
        self.sum = sum
        self.sum_sq = sum_sq
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
        """Returns (average, standard_deviation)."""
        avg = 0.0
        std = 0.0

        if self.cnt > 0:
            avg = self.sum / self.cnt

        if self.cnt > 1:
            variance = (self.sum_sq / self.cnt) - (avg * avg)
            std = max(0.0, variance) ** 0.5

        return (avg, std)


custom_stats = pw.reducers.udf_reducer(CustomStatsAccumulator)


def detect_spikes(ohlc_bars: pw.Table) -> pw.Table:
    """
    Analyzes a stream of OHLC bars to detect volume and volatility spikes.
    """
    
    # Calculate price range (volatility proxy)
    ohlc_with_range = ohlc_bars.with_columns(
        price_range=pw.if_else(
            pw.this.close != 0,
            (pw.this.high - pw.this.low) / pw.this.close,
            0.0
        )
    )
    
    # Rolling window statistics
    rolling_stats = ohlc_with_range.windowby(
        ohlc_with_range.timestamp,
        window=pw.temporal.sliding(
            duration=pw.Duration(ROLLING_WINDOW_DURATION),
            hop=pw.Duration(ROLLING_WINDOW_HOP),
        ),
        behavior=pw.temporal.exactly_once_behavior(),
        instance=ohlc_with_range.symbol
    ).reduce(
        timestamp=pw.this._pw_window_end,
        symbol=pw.this._pw_instance,
        current_close=pw.reducers.argmax(pw.this.timestamp, id=pw.this.close),
        current_volume=pw.reducers.argmax(pw.this.timestamp, id=pw.this.volume),
        current_range=pw.reducers.argmax(pw.this.timestamp, id=pw.this.price_range),
        volume_stats=custom_stats(pw.this.volume),
        range_stats=custom_stats(pw.this.price_range),
        bar_count=pw.reducers.count()
    )

    # Filter for stable statistics
    stable_stats = rolling_stats.filter(
        pw.this.bar_count >= MIN_BARS_FOR_STATS
    )

    # Unpack statistics
    stats_unpacked = stable_stats.with_columns(
        avg_volume=pw.this.volume_stats[0],
        std_volume=pw.this.volume_stats[1],
        avg_range=pw.this.range_stats[0],
        std_range=pw.this.range_stats[1]
    )

    # Calculate Z-scores
    zscore_stats = stats_unpacked.with_columns(
        volume_zscore=pw.if_else(
            pw.this.std_volume > 1e-6,
            (pw.this.current_volume - pw.this.avg_volume) / pw.this.std_volume,
            0.0
        ),
        volatility_zscore=pw.if_else(
            pw.this.std_range > 1e-9,
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
        )
    )

    # Output format
    vol_data = zscore_stats.select(
        timestamp=pw.this.timestamp,
        symbol=pw.this.symbol,
        volume_zscore=pw.this.volume_zscore,
        volatility_zscore=pw.this.volatility_zscore
    )

    return vol_data


def main():
    """Main entry point for the Spike Detector."""
    
    logger.info("=" * 70)
    logger.info("COMMON SPIKE DETECTOR")
    logger.info("=" * 70)
    logger.info(f"Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
    logger.info(f"Input Topic: {INPUT_TOPIC}")
    logger.info(f"Output Topic: {OUTPUT_TOPIC}")
    logger.info(f"Rolling Window: {ROLLING_WINDOW_DURATION}")
    logger.info(f"Spike Threshold: {SPIKE_THRESHOLD}")
    logger.info("=" * 70)
    
    # Wait for Kafka to be ready
    logger.info("Waiting for Kafka to be ready...")
    time.sleep(5)
    
    # Read from Kafka
    logger.info("Connecting to Kafka for stock data...")
    ticks = pw.io.kafka.read(
        rdkafka_settings=RDKAFKA_CONSUMER_SETTINGS,
        topic=INPUT_TOPIC,
        schema=TickInputSchema,
        format="json",
        autocommit_duration_ms=1000,
    )
    logger.info("✓ Kafka tick stream connected.")

    # Process ticks
    ticks_processed = ticks.with_columns(
        symbol=ticks.s,
        timestamp=pw.this.t.dt.utc_from_timestamp("ms"),
        price=ticks.p,
        volume=ticks.v
    ).select(pw.this.symbol, pw.this.timestamp, pw.this.price, pw.this.volume)

    # Create OHLC bars
    ohlc_bars = ticks_processed.windowby(
        ticks_processed.timestamp,
        window=pw.temporal.tumbling(duration=pw.Duration("10s")),
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

    # Detect spikes
    vol_data = detect_spikes(ohlc_bars)

    # Write to Kafka
    pw.io.kafka.write(
        vol_data,
        rdkafka_settings=RDKAFKA_PRODUCER_SETTINGS,
        topic_name=OUTPUT_TOPIC,
        format="json"
    )
    
    # Also write to JSONL for debugging
    pw.io.jsonlines.write(vol_data, "/app/output/vol_data.jsonl")
    pw.io.jsonlines.write(ohlc_bars, "/app/output/ohlc_bars.jsonl")

    logger.info(f"✓ Spike detector initialized. Streaming to '{OUTPUT_TOPIC}'...")
    
    pw.run()


if __name__ == "__main__":
    main()
