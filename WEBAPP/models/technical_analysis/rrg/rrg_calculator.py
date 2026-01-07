import pathway as pw
import pandas as pd
import numpy as np
import json
import time

import redis
import yfinance as yf
from datetime import datetime
from typing import Dict, Any
from collections import deque
from pathway.io.python import ConnectorSubject
import os

SYMBOLS = ["MSFT", "AAPL", "TSLA", "GOOGL", "SPY"]
BENCHMARK_TICKER = "SPY"
RRG_PERIOD = 21
DATA_PERIOD = "5y"
DATA_INTERVAL = "1wk"
SIM_SPEED_SEC = 0.5
fmt = "%Y-%m-%dT%H:%M:%S"

HISTORY_WINDOW_SIZE = (RRG_PERIOD * 3 + 5) * len(SYMBOLS)

OUTPUT_JSONL_FILE = "output/rrg_output.json"


class YFinanceSchema(pw.Schema):
    timestamp: int
    symbol: str
    close: float


data_history = deque(maxlen=HISTORY_WINDOW_SIZE)

try:
    if os.path.exists(OUTPUT_JSONL_FILE):
        os.remove(OUTPUT_JSONL_FILE)
    print(f"Engine: Cleared old output file: {OUTPUT_JSONL_FILE}")
except Exception as e:
    print(f"Engine: Warning: Could not clear old file. {e}")


def calculate_rrg_metrics(data_history_list, period=RRG_PERIOD):
    try:
        df = pd.DataFrame(data_history_list)
        df['timestamp'] = pd.to_datetime(df['timestamp'], format=fmt)
        df = df.drop_duplicates(subset=['timestamp', 'symbol'], keep='last')
        df = df.sort_values(by='timestamp')
        df_pivot = df.pivot(index='timestamp', columns='symbol', values='close')

        if len(df_pivot) < period * 3:
            print(f"Engine: Warming up... {len(df_pivot)} / {period * 3} timestamps", end='\r')
            return []

        benchmark = df_pivot[BENCHMARK_TICKER]
        latest_coordinates = []

        for symbol in df_pivot.columns:
            if symbol == BENCHMARK_TICKER:
                continue

            rs = df_pivot[symbol] / benchmark
            rs_mean = rs.rolling(window=period).mean()
            rs_sd = rs.rolling(window=period).std()
            rs_ratio = 100 * (((rs - rs_mean) / rs_sd) + 1)

            momentum = rs_ratio.diff(periods=period)
            mom_mean = momentum.rolling(window=period).mean()
            mom_sd = momentum.rolling(window=period).std()
            rs_momentum = 100 * (((momentum - mom_mean) / mom_sd) + 1)

            try:
                last_valid_ratio = rs_ratio.dropna().iloc[-1]
                last_valid_mom = rs_momentum.dropna().iloc[-1]

                if not np.isfinite(last_valid_ratio) or not np.isfinite(last_valid_mom):
                    continue

                latest_coordinates.append({
                    "symbol": symbol,
                    "rs_ratio": last_valid_ratio,
                    "rs_momentum": last_valid_mom,
                    "timestamp": df_pivot.index[-1].strftime(fmt)
                })
            except IndexError:
                continue
        return latest_coordinates
    except Exception as e:
        print(f"\nEngine: Error in RRG calculation: {e}")
        return []


class YFinanceSubject(ConnectorSubject):
    def __init__(self):
        super().__init__()
        self.data_queue = self._load_data()

    def _load_data(self):
        global data_history
        df_hist = yf.download(tickers=SYMBOLS, period=DATA_PERIOD, interval=DATA_INTERVAL)
        print(f"Engine: Download complete. Found {len(df_hist)} minutes of data.")

        df_close = df_hist['Close'].stack().reset_index()
        df_close.columns = ['timestamp', 'symbol', 'close']
        df_close = df_close.dropna()
        df_close = df_close.drop_duplicates(subset=['timestamp', 'symbol'], keep='last')
        df_close = df_close.sort_values(by='timestamp')
        df_close['timestamp'] = (pd.to_datetime(df_close['timestamp']).astype(np.int64) // 10 ** 9)
        formatted_data = df_close.to_dict('records')
        df_close_str_time = df_close.copy()
        df_close_str_time['timestamp'] = pd.to_datetime(df_close_str_time['timestamp'], unit='s').dt.strftime(
            fmt)
        formatted_data_for_redis = df_close_str_time.to_dict('records')
        warmup_size = min(len(formatted_data_for_redis), HISTORY_WINDOW_SIZE)
        data_to_fill = formatted_data_for_redis[:warmup_size]
        data_history.extend(data_to_fill)

        data_queue = deque(formatted_data[warmup_size:])
        print(f"Engine: Warm-up complete. Starting simulation with {len(data_queue)} records.")
        return data_queue

    def run(self):
        print("Engine: Connector 'run' method started...")
        while self.data_queue:
            try:
                tick = self.data_queue.popleft()
                self.next(
                    timestamp=tick['timestamp'],
                    symbol=tick['symbol'],
                    close=tick['close']
                )
                time.sleep(SIM_SPEED_SEC)
            except IndexError:
                break
        print("Engine: Simulation data queue empty. Connector 'run' method finishing.")


def calculate_and_write_to_json_callback(
        key: Any, row: Dict, time: datetime, is_addition: bool
):
    if not is_addition:
        return

    global data_history
    timestamp = row['timestamp']
    symbol = row['symbol']
    close = row['close']
    tick = {"timestamp": timestamp.strftime(fmt), "symbol": symbol, "close": close}

    data_history.append(tick)
    rrg_points = calculate_rrg_metrics(list(data_history), period=RRG_PERIOD)

    if rrg_points:
        try:
            # Connect to your cloud Redis
            r = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)
            r.set("rrg_data:stocks", json.dumps(rrg_points))
            print("Wrote stock data to Redis")
            with open(OUTPUT_JSONL_FILE, "w") as f:
                json.dump(rrg_points, f)

            print(f"Engine: Tick: {timestamp} | Wrote {len(rrg_points)} RRG points to {OUTPUT_JSONL_FILE}.")
        except Exception as e:
            print(f"Engine: Error writing to {OUTPUT_JSONL_FILE}: {e}")


def run_pipeline():
    raw_stream = pw.io.python.read(
        YFinanceSubject(),
        schema=YFinanceSchema,
        mode="streaming"
    )

    stream = raw_stream.select(
        timestamp=raw_stream.timestamp.dt.utc_from_timestamp("s"),
        symbol=raw_stream.symbol,
        close=raw_stream.close
    )

    pw.io.subscribe(stream, calculate_and_write_to_json_callback)
    pw.run()


if __name__ == "__main__":
    run_pipeline()