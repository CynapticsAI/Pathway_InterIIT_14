import csv
from pathlib import Path
from typing import Tuple
import time
import pathway as pw
import warnings
from datetime import datetime
import pandas as pd
import os
bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
class TickInputSchema(pw.Schema):
    s: str
    p: float
    t: int
    v: float  # Volume

class HoldingsSchema(pw.Schema):
    symbol: str
    quantity: float
    cost_basis: float

def calculate_portfolio_pnl(ohlc_bars: pw.Table, holdings) -> Tuple[pw.Table, pw.Table]:
    """
    Analyzes a stream of 1-minute OHLC bars to calculate real-time PnL.

    Returns:
        A tuple of two tables: (positions_pnl_stream, total_pnl_stream)
    """
    current_prices = ohlc_bars.select(
        pw.this.symbol,
        timestamp=pw.this.timestamp,
        current_price=pw.this.close
    )

    print("Joining live prices with holdings and calculating PnL...")
    positions_pnl_stream = current_prices.join(
        holdings,
        current_prices.symbol == holdings.symbol
    ).select(
        symbol=current_prices.symbol,
        timestamp=current_prices.timestamp,
        market_value=current_prices.current_price * holdings.quantity,
        cost_value=holdings.cost_basis * holdings.quantity,
    ).with_columns(
        unrealized_pnl=pw.this.market_value - pw.this.cost_value
    ).with_columns(
        unrealized_pnl_pct=pw.this.unrealized_pnl / (pw.this.cost_value + 0.01)
    )

    print("Calculating total portfolio PnL...")
    total_pnl_stream = positions_pnl_stream.windowby(
        positions_pnl_stream.timestamp,
        window=pw.temporal.tumbling(duration=pw.Duration("1m")),
        behavior=pw.temporal.exactly_once_behavior(),
    ).reduce(
        timestamp=pw.reducers.min(pw.this.timestamp),
        total_market_value=pw.reducers.sum(pw.this.market_value),
        total_cost_value=pw.reducers.sum(pw.this.cost_value)
    ).with_columns(
        total_unrealized_pnl=pw.this.total_market_value - pw.this.total_cost_value
    ).with_columns(
        total_unrealized_pnl_pct=pw.this.total_unrealized_pnl / (pw.this.total_cost_value + 0.01)
    )

    final_total = total_pnl_stream.select(
        pw.this.timestamp,
        pw.this.total_market_value,
        pw.this.total_cost_value,
        pw.this.total_unrealized_pnl,
        pw.this.total_unrealized_pnl_pct
    )
    return (positions_pnl_stream, final_total)
def main():

    ticks = pw.io.kafka.read(
        rdkafka_settings={
            "bootstrap.servers": "kafka:9092",
            "group.id": "stock_risk_calculator_pnl",  # New group ID
            "session.timeout.ms": "6000",
        },
        topic="stock_data",
        schema=TickInputSchema,
        format="json",
        autocommit_duration_ms=1000,
    )
    ticks_processed = ticks.with_columns(
        symbol=ticks.s,
        timestamp=pw.this.t.dt.from_timestamp("ms"),
        price=ticks.p,
        volume=ticks.v
    ).select(pw.this.symbol, pw.this.timestamp, pw.this.price, pw.this.volume)

    ohlc_bars = ticks_processed.windowby(
        ticks_processed.timestamp,
        window=pw.temporal.tumbling(duration=pw.Duration("1m")),
        behavior=pw.temporal.exactly_once_behavior(),  # 1-minute windows
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
    output_path = "/app/output/ohlc_bars.jsonl"
    portfolio_file = "/app/portfolio.csv"
    print(f"Loading static portfolio from: {portfolio_file}")
    holdings = pw.io.csv.read(
        portfolio_file,
        schema=HoldingsSchema,
        mode="static"
    )

    positions_pnl, total_pnl = calculate_portfolio_pnl(ohlc_bars, holdings)

    positions_output_path = "/app/output/positions_pnl.jsonl"
    pw.io.jsonlines.write(positions_pnl, positions_output_path)

    total_output_path = "/app/output/total_portfolio_pnl.jsonl"
    pw.io.jsonlines.write(total_pnl, total_output_path)

    rdkafka_settings = {
        "bootstrap.servers": "kafka:9092",
        "group.id": "OUTPUT",
        "session.timeout.ms": "6000",
    }
    pw.io.kafka.write(total_pnl, rdkafka_settings, topic_name="pnl", format="json")
    pw.run()

if __name__ == "__main__":
    main()


