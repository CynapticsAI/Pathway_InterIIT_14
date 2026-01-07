# pathway_fred_producer.py (FETCH FROM 1990)
import os
import time
import pandas as pd
from fredapi import Fred
import logging
from datetime import datetime
import pathway as pw
import threading

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S"
)

FRED_API_KEY = os.getenv("FRED_API_KEY")
fred = Fred(api_key=FRED_API_KEY)

ALL_FRED_SERIES = [
    "DCOILWTICO", "CPIENGSL", "PPIENG", "INDPRO", "CPALTT01USM657N",
    "PPIACO", "MNFCTRIRSA", "IPMAN", "CAPUTLB00004S", "DGORDER", "UNRATE",
    "RSAFS", "UMCSENT", "PCE", "CPIAUCSL", "RRSFS", "CPIFABSL",
    "CPIMEDSL", "GDP", "FEDFUNDS", "T10Y2Y", "M2SL", "HOUST", "MORTGAGE30US",
    "IPB53100SQ", "CPENGSL", "T10Y3M", "PERMIT", "CSUSHPINSA"
]

class ContinuousFREDCollector:
    def __init__(self, csv_path="data/fred_stream.csv", start_date="1990-01-01"):
        self.csv_path = csv_path
        self.start_date = start_date
        self.is_running = True
        # os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    
    def fetch_fred_data(self):
        """Fetch latest FRED data from 1990 onwards"""
        logging.info(f"\n{'='*70}")
        logging.info(f"Fetching {len(ALL_FRED_SERIES)} FRED series from {self.start_date}...")
        logging.info(f"{'='*70}")
        
        data = {}
        successful = 0
        
        for series_id in ALL_FRED_SERIES:
            try:
                # Fetch with observation_start parameter
                series = fred.get_series(series_id, observation_start=self.start_date)
                data[series_id] = series
                successful += 1
                date_range = f"{series.index.min().strftime('%Y-%m-%d')} to {series.index.max().strftime('%Y-%m-%d')}"
                logging.info(f"  ✓ {series_id:20s} ({len(series):4d} records) | Range: {date_range}")
            except Exception as e:
                logging.warning(f"  ✗ {series_id:20s} - {e}")
                # Create empty series instead of missing column
                data[series_id] = pd.Series(dtype=float)
        
        logging.info(f"\n✓ Successfully fetched {successful}/{len(ALL_FRED_SERIES)} series")
        
        if not data:
            logging.error("No valid FRED series downloaded!")
            return None
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        if len(df) == 0:
            logging.error("DataFrame is empty!")
            return None
            
        df.index = pd.to_datetime(df.index)
        
        # Filter to only include dates from start_date onwards
        df = df[df.index >= self.start_date]
        
        logging.info(f"After date filtering (>= {self.start_date}): {len(df)} rows")
        
        # Resample to monthly end frequency
        df = df.resample("ME").last()
        
        logging.info(f"After monthly resampling: {len(df)} rows")
        
        if len(df) == 0:
            logging.error("No data after filtering and resampling!")
            return None
        
        # Add metadata
        df['date'] = df.index.strftime('%Y-%m-%d')
        df['fetch_timestamp'] = datetime.now().isoformat()
        
        # Reset index
        df = df.reset_index(drop=True)
        
        # Reorder columns
        cols = ['date', 'fetch_timestamp'] + [col for col in df.columns if col not in ['date', 'fetch_timestamp']]
        df = df[cols]
        
        # Fill missing values: forward fill -> backward fill -> 0
        logging.info("Filling missing values...")
        for col in df.columns:
            if col not in ['date', 'fetch_timestamp']:
                before_fill = df[col].isna().sum()
                df[col] = df[col].ffill().bfill().fillna(0.0)
                after_fill = df[col].isna().sum()
                non_zero = (df[col] != 0).sum()
                logging.info(f"  {col:20s}: NaN before={before_fill:3d}, after={after_fill:3d}, non-zero={non_zero:3d}/{len(df)}")
        
        logging.info(f"\n✓ Final DataFrame: {df.shape}")
        logging.info(f"  Date range: {df['date'].min()} to {df['date'].max()}")
        
        return df
    
    def append_to_csv(self, df):
        """Append new data to CSV file (row by row for streaming simulation)"""
        try:
            file_exists = os.path.isfile(self.csv_path)
            
            if file_exists:
                existing_df = pd.read_csv(self.csv_path)
                existing_dates = set(existing_df['date'].astype(str))
                
                new_rows = df[~df['date'].astype(str).isin(existing_dates)]
                
                if len(new_rows) > 0:
                    logging.info(f"\n{'='*70}")
                    logging.info(f"📝 Appending {len(new_rows)} new rows to CSV...")
                    logging.info(f"{'='*70}")
                    
                    for idx, row in new_rows.iterrows():
                        row_df = pd.DataFrame([row])
                        row_df.to_csv(self.csv_path, mode='a', header=False, index=False)
                        logging.info(f"  ✓ Row appended | Date: {row['date']}")
                        time.sleep(0.1)  # Faster streaming
                    
                    logging.info(f"✓ All {len(new_rows)} rows appended successfully")
                    return len(new_rows)
                else:
                    logging.info("⚠️  No new data to append")
                    logging.info("Re-writing last 10 rows to keep stream active...")
                    last_rows = df.tail(10)
                    for idx, row in last_rows.iterrows():
                        row_df = pd.DataFrame([row])
                        row_df.to_csv(self.csv_path, mode='a', header=False, index=False)
                        logging.info(f"  ✓ Re-streamed row | Date: {row['date']}")
                        time.sleep(0.1)
                    return 10
            else:
                logging.info(f"\n{'='*70}")
                logging.info(f"📝 Creating new CSV: {self.csv_path}")
                logging.info(f"Writing {len(df)} rows...")
                logging.info(f"{'='*70}")
                
                # Write header
                df.iloc[:0].to_csv(self.csv_path, index=False)
                
                # Write rows one by one
                for idx, row in df.iterrows():
                    row_df = pd.DataFrame([row])
                    row_df.to_csv(self.csv_path, mode='a', header=False, index=False)
                    logging.info(f"  ✓ Row {idx+1}/{len(df)} written | Date: {row['date']}")
                    time.sleep(0.1)  # Faster streaming
                
                logging.info(f"✓ Created new CSV with {len(df)} rows")
                return len(df)
                
        except Exception as e:
            logging.error(f"❌ Error appending to CSV: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def run_continuous(self, fetch_interval=3600):
        """Run continuous data collection"""
        logging.info(f"\n{'#'*70}")
        logging.info(f"🚀 CONTINUOUS FRED DATA COLLECTOR STARTED")
        logging.info(f"{'#'*70}")
        logging.info(f"CSV Output: {self.csv_path}")
        logging.info(f"Start Date: {self.start_date}")
        logging.info(f"Fetch Interval: {fetch_interval}s ({fetch_interval/3600:.1f} hours)")
        logging.info(f"{'#'*70}\n")
        
        cycle = 1
        
        while self.is_running:
            try:
                logging.info(f"\n{'#'*70}")
                logging.info(f"CYCLE {cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logging.info(f"{'#'*70}")
                
                df = self.fetch_fred_data()
                
                if df is not None:
                    rows_added = self.append_to_csv(df)
                
                cycle += 1
                logging.info(f"\n{'='*70}")
                logging.info(f"✅ Cycle {cycle-1} complete. Next fetch in {fetch_interval}s...")
                logging.info(f"{'='*70}\n")
                
                time.sleep(fetch_interval)
                
            except KeyboardInterrupt:
                logging.info("\n\n🛑 Collector stopped by user")
                self.is_running = False
                break
            except Exception as e:
                logging.error(f"❌ Error in cycle {cycle}: {e}")
                import traceback
                traceback.print_exc()
                logging.info("Waiting 60s before retry...")
                time.sleep(60)
    
    def stop(self):
        """Stop the collector"""
        self.is_running = False


class FREDDataSchema(pw.Schema):
    date: str
    fetch_timestamp: str
    DCOILWTICO: float
    CPIENGSL: float
    PPIENG: float
    INDPRO: float
    CPALTT01USM657N: float
    PPIACO: float
    MNFCTRIRSA: float
    IPMAN: float
    CAPUTLB00004S: float
    DGORDER: float
    UNRATE: float
    RSAFS: float
    UMCSENT: float
    PCE: float
    CPIAUCSL: float
    RRSFS: float
    CPIFABSL: float
    CPIMEDSL: float
    GDP: float
    FEDFUNDS: float
    T10Y2Y: float
    M2SL: float
    HOUST: float
    MORTGAGE30US: float
    IPB53100SQ: float
    CPENGSL: float
    T10Y3M: float
    PERMIT: float
    CSUSHPINSA: float


def start_pathway_producer(csv_path, kafka_servers):
    """Start Pathway producer to stream CSV to Kafka"""
    
    rdkafka_producer_settings = {
        "bootstrap.servers": kafka_servers,  # This already uses the parameter, which is good
        "security.protocol": "plaintext",
    }
    
    logging.info(f"\n{'='*70}")
    logging.info(f"🚀 PATHWAY KAFKA PRODUCER STARTED")
    logging.info(f"{'='*70}")
    logging.info(f"Reading from: {csv_path}")
    logging.info(f"Streaming to: Kafka topic 'fred_economic_data'")
    logging.info(f"Mode: Continuous real-time streaming")
    logging.info(f"{'='*70}\n")
    
    fred_data_table = pw.io.csv.read(
        csv_path,
        schema=FREDDataSchema,
        mode='streaming',
        autocommit_duration_ms=1000
    )
    
    pw.io.subscribe(
        fred_data_table,
        on_change=lambda key, row, time, is_addition: 
            logging.info(f"📤 Streaming to Kafka | Date: {row['date']}") 
            if is_addition else None
    )
    
    pw.io.kafka.write(
        fred_data_table,
        rdkafka_producer_settings,
        topic_name="fred_economic_data",
        format="json"
    )
    
    logging.info("✅ Pathway producer initialized and ready!")
    logging.info("Monitoring CSV for new data...\n")
    
    pw.run()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Combined FRED data collector and Pathway producer")
    parser.add_argument("--csv", type=str, default="data/fred_stream.csv", 
                        help="CSV file path for data storage")
    parser.add_argument("--kafka", type=str, default=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),  # ✅ Use env var
                        help="Kafka bootstrap server")
    parser.add_argument("--fetch-interval", type=int, default=600, 
                        help="Interval between FRED data fetches (seconds)")
    parser.add_argument("--start-date", type=str, default="1990-01-01",
                        help="Start date for FRED data (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    collector = ContinuousFREDCollector(csv_path=args.csv, start_date=args.start_date)
    
    collector_thread = threading.Thread(
        target=collector.run_continuous,
        args=(args.fetch_interval,),
        daemon=True
    )
    collector_thread.start()
    
    logging.info("⏳ Waiting for initial data collection...")
    time.sleep(10)
    
    while not os.path.isfile(args.csv):
        logging.info("⏳ Waiting for CSV file to be created...")
        time.sleep(2)
    
    logging.info("✅ CSV file detected, starting Pathway producer...")
    
    try:
        start_pathway_producer(args.csv, args.kafka)
    except KeyboardInterrupt:
        logging.info("\n🛑 Stopping producer...")
        collector.stop()
        logging.info("✅ Producer stopped successfully")