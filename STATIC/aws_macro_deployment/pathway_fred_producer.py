# pathway_fred_producer.py
import argparse
import logging
import os
import threading
import time
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd
import pathway as pw
from fredapi import Fred

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

# Known problematic series that don't exist or have issues
SKIP_SERIES = [
    "CAPUTLB00004S",  # Doesn't exist
    "CPENGSL"          # Doesn't exist
]

# Filter out problematic series
ALL_FRED_SERIES = [s for s in ALL_FRED_SERIES if s not in SKIP_SERIES]

class ContinuousFREDCollector:
    def __init__(self, csv_path: str = "data/fred_stream.csv", start_date: str = "1990-01-01"):
        self.csv_path = csv_path
        self.start_date = start_date
        self.is_running = True
        self.last_successful_fetch = None
    
    def fetch_fred_data(self) -> Optional[pd.DataFrame]:
        """Fetch latest FRED data from 1990 onwards with proper validation."""
        logging.info(f"Fetching {len(ALL_FRED_SERIES)} FRED series from {self.start_date}...")
        
        data = {}
        successful = 0
        failed_series = []
        
        for series_id in ALL_FRED_SERIES:
            try:
                # Fetch with observation_start parameter
                series = fred.get_series(series_id, observation_start=self.start_date)
                
                # ✅ FIX 1: Validate series has data
                if len(series) == 0:
                    logging.warning(f"{series_id:20s} - Empty series, skipping")
                    failed_series.append(series_id)
                    continue
                
                # ✅ FIX 2: Check data quality
                nan_pct = (series.isna().sum() / len(series)) * 100
                if nan_pct > 80:
                    logging.warning(f"{series_id:20s} - Too many NaN ({nan_pct:.1f}%), skipping")
                    failed_series.append(series_id)
                    continue
                
                # ✅ FIX 3: Check for extreme values
                non_nan_values = series.dropna()
                if len(non_nan_values) > 0:
                    max_val = non_nan_values.abs().max()
                    if max_val > 1e10:
                        logging.warning(f"{series_id:20s} - Extreme values detected (max={max_val:.2e}), skipping")
                        failed_series.append(series_id)
                        continue
                
                data[series_id] = series
                successful += 1
                date_range = f"{series.index.min().strftime('%Y-%m-%d')} to {series.index.max().strftime('%Y-%m-%d')}"
                logging.info(f"✓ {series_id:20s} ({len(series):4d} records) | Range: {date_range} | NaN: {nan_pct:.1f}%")
                
            except Exception as e:
                logging.warning(f"✗ {series_id:20s} - {e}")
                failed_series.append(series_id)
        
        logging.info(f"Successfully fetched {successful}/{len(ALL_FRED_SERIES)} series")
        
        if failed_series:
            logging.warning(f"Failed series: {', '.join(failed_series)}")
        
        # ✅ FIX 4: Require minimum number of series
        if successful < 10:
            logging.error(f"Only {successful} series fetched, need at least 10!")
            return None
        
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
        
        # ✅ FIX 5: Conservative filling - limit forward fill to 3 months
        logging.info("Filling missing values (max 3 month forward fill)...")
        for col in df.columns:
            before_fill = df[col].isna().sum()
            
            # Forward fill limited to 3 periods (months)
            df[col] = df[col].fillna(method='ffill', limit=3)
            
            # Backward fill limited to 3 periods
            df[col] = df[col].fillna(method='bfill', limit=3)
            
            # ✅ FIX 6: Use column median instead of 0 for remaining NaN
            remaining_nan = df[col].isna().sum()
            if remaining_nan > 0:
                median_val = df[col].median()
                if pd.isna(median_val):
                    median_val = 0.0
                df[col] = df[col].fillna(median_val)
            
            after_fill = df[col].isna().sum()
            non_zero = (df[col] != 0).sum()
            logging.info(f"  {col:20s}: NaN before={before_fill:3d}, after={after_fill:3d}, non-zero={non_zero:3d}/{len(df)}")
        
        # ✅ FIX 7: Clean extreme values and infinity
        logging.info("Cleaning extreme values and infinity...")
        for col in df.columns:
            # Replace inf with NaN
            df[col] = df[col].replace([np.inf, -np.inf], np.nan)
            
            # Fill any new NaN from inf replacement
            df[col] = df[col].fillna(df[col].median())
            
            # Clip extreme values to reasonable range
            q99 = df[col].quantile(0.99)
            q01 = df[col].quantile(0.01)
            range_val = q99 - q01
            
            if range_val > 0:
                upper_limit = q99 + 3 * range_val
                lower_limit = q01 - 3 * range_val
                df[col] = df[col].clip(lower=lower_limit, upper=upper_limit)
        
        # ✅ FIX 8: Final validation
        for col in df.columns:
            if not np.all(np.isfinite(df[col])):
                logging.error(f"Column {col} still has non-finite values after cleaning!")
                df[col] = df[col].replace([np.inf, -np.inf], 0).fillna(0)
        
        # Add metadata
        df['date'] = df.index.strftime('%Y-%m-%d')
        df['fetch_timestamp'] = datetime.now().isoformat()
        
        # Reset index
        df = df.reset_index(drop=True)
        
        # Reorder columns
        cols = ['date', 'fetch_timestamp'] + [col for col in df.columns if col not in ['date', 'fetch_timestamp']]
        df = df[cols]
        
        logging.info(f"✓ Final DataFrame: {df.shape}")
        logging.info(f"  Date range: {df['date'].min()} to {df['date'].max()}")
        logging.info(f"  Columns: {len(df.columns)} ({len(df.columns)-2} FRED series)")
        
        self.last_successful_fetch = datetime.now()
        
        return df
    
    def append_to_csv(self, df: pd.DataFrame) -> int:
        """Append new data to CSV file (row by row for streaming simulation)."""
        try:
            file_exists = os.path.isfile(self.csv_path)
            
            if file_exists:
                existing_df = pd.read_csv(self.csv_path)
                existing_dates = set(existing_df['date'].astype(str))
                
                new_rows = df[~df['date'].astype(str).isin(existing_dates)]
                
                if len(new_rows) > 0:
                    logging.info(f"Appending {len(new_rows)} new rows to CSV...")
                    
                    for idx, row in new_rows.iterrows():
                        row_df = pd.DataFrame([row])
                        row_df.to_csv(self.csv_path, mode='a', header=False, index=False)
                        logging.info(f"  Row appended | Date: {row['date']}")
                        time.sleep(0.1)  # Faster streaming
                    
                    logging.info(f"✓ All {len(new_rows)} rows appended successfully")
                    return len(new_rows)
                else:
                    # ✅ FIX 9: Don't re-stream old data, just log
                    logging.info("No new data to append (all dates already exist)")
                    logging.info("Skipping re-streaming of old data to avoid duplicates")
                    return 0
            else:
                logging.info(f"Creating new CSV: {self.csv_path}")
                logging.info(f"Writing {len(df)} rows...")
                
                # Write header
                df.iloc[:0].to_csv(self.csv_path, index=False)
                
                # Write rows one by one
                for idx, row in df.iterrows():
                    row_df = pd.DataFrame([row])
                    row_df.to_csv(self.csv_path, mode='a', header=False, index=False)
                    if (idx + 1) % 50 == 0:
                        logging.info(f"  Progress: {idx+1}/{len(df)} rows written")
                    time.sleep(0.05)  # Faster streaming
                
                logging.info(f"✓ Created new CSV with {len(df)} rows")
                return len(df)
                
        except Exception as e:
            logging.error(f"Error appending to CSV: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def run_continuous(self, fetch_interval: int = 3600) -> None:
        """Run continuous data collection."""
        logging.info("=" * 70)
        logging.info("CONTINUOUS FRED DATA COLLECTOR STARTED")
        logging.info("=" * 70)
        logging.info(f"CSV Output: {self.csv_path}")
        logging.info(f"Start Date: {self.start_date}")
        logging.info(f"Fetch Interval: {fetch_interval}s ({fetch_interval/60:.1f} minutes)")
        logging.info(f"Active Series: {len(ALL_FRED_SERIES)}")
        logging.info(f"Skipped Series: {', '.join(SKIP_SERIES) if SKIP_SERIES else 'None'}")
        logging.info("=" * 70)
        
        cycle = 1
        
        while self.is_running:
            try:
                logging.info(f"\n{'='*70}")
                logging.info(f"CYCLE {cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logging.info(f"{'='*70}")
                
                df = self.fetch_fred_data()
                
                if df is not None:
                    rows_added = self.append_to_csv(df)
                    logging.info(f"Cycle {cycle} complete: {rows_added} rows added")
                else:
                    logging.warning(f"Cycle {cycle} failed: No data fetched")
                
                cycle += 1
                
                if self.last_successful_fetch:
                    time_since_last = datetime.now() - self.last_successful_fetch
                    logging.info(f"Last successful fetch: {time_since_last.total_seconds():.0f}s ago")
                
                logging.info(f"Next fetch in {fetch_interval}s ({fetch_interval/60:.1f} minutes)...")
                logging.info("=" * 70)
                
                time.sleep(fetch_interval)
                
            except KeyboardInterrupt:
                logging.info("Collector stopped by user")
                self.is_running = False
                break
            except Exception as e:
                logging.error(f"Error in cycle {cycle}: {e}")
                import traceback
                traceback.print_exc()
                logging.info("Waiting 60s before retry...")
                time.sleep(60)
    
    def stop(self) -> None:
        """Stop the collector."""
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
    # CAPUTLB00004S: float  # REMOVED - doesn't exist
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
    # CPENGSL: float  # REMOVED - doesn't exist
    T10Y3M: float
    PERMIT: float
    CSUSHPINSA: float


def start_pathway_producer(csv_path: str, kafka_servers: str) -> None:
    """Start Pathway producer to stream CSV to Kafka."""
    
    rdkafka_producer_settings = {
        "bootstrap.servers": kafka_servers,
        "security.protocol": "plaintext",
    }
    
    logging.info("=" * 70)
    logging.info("PATHWAY KAFKA PRODUCER STARTED")
    logging.info("=" * 70)
    logging.info(f"Reading from: {csv_path}")
    logging.info(f"Streaming to: Kafka topic 'fred_economic_data'")
    logging.info(f"Mode: Continuous real-time streaming")
    logging.info("=" * 70)
    
    fred_data_table = pw.io.csv.read(
        csv_path,
        schema=FREDDataSchema,
        mode='streaming',
        autocommit_duration_ms=1000
    )
    
    pw.io.subscribe(
        fred_data_table,
        on_change=lambda key, row, time, is_addition: 
            logging.info(f"→ Kafka | Date: {row['date']}") 
            if is_addition else None
    )
    
    pw.io.kafka.write(
        fred_data_table,
        rdkafka_producer_settings,
        topic_name="fred_economic_data",
        format="json"
    )
    
    logging.info("✓ Pathway producer initialized and ready!")
    logging.info("Monitoring CSV for new data...")
    
    pw.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Combined FRED data collector and Pathway producer")
    parser.add_argument("--csv", type=str, default="data/fred_stream.csv", 
                        help="CSV file path for data storage")
    parser.add_argument("--kafka", type=str, default=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9090"), 
                        help="Kafka bootstrap server")
    parser.add_argument("--fetch-interval", type=int, default=3600, 
                        help="Interval between FRED data fetches (seconds)")
    parser.add_argument("--start-date", type=str, default="1990-01-01",
                        help="Start date for FRED data (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(args.csv) if os.path.dirname(args.csv) else ".", exist_ok=True)
    
    collector = ContinuousFREDCollector(csv_path=args.csv, start_date=args.start_date)
    
    collector_thread = threading.Thread(
        target=collector.run_continuous,
        args=(args.fetch_interval,),
        daemon=True
    )
    collector_thread.start()
    
    logging.info("Waiting for initial data collection...")
    time.sleep(15)  # Increased wait time
    
    while not os.path.isfile(args.csv):
        logging.info("Waiting for CSV file to be created...")
        time.sleep(2)
    
    logging.info("✓ CSV file detected, starting Pathway producer...")
    time.sleep(2)
    
    try:
        start_pathway_producer(args.csv, args.kafka)
    except KeyboardInterrupt:
        logging.info("Stopping producer...")
        collector.stop()
        logging.info("Producer stopped successfully")