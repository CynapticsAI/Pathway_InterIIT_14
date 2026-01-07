import datetime
import time
import threading
import numpy as np
import pathway as pw
from datetime import timedelta
import joblib
import json



KAFKA = {
    "bootstrap.servers": "13.50.238.243:29092",
    "group.id": "trigger",
    "session.timeout.ms": "6000",
}
THRESH= 0.7
NET_THRESH=10

class selectSchema(pw.Schema):
    timestamp : str
    crns_count :float
    sari_count :float
    crns_pred :float
    sari_pred :float
    sample_count :float
    crns_confidence :float
    sari_confidence :float
    model_selected :str
    final_pred :float
    signal_confidence :float
    diff :float
    time :float

strm =pw.io.kafka.read(
    rdkafka_settings=KAFKA,   
    topic="model_selection",
    schema=selectSchema,
    format="json",
)
strm =strm.with_columns(
    timestamp=strm.timestamp.dt.strptime(fmt="%Y-%m-%dT%H:%M:%S.%f%z"),
    thresh_bool=pw.if_else(strm.signal_confidence >= THRESH, 1, 0),
)

trig= strm.windowby(
    strm.timestamp,
    window=pw.temporal.sliding(
        duration=timedelta(minutes=15),
        hop=timedelta(seconds=10),
    ),
    behavior = pw.temporal.exactly_once_behavior(),
).reduce(
    timestampf=pw.this._pw_window_end,
    f_pred= pw.reducers.argmin(pw.this.timestamp,pw.this.final_pred),
    l_pred= pw.reducers.argmax(pw.this.timestamp,pw.this.final_pred),
    net_bool=pw.reducers.sum(pw.this.thresh_bool),
)

trig= trig.with_columns(
    send= pw.if_else(
        pw.this.net_bool >NET_THRESH, True, False)
) 

pw.io.jsonlines.write(trig, "/app/t_output/trigger_output.jsonl")

pw.run()