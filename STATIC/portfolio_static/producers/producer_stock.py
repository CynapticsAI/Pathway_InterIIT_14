import pathway as pw
import pandas as pd
import time
import os
from datetime import datetime

# --- CONFIGURATION ---
TOPIC_NAME = "stock_data"
DATA_DIR = "/app/data"
# Exact filenames you have in your data folder
TARGET_STOCKS = ["TSLA", "BX", "NIO", "AMZN", "MSFT"]
START_DATE = "2021-09-01"
END_DATE = "2022-09-30"

RDKAFKA_SETTINGS = {
    "bootstrap.servers": "kafka:9092",
    "group.id": "producer_group_csv_stocks",
    "session.timeout.ms": "6000",
}

class StockAggregates(pw.Schema):
    s: str   # symbol
    p: float # price (Close)
    t: int   # timestamp (ms)
    v: float # volume
    r: float # return

class CsvSubject(pw.io.python.ConnectorSubject):
    def __init__(self, records):
        super().__init__()
        self.records = records
        
    def run(self):
        print(f"📤 Streaming {len(self.records)} historical records...", flush=True)
        # Sort by timestamp to ensure correct chronological replay
        self.records.sort(key=lambda x: x["t"])
        
        for record in self.records:
            self.next_json(record)
            # Tiny sleep to allow the scorer window to process data logically
            time.sleep(0.0005) 
        print("✅ Stock Data Stream complete.")

def load_and_merge_csvs():
    all_records = []
    print(f"📂 Loading CSVs from {DATA_DIR}...", flush=True)

    for sym in TARGET_STOCKS:
        file_path = os.path.join(DATA_DIR, f"{sym}.csv")
        if not os.path.exists(file_path):
            print(f"⚠️ Warning: File {file_path} not found. Skipping.")
            continue
            
        try:
            df = pd.read_csv(file_path)
            
            # Standardize Columns
            df.columns = [c.lower() for c in df.columns]
            # Handle 'Date' vs 'timestamp'
            date_col = 'date' if 'date' in df.columns else 'timestamp'
            if date_col not in df.columns:
                print(f"❌ Skipping {sym}: No date column found.")
                continue

            # ✅ FIX: Explicitly handle day-first formats (13-09-2021)
            # We use 'coerce' to handle mixed formats safely
            try:
                df[date_col] = pd.to_datetime(df[date_col], dayfirst=True)
            except:
                # Fallback for ISO or US formats mixed in
                df[date_col] = pd.to_datetime(df[date_col], format='mixed', dayfirst=True)
            
            # Filter Date Range
            mask = (df[date_col] >= START_DATE) & (df[date_col] <= END_DATE)
            df = df.loc[mask].copy()
            
            # Calculate Returns
            df['return'] = df['close'].pct_change().fillna(0.0)
            
            print(f"   -> Loaded {len(df)} rows for {sym}")

            for _, row in df.iterrows():
                all_records.append({
                    "s": sym,
                    "p": float(row["close"]),
                    "t": int(row[date_col].timestamp() * 1000),
                    "v": float(row["volume"]),
                    "r": float(row["return"])
                })
                
        except Exception as e:
            print(f"❌ Error processing {sym}: {e}")

    print(f"✅ Total merged records: {len(all_records)}")
    return all_records

def main():
    print("⏳ Waiting 15s for Kafka to be ready...", flush=True)
    time.sleep(15)
    
    records = load_and_merge_csvs()
    
    if not records:
        print("❌ No data loaded. Please check /app/data folder.")
        # Keep container alive to debug
        time.sleep(3600)
        return

    subject = CsvSubject(records)
    t_stream = pw.io.python.read(subject, schema=StockAggregates)
    
    pw.io.kafka.write(t_stream, RDKAFKA_SETTINGS, topic_name=TOPIC_NAME, format="json")
    pw.run()

if __name__ == "__main__":
    main()