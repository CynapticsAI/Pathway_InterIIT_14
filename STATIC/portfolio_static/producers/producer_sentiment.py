import pathway as pw
import pandas as pd
import time
import os
import json
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

# --- SETUP ---
try:
    nltk.download("vader_lexicon", quiet=True)
except:
    print("Warning: NLTK download failed (network?). VADER might fail.")

sia = SentimentIntensityAnalyzer()

TOPIC_NAME = "sentiment_scores"
DATA_DIR = "/app/data"
TWEETS_FILE = "stock_tweets.csv"
TARGET_STOCKS = ["TSLA", "BX", "NIO", "AMZN", "MSFT"]
START_DATE = "2021-09-01"
END_DATE = "2022-09-30"

RDKAFKA_SETTINGS = {
    "bootstrap.servers": "kafka:9092",
    "group.id": "sentiment_producer_csv",
    "session.timeout.ms": "6000",
}

class SentimentSchema(pw.Schema):
    symbol: str
    sentiment_score: float
    t: int

class TweetSubject(pw.io.python.ConnectorSubject):
    def __init__(self, records):
        super().__init__()
        self.records = records

    def run(self):
        print(f"📤 Streaming {len(self.records)} sentiment records...", flush=True)
        self.records.sort(key=lambda x: x["t"])
        
        for record in self.records:
            self.next_json(record)
            time.sleep(0.0005) # Sync roughly with stock producer
        print("✅ Sentiment Stream complete.")

def process_tweets():
    file_path = os.path.join(DATA_DIR, TWEETS_FILE)
    if not os.path.exists(file_path):
        print(f"❌ Sentiment file not found: {file_path}")
        return []

    print("📖 Reading Tweets CSV...")
    try:
        df = pd.read_csv(file_path)
        # Normalize columns
        df.columns = [c.lower().strip() for c in df.columns]
        
        # Mapping common column names
        date_col = next((c for c in ['date', 'timestamp', 'time'] if c in df.columns), None)
        
        # ✅ FIX: Added 'stock_name' to the search list to match your CSV
        sym_col = next((c for c in ['stock_symbol', 'ticker', 'symbol', 'stock_name'] if c in df.columns), None)
        
        txt_col = next((c for c in ['tweet', 'text', 'content'] if c in df.columns), None)

        if not (date_col and sym_col and txt_col):
            print(f"❌ Missing required columns. Found: {df.columns}")
            return []

        # Handle date parsing robustly
        try:
            df[date_col] = pd.to_datetime(df[date_col], dayfirst=True)
        except:
            df[date_col] = pd.to_datetime(df[date_col], format='mixed')
        
        # Filter Date & Stocks
        mask = (df[date_col] >= START_DATE) & \
               (df[date_col] <= END_DATE) & \
               (df[sym_col].isin(TARGET_STOCKS))
        df = df.loc[mask]
        
        processed_data = []
        print(f"🧠 Analyzing sentiment for {len(df)} tweets...")
        
        for _, row in df.iterrows():
            text = str(row.get(txt_col, ''))
            score = sia.polarity_scores(text)["compound"]
            
            processed_data.append({
                "symbol": row[sym_col],
                "sentiment_score": float(score),
                "t": int(row[date_col].timestamp() * 1000)
            })
            
        return processed_data

    except Exception as e:
        print(f"❌ Error processing tweets: {e}")
        return []

def main():
    print("⏳ Waiting 18s for Stock Producer to start...", flush=True)
    time.sleep(18) 
    
    records = process_tweets()
    
    # Pathway Connector
    subject = TweetSubject(records)
    t_stream = pw.io.python.read(subject, schema=SentimentSchema)
    pw.io.kafka.write(t_stream, RDKAFKA_SETTINGS, topic_name=TOPIC_NAME, format="json")
    pw.run()

if __name__ == "__main__":
    main()