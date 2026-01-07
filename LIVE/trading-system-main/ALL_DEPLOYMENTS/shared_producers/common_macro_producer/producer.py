"""
Common Macro Producer

This unified producer handles macroeconomic data from FRED API.
It merges functionality from:
- aws_macro_deployment/pathway_fred_producer.py

Features:
- Fetches FRED economic indicators
- Continuous data collection with CSV caching
- Streams data to Kafka via Pathway
- Publishes to 'fred_economic_data' Kafka topic

Output Schema (JSON):
- Contains all FRED series values plus date and fetch_timestamp
"""

import os
import time
import logging
import threading
from datetime import datetime
from typing import Optional, List

import numpy as np
import pandas as pd
import pathway as pw
from fredapi import Fred
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
FRED_API_KEY = os.getenv("FRED_API_KEY", "")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9090")
CSV_PATH = os.getenv("FRED_CSV_PATH", "data/fred_stream.csv")
FETCH_INTERVAL = int(os.getenv("FRED_FETCH_INTERVAL", "3600"))
START_DATE = os.getenv("FRED_START_DATE", "1990-01-01")

# Initialize FRED client
fred = Fred(api_key=FRED_API_KEY) if FRED_API_KEY else None

# Kafka settings
RDKAFKA_PRODUCER_SETTINGS = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
    "security.protocol": "plaintext",
}

TOPIC_NAME = "fred_economic_data"

# FRED series to fetch
ALL_FRED_SERIES = [
    "DCOILWTICO", "CPIENGSL", "PPIENG", "INDPRO", "CPALTT01USM657N",
    "PPIACO", "MNFCTRIRSA", "IPMAN", "DGORDER", "UNRATE",
    "RSAFS", "UMCSENT", "PCE", "CPIAUCSL", "RRSFS", "CPIFABSL",
    "CPIMEDSL", "GDP", "FEDFUNDS", "T10Y2Y", "M2SL", "HOUST", "MORTGAGE30US",
    "IPB53100SQ", "T10Y3M", "PERMIT", "CSUSHPINSA"
]


class ContinuousFREDCollector:
    """Collects FRED data continuously and writes to CSV for streaming."""
    
    def __init__(self, csv_path: str, start_date: str):
        self.csv_path = csv_path
        self.start_date = start_date
        self.is_running = True
        self.last_successful_fetch = None
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(csv_path) if os.path.dirname(csv_path) else ".", exist_ok=True)
    
    def fetch_fred_data(self) -> Optional[pd.DataFrame]:
        """Fetch latest FRED data with validation."""
        if not fred:
            logger.error("FRED API key not configured")
            return None
        
        logger.info(f"Fetching {len(ALL_FRED_SERIES)} FRED series from {self.start_date}...")
        
        data = {}
        successful = 0
        failed_series = []
        
        for series_id in ALL_FRED_SERIES:
            try:
                series = fred.get_series(series_id, observation_start=self.start_date)
                
                if len(series) == 0:
                    logger.warning(f"{series_id:20s} - Empty series, skipping")
                    failed_series.append(series_id)
                    continue
                
                nan_pct = (series.isna().sum() / len(series)) * 100
                if nan_pct > 80:
                    logger.warning(f"{series_id:20s} - Too many NaN ({nan_pct:.1f}%), skipping")
                    failed_series.append(series_id)
                    continue
                
                data[series_id] = series
                successful += 1
                date_range = f"{series.index.min().strftime('%Y-%m-%d')} to {series.index.max().strftime('%Y-%m-%d')}"
                logger.info(f"✓ {series_id:20s} ({len(series):4d} records)")
                
            except Exception as e:
                logger.warning(f"✗ {series_id:20s} - {e}")
                failed_series.append(series_id)
        
        logger.info(f"Successfully fetched {successful}/{len(ALL_FRED_SERIES)} series")
        
        if successful < 10:
            logger.error(f"Only {successful} series fetched, need at least 10!")
            return None
        
        if not data:
            logger.error("No valid FRED series downloaded!")
            return None
        
        # Create DataFrame
        df = pd.DataFrame(data)
        df.index = pd.to_datetime(df.index)
        df = df[df.index >= self.start_date]
        
        # Resample to monthly
        df = df.resample("ME").last()
        
        if len(df) == 0:
            logger.error("No data after filtering and resampling!")
            return None
        
        # Fill missing values
        for col in df.columns:
            df[col] = df[col].fillna(method='ffill', limit=3)
            df[col] = df[col].fillna(method='bfill', limit=3)
            
            remaining_nan = df[col].isna().sum()
            if remaining_nan > 0:
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val if not pd.isna(median_val) else 0.0)
        
        # Clean extreme values
        for col in df.columns:
            df[col] = df[col].replace([np.inf, -np.inf], np.nan)
            df[col] = df[col].fillna(df[col].median())
        
        # Add metadata
        df['date'] = df.index.strftime('%Y-%m-%d')
        df['fetch_timestamp'] = datetime.now().isoformat()
        df = df.reset_index(drop=True)
        
        # Reorder columns
        cols = ['date', 'fetch_timestamp'] + [col for col in df.columns if col not in ['date', 'fetch_timestamp']]
        df = df[cols]
        
        logger.info(f"✓ Final DataFrame: {df.shape}")
        self.last_successful_fetch = datetime.now()
        
        return df
    
    def append_to_csv(self, df: pd.DataFrame) -> int:
        """Append new data to CSV file."""
        try:
            file_exists = os.path.isfile(self.csv_path)
            
            if file_exists:
                existing_df = pd.read_csv(self.csv_path)
                existing_dates = set(existing_df['date'].astype(str))
                new_rows = df[~df['date'].astype(str).isin(existing_dates)]
                
                if len(new_rows) > 0:
                    logger.info(f"Appending {len(new_rows)} new rows to CSV...")
                    for idx, row in new_rows.iterrows():
                        row_df = pd.DataFrame([row])
                        row_df.to_csv(self.csv_path, mode='a', header=False, index=False)
                        time.sleep(0.1)
                    return len(new_rows)
                else:
                    logger.info("No new data to append")
                    return 0
            else:
                logger.info(f"Creating new CSV: {self.csv_path}")
                df.iloc[:0].to_csv(self.csv_path, index=False)
                
                for idx, row in df.iterrows():
                    row_df = pd.DataFrame([row])
                    row_df.to_csv(self.csv_path, mode='a', header=False, index=False)
                    time.sleep(0.05)
                
                logger.info(f"✓ Created new CSV with {len(df)} rows")
                return len(df)
                
        except Exception as e:
            logger.error(f"Error appending to CSV: {e}")
            return 0
    
    def run_continuous(self, fetch_interval: int = 3600) -> None:
        """Run continuous data collection."""
        logger.info("=" * 70)
        logger.info("CONTINUOUS FRED DATA COLLECTOR STARTED")
        logger.info("=" * 70)
        logger.info(f"CSV Output: {self.csv_path}")
        logger.info(f"Fetch Interval: {fetch_interval}s")
        logger.info("=" * 70)
        
        cycle = 1
        
        while self.is_running:
            try:
                logger.info(f"\n{'='*70}")
                logger.info(f"CYCLE {cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*70}")
                
                df = self.fetch_fred_data()
                
                if df is not None:
                    rows_added = self.append_to_csv(df)
                    logger.info(f"Cycle {cycle} complete: {rows_added} rows added")
                else:
                    logger.warning(f"Cycle {cycle} failed: No data fetched")
                
                cycle += 1
                logger.info(f"Next fetch in {fetch_interval}s...")
                time.sleep(fetch_interval)
                
            except KeyboardInterrupt:
                logger.info("Collector stopped by user")
                self.is_running = False
                break
            except Exception as e:
                logger.error(f"Error in cycle {cycle}: {e}")
                time.sleep(60)
    
    def stop(self) -> None:
        self.is_running = False


class FREDDataSchema(pw.Schema):
    """Schema for FRED data - dynamically generated based on available series."""
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
    T10Y3M: float
    PERMIT: float
    CSUSHPINSA: float


def start_pathway_producer(csv_path: str) -> None:
    """Start Pathway producer to stream CSV to Kafka."""
    
    logger.info("=" * 70)
    logger.info("PATHWAY KAFKA PRODUCER STARTED")
    logger.info("=" * 70)
    logger.info(f"Reading from: {csv_path}")
    logger.info(f"Streaming to: Kafka topic '{TOPIC_NAME}'")
    logger.info("=" * 70)
    
    fred_data_table = pw.io.csv.read(
        csv_path,
        schema=FREDDataSchema,
        mode='streaming',
        autocommit_duration_ms=1000
    )
    
    pw.io.subscribe(
        fred_data_table,
        on_change=lambda key, row, time, is_addition: 
            logger.info(f"→ Kafka | Date: {row['date']}") 
            if is_addition else None
    )
    
    pw.io.kafka.write(
        fred_data_table,
        RDKAFKA_PRODUCER_SETTINGS,
        topic_name=TOPIC_NAME,
        format="json"
    )
    
    logger.info("✓ Pathway producer initialized!")
    pw.run()


def main():
    """Main entry point for the FRED producer."""
    
    logger.info("=" * 70)
    logger.info("COMMON MACRO PRODUCER (FRED)")
    logger.info("=" * 70)
    logger.info(f"Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
    logger.info(f"Topic: {TOPIC_NAME}")
    logger.info(f"CSV Path: {CSV_PATH}")
    logger.info(f"Fetch Interval: {FETCH_INTERVAL}s")
    logger.info("=" * 70)
    
    if not FRED_API_KEY:
        logger.error("FRED_API_KEY environment variable is required")
        return
    
    # Wait for Kafka to be ready
    logger.info("Waiting for Kafka to be ready...")
    time.sleep(5)
    
    # Create collector
    collector = ContinuousFREDCollector(csv_path=CSV_PATH, start_date=START_DATE)
    
    # Start collector in background thread
    collector_thread = threading.Thread(
        target=collector.run_continuous,
        args=(FETCH_INTERVAL,),
        daemon=True
    )
    collector_thread.start()
    
    # Wait for initial data
    logger.info("Waiting for initial data collection...")
    time.sleep(15)
    
    while not os.path.isfile(CSV_PATH):
        logger.info("Waiting for CSV file to be created...")
        time.sleep(2)
    
    logger.info("✓ CSV file detected, starting Pathway producer...")
    time.sleep(2)
    
    try:
        start_pathway_producer(CSV_PATH)
    except KeyboardInterrupt:
        logger.info("Stopping producer...")
        collector.stop()
        logger.info("Producer stopped successfully")


if __name__ == "__main__":
    main()
