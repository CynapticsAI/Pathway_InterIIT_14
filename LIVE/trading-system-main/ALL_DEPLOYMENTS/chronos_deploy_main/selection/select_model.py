import datetime
import time
import threading
import numpy as np
import pathway as pw
from datetime import timedelta
import joblib
import json

KAFKA = {
    "bootstrap.servers": "kafka:9090",
    "group.id": "select_model",
    "session.timeout.ms": "6000",
}
KAFKA_W = {
    "bootstrap.servers": "kafka:9090",
    "group.id": "select_model_write",
    "session.timeout.ms": "6000",
}
NEW_TIMEFRAME = "10s"  # in minutes

class OhlcSchema(pw.Schema):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float

class crnsSchema(pw.Schema):

    symbol:str
    windowStart:str
    windowEnd:str
    preds_json: str
    time:float
    diff:float

class sariSchema(pw.Schema):
    timestamp: str
    symbol: str
    final_combined_signal: float
    sarimax_signal: float
    sentiment_score: float
    sentiment_score_raw: float
    last_seen_headline : str
    time_since_last_news_s: float
    decay_factor: float
    message: str
    current_price: float
    forecast_price: float
    diff:float
    time:float


@pw.udf
def first_pred_from_dict(preds_data : str) -> float:
    """
    Extract the first prediction from preds_data["preds"].
    Returns -1.0 if preds_data is None, doesn't have 'preds',
    or 'preds' is empty.
    """
    plist= json.loads(preds_data).get("preds", [-1.0])


    if(len(plist)==0):
        return -1.0

    return plist[0]
    
    
    # # Check if preds exists and is a non-empty list
    # if not preds or not isinstance(preds, list):
    #     return -3.0

    # try:
    #     return float(preds[0])
    # except (ValueError, IndexError, TypeError):
    #     return -4.0



class TickInputSchema(pw.Schema):
    s: str
    p: float
    t: int
    v: float  # Volume

ticks = pw.io.kafka.read(
    rdkafka_settings={
        "bootstrap.servers": "kafka:9090",
        "group.id": "stock_read_select",  # New group ID
        "session.timeout.ms": "6000",
    },
    topic="stock_data",
    schema=TickInputSchema,
    format="json",
    autocommit_duration_ms=1000
)
ticks_processed = ticks.with_columns(
    symbol=ticks.s,
    timestamp=pw.this.t.dt.utc_from_timestamp("ms"),  # Convert int (ms) to datetime
    price=ticks.p,
    volume=ticks.v
).select(pw.this.symbol, pw.this.timestamp, pw.this.price, pw.this.volume).filter(pw.this.symbol == "BINANCE:BTCUSDT")
ohlc_bars = ticks_processed.windowby(
    ticks_processed.timestamp,
    window=pw.temporal.tumbling(duration=pw.Duration(NEW_TIMEFRAME)),
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
ohlc_stream = ohlc_bars.with_columns(
    return_val=pw.if_else(
        pw.this.open != 0,
        (pw.this.close - pw.this.open) / pw.this.open,
        0.0
    )
)

pw.io.csv.write(ohlc_stream, "/app/s_output/ohlc1.csv")


crns_stream = pw.io.kafka.read(
    rdkafka_settings=KAFKA,
    topic="chronos_infer_preds",
    schema=crnsSchema,
    format="json",
)



crns_stream = crns_stream.with_columns(
    windowStart=crns_stream.windowStart.dt.strptime(fmt="%Y-%m-%dT%H:%M:%S.%f%z"),
    windowEnd=crns_stream.windowEnd.dt.strptime(fmt="%Y-%m-%dT%H:%M:%S.%f%z"),
    crns_pred=first_pred_from_dict(crns_stream.preds_json),
).filter(
    pw.this.crns_pred !=-1.0)


pw.io.csv.write(crns_stream, "/app/s_output/crns.csv")

sari_stream = pw.io.kafka.read(
    rdkafka_settings=KAFKA,
    topic="sarimax_forecast",
    schema=sariSchema,  
    format="json",
)

sari_stream = sari_stream.with_columns(
    timestamp=sari_stream.timestamp.dt.strptime(fmt="%Y-%m-%dT%H:%M:%S.%f%z"),
).filter(
    pw.this.forecast_price!=0.0)

pw.io.csv.write(sari_stream, "/app/s_output/sari.csv")

ohlc_stream_2= ohlc_stream.with_columns(
    timestampf=ohlc_stream.timestamp - timedelta(seconds=5)
)

ohlc_stream= ohlc_stream.asof_join(
    ohlc_stream_2,  
    ohlc_stream.timestamp,
    ohlc_stream_2.timestampf,
    how=pw.JoinMode.LEFT,
    direction=pw.temporal.Direction.FORWARD,
).select(
    timestamp=ohlc_stream.timestamp,
    prev_close=ohlc_stream.close,
    new_close=ohlc_stream_2.close,
).filter(
    pw.this.new_close.is_not_none()).with_columns(new_close=pw.unwrap(pw.this.new_close))

pw.io.csv.write(ohlc_stream, "/app/s_output/ohlc.csv")



comp= ohlc_stream.asof_join(
    crns_stream,
    ohlc_stream.timestamp,
    crns_stream.windowEnd,
    # ohlc_stream.timestamp== crns_stream.windowEnd,
    how=pw.JoinMode.LEFT,
    direction=pw.temporal.Direction.BACKWARD,
).select(
    timestamp=ohlc_stream.timestamp,
    prev_close=ohlc_stream.prev_close,
    new_close=ohlc_stream.new_close,
    crns_pred=crns_stream.crns_pred,
).filter(
    pw.this.crns_pred.is_not_none()).with_columns(crns_preds=pw.unwrap(pw.this.crns_pred))

pw.io.csv.write(comp, "/app/s_output/comp.csv")

comp= comp.asof_join(
    sari_stream,
    comp.timestamp,
    sari_stream.timestamp,
    # comp.timestamp== sari_stream.timestamp,
    how=pw.JoinMode.LEFT,
    direction=pw.temporal.Direction.BACKWARD,
).select(
    timestamp=comp.timestamp,
    prev_close=comp.prev_close,
    new_close=comp.new_close,
    crns_pred=comp.crns_pred,
    sari_pred=sari_stream.forecast_price,
).filter(
    pw.this.sari_pred.is_not_none()).with_columns(sari_pred=pw.unwrap(pw.this.sari_pred))

comp= comp.with_columns(
    real_diff= pw.this.new_close - pw.this.prev_close,
    crns_diff= pw.this.crns_pred - pw.this.prev_close,
    sari_diff= pw.this.sari_pred - pw.this.prev_close,
)




comp= comp.with_columns(
    crns_bool= pw.if_else(
        pw.this.crns_diff*pw.this.real_diff >0, 1.0, 0.0),
    sari_bool= pw.if_else(
        pw.this.sari_diff*pw.this.real_diff >0, 1.0, 0.0),
)

pw.io.csv.write(comp, "/app/s_output/comp2.csv")

decision= comp.windowby(
    comp.timestamp,
    window=pw.temporal.sliding(
        duration=timedelta(minutes=3),
        hop=timedelta(seconds=10),
    ),
    behavior = pw.temporal.exactly_once_behavior(),
).reduce(
    timestamp=pw.this._pw_window_end,
    crns_count=pw.reducers.sum(pw.this.crns_bool),
    sari_count=pw.reducers.sum(pw.this.sari_bool),
    crns_pred= pw.reducers.argmax(pw.this.timestamp,pw.this.crns_pred),
    sari_pred= pw.reducers.argmax(pw.this.timestamp,pw.this.sari_pred),
    sample_count=pw.reducers.count(),
)
decision = decision.with_columns(
    crns_confidence=pw.if_else(
        pw.this.sample_count > 0,
        pw.this.crns_count / pw.this.sample_count,
        0.0,
    ),
    sari_confidence=pw.if_else(
        pw.this.sample_count > 0,
        pw.this.sari_count / pw.this.sample_count,
        0.0,
    ),
)
decision= decision.with_columns(
    model_selected= pw.if_else(
        pw.this.crns_count > pw.this.sari_count, "CHRONOS", "SARIMAX"
    ),
    final_pred= pw.if_else(
        pw.this.crns_count >= pw.this.sari_count,
        pw.this.crns_pred,
        pw.this.sari_pred),
    signal_confidence=pw.if_else(
        pw.this.crns_count >= pw.this.sari_count,
        pw.this.crns_confidence,
        pw.this.sari_confidence,
    ),
)
pw.io.kafka.write(
    decision,
    rdkafka_settings=KAFKA_W,
    topic_name="model_selection",
    format="json",
)
pw.io.jsonlines.write(decision, "/app/s_output/model_selection.jsonl")

pw.run()