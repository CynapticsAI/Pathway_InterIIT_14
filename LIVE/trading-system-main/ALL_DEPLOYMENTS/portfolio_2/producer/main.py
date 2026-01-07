import os
import pathway as pw
import json
import asyncio
import aiohttp
import yfinance as yf
import pandas as pd  # Added pandas to read CSV
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta

load_dotenv()
API_KEY = os.getenv("API_KEY")
TOPIC_NAME = "stock_data"

rdkafka_settings = {
    "bootstrap.servers": "kafka:9090",
    "group.id": "producer_group_multi",
    "session.timeout.ms": "6000",
}

# ---------------------------------------------------------
# CONFIGURATION: LOAD STOCKS FROM CSV
# ---------------------------------------------------------
# We read the master stock list to generate the map dynamically
try:
    print("Loading Master Stock List...", flush=True)
    stock_df = pd.read_csv("master_stock_list.csv")
    
    # Creating a map. Yahoo uses the symbol directly (e.g. AAPL). 
    # Finnhub usually requires the specific exchange or just the symbol. 
    # For US stocks, Finnhub usually accepts just the ticker (e.g., "AAPL").
    # If you need specific exchanges, you might need to append "US:" 
    SYMBOLS_MAP = {row['symbol']: row['symbol'] for index, row in stock_df.iterrows()}
    
    # If you still want crypto, you can append them manually:
    # SYMBOLS_MAP["BTC-USD"] = "BINANCE:BTCUSDT"
    
except Exception as e:
    print(f"Error reading CSV: {e}")
    print("Falling back to default Crypto list.")
    SYMBOLS_MAP = {
        "BTC-USD": "BINANCE:BTCUSDT",
        "ETH-USD": "BINANCE:ETHUSDT"
    }

# ... Rest of your code (Class StockAggregates, etc) remains the same ...

class StockAggregates(pw.Schema):
    s: str   # symbol
    p: float # price
    t: int   # timestamp
    v: float # volume
    r: float # return

# ---------------------------------------------------------
# 1. History Connector (Handles List)
# ---------------------------------------------------------
class HistorySubject(pw.io.python.ConnectorSubject):
    def __init__(self, records):
        super().__init__()
        self.records = records
        
    def run(self):
        print(f"📤 Streaming {len(self.records)} historical records for {len(SYMBOLS_MAP)} symbols...")
        for record in self.records:
            self.next_json(record)

# ---------------------------------------------------------
# 2. Live Connector (Handles Dictionary of Prices)
# ---------------------------------------------------------
class FinnhubSubject(pw.io.python.ConnectorSubject):
    def __init__(self, api_key, symbols_map, last_known_prices):
        super().__init__()
        self.url = f"wss://ws.finnhub.io?token={api_key}"
        self.symbols = list(symbols_map.values()) # List of Finnhub symbols
        # Key: Symbol, Value: Price (float)
        self.last_prices = last_known_prices 

    def run(self):
        asyncio.run(self._start_ws())

    async def _start_ws(self):
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(self.url) as ws:
                
                # Subscribe to ALL symbols
                for sym in self.symbols:
                    await ws.send_json({"type": "subscribe", "symbol": sym})
                    print(f" Subscribed to {sym}")

                print(f"Live Stream Started. Tracking {len(self.symbols)} symbols.")
                
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        if data.get("type") == "trade":
                            for trade in data.get("data", []):
                                symbol = trade["s"]
                                current_price = float(trade["p"])
                                
                                # Get the specific last price for THIS symbol
                                prev_price = self.last_prices.get(symbol)
                                
                                if prev_price and prev_price > 0:
                                    ret = (current_price - prev_price) / prev_price
                                else:
                                    ret = 0.0
                                
                                # Update state for this specific symbol
                                self.last_prices[symbol] = current_price
                                
                                self.next_json({
                                    "s": symbol,
                                    "p": current_price,
                                    "t": int(trade["t"]),
                                    "v": float(trade["v"]),
                                    "r": float(ret)
                                })

# ---------------------------------------------------------
# Fetch History Loop
# ---------------------------------------------------------
def get_historical_data():
    all_records = []
    last_prices_map = {}

    # End date is NOW, Start date is 8 months ago
    end_date = datetime.now()
    start_date = end_date - timedelta(days=240)

    print(f"Fetching History for {len(SYMBOLS_MAP)} symbols...")

    for yf_sym, fh_sym in SYMBOLS_MAP.items():
        print(f"   ... fetching {yf_sym}")
        try:
            # Fetch data
            df = yf.Ticker(yf_sym).history(start=start_date, end=end_date, interval="1h")
            if df.empty:
                # Fallback to daily if hourly is missing
                df = yf.Ticker(yf_sym).history(start=start_date, end=end_date, interval="1d")
            
            # Calculate returns
            df['Return'] = df['Close'].pct_change().fillna(0.0)

            # Append to master list
            for date_idx, row in df.iterrows():
                price = float(row["Close"])
                all_records.append({
                    "s": fh_sym, # Use the Finnhub symbol name here!
                    "p": price,
                    "t": int(date_idx.timestamp() * 1000),
                    "v": float(row["Volume"]),
                    "r": float(row["Return"])
                })
                
            # Save the very last price for this symbol
            if not df.empty:
                last_prices_map[fh_sym] = float(df["Close"].iloc[-1])
            else:
                last_prices_map[fh_sym] = 0.0

        except Exception as e:
            print(f"Error fetching {yf_sym}: {e}")

    # CRITICAL: Sort combined records by time so they replay chronologically
    # This mixes BTC, ETH, SOL records in the correct time order.
    all_records.sort(key=lambda x: x["t"])
    
    print(f"Loaded {len(all_records)} total records.")
    return all_records, last_prices_map

def main():
    print("Waiting for Kafka...", flush=True)
    time.sleep(5)
    
    # 1. Get History & Price Map
    history_data, last_prices_map = get_historical_data()
    
    # 2. Push History
    history_subject = HistorySubject(history_data)
    t_hist = pw.io.python.read(history_subject, schema=StockAggregates)
    pw.io.kafka.write(t_hist, rdkafka_settings, topic_name=TOPIC_NAME, format="json")
    
    # 3. Push Live (Pass the map of prices)
    live_subject = FinnhubSubject(API_KEY, SYMBOLS_MAP, last_prices_map)
    t_live = pw.io.python.read(live_subject, schema=StockAggregates)
    pw.io.kafka.write(t_live, rdkafka_settings, topic_name=TOPIC_NAME, format="json")
    pw.io.csv.write(t_live, "/app/output/a.csv")

    print(" Producer Running...", flush=True)
    pw.run()

if __name__ == "__main__":
    main()