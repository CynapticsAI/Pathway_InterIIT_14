from pathlib import Path
import pathway as pw
# No pandas needed for this streaming approach
from datetime import datetime
import panel as pn

class TickInputSchema(pw.Schema):
    s: str  # Symbol
    p: float  # Price
    t: int  # Timestamp (assumed milliseconds since epoch)
    v: float  # Volume
def calculate_market_breadth(ohlc_bars: pw.Table) -> pw.Table:
    """
    Calculates market breadth statistics from 1-minute OHLC data.
    """
    #Calculating per-stock advance/decline status
    ohlc_with_status = ohlc_bars.with_columns(
        status=pw.if_else(
            pw.this.close > pw.this.open, 1,
            pw.if_else(
                pw.this.close < pw.this.open, -1,
                0
            )
        )
    )
    # Aggregate across all stocks for each minute *based on the OHLC bar timestamp*
    market_breadth = ohlc_with_status.windowby(
        ohlc_with_status.timestamp,
        window=pw.temporal.tumbling(duration=pw.Duration("1m")),
        behavior=pw.temporal.exactly_once_behavior(),
    ).reduce(
        timestamp = pw.reducers.any(pw.this.timestamp),
        total_stocks=pw.reducers.count_distinct(pw.this.symbol),
        advancing_stocks=pw.reducers.sum(
            pw.if_else(pw.this.status == 1, 1, 0)
        ),
        declining_stocks=pw.reducers.sum(
            pw.if_else(pw.this.status == -1, 1, 0)
        ),
        unchanged_stocks=pw.reducers.sum(
            pw.if_else(pw.this.status == 0, 1, 0)
        ),

    )

    market_breadth = market_breadth.with_columns(
        advance_decline_line=pw.this.advancing_stocks - pw.this.declining_stocks
    )

    market_breadth = market_breadth.select(
        market_breadth.timestamp,
        market_breadth.advancing_stocks,
        market_breadth.declining_stocks,
        market_breadth.unchanged_stocks,
        market_breadth.total_stocks,
        market_breadth.advance_decline_line
    )
    return market_breadth


def main():
    ticks = pw.io.kafka.read(
        rdkafka_settings={
            "bootstrap.servers": "kafka:9092",
            "group.id": "stock_risk_calculator",
            "session.timeout.ms": "6000",
        },
        topic="stock_data",
        schema=TickInputSchema,
        format="json",
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
    pw.io.jsonlines.write(ohlc_bars, output_path)
    print("\nStarting Market Breadth calculation pipeline...")
    market_breadth_stream = calculate_market_breadth(ohlc_bars)

    rdkafka_settings = {
        "bootstrap.servers": "kafka:9092",
        "group.id": "market_breadth_calculator",
        "session.timeout.ms": "6000",
    }
    pw.io.kafka.write(market_breadth_stream, rdkafka_settings, topic_name="market_breadth", format="json")

    output_path = "/app/output/market_breadth.jsonl"
    pw.io.jsonlines.write(market_breadth_stream, output_path)
    pw.run()
if __name__ == "__main__":
    main()
