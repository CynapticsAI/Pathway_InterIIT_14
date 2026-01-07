import pathway as pw
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from datetime import datetime, timezone
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import os
import nltk
import pandas as pd
import time

# -----------------------------
# SETUP + CONFIG
# -----------------------------
nltk.download("vader_lexicon", quiet=True)
sia = SentimentIntensityAnalyzer()

ALPHA = 0.05 
JSONL_FILE = "/app/output/sentiment_live.jsonl"
TOPIC_NAME = "sentiment_scores"

rdkafka_settings = {
    "bootstrap.servers": "kafka:9090",
    "group.id": "sentiment_producer",
    "session.timeout.ms": "6000",
}

# --- Load Stocks ---
print("Loading stock list...", flush=True)
try:
    df_stocks = pd.read_csv("master_stock_list.csv")
    df_stocks.columns = df_stocks.columns.str.strip()
    df_stocks['symbol'] = df_stocks['symbol'].str.strip()
    TICKERS = df_stocks['symbol'].unique().tolist()
    print(f"Loaded {len(TICKERS)} tickers.", flush=True)
except Exception as e:
    print(f"Error loading master_stock_list.csv: {e}")
    TICKERS = ["TSLA", "AAPL", "MSFT", "NVDA"]

# Global State: Persist the last known sentiment score
# Initialize to 0.0 (Neutral)
ticker_scores = {ticker: 0.0 for ticker in TICKERS}

if not os.path.exists(JSONL_FILE):
    with open(JSONL_FILE, "w") as f: pass

# -----------------------------
# CONNECTORS
# -----------------------------
class ScoreOutputSubject(pw.io.python.ConnectorSubject):
    def run(self):
        while True: time.sleep(10)
    
    def push(self, data):
        self.next_json(data)

class FinvizNewsSubject(pw.io.python.ConnectorSubject):
    def __init__(self, tickers, poll_interval=60.0):
        self._tickers = tickers
        self._poll_interval = poll_interval
        self._last_keys = set()
        super().__init__()

    def run(self):
        async def poll_loop():
            async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as session:
                while True:
                    print(f"--- Polling cycle for {len(self._tickers)} stocks ---", flush=True)
                    
                    for tick in self._tickers:
                        news_found = False
                        url = f"https://finviz.com/quote.ashx?t={tick}"
                        
                        try:
                            async with session.get(url, timeout=5) as resp:
                                if resp.status == 200:
                                    html = await resp.text()
                                    rows = await self.on_poll(html, tick)
                                    if rows:
                                        news_found = True
                                        for r in rows: self.next_json(r)
                        except Exception: 
                            pass 
                        
                        # LOGIC CHANGE: If no news, send a "Heartbeat" with the previous score
                        # This keeps the stream alive without faking news.
                        if not news_found:
                            self.next_json({
                                "title": "HEARTBEAT", 
                                "ticker": tick,
                                "is_heartbeat": True 
                            })
                        
                        await asyncio.sleep(1.0) 
                    
                    await asyncio.sleep(self._poll_interval)
        
        asyncio.run(poll_loop())

    async def on_poll(self, html, ticker):
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find(id="news-table")
        if not table: return []
        
        articles = []
        for row in table.find_all("tr"):
            tds = row.find_all("td")
            if len(tds) < 2: continue
            
            link = tds[1].find("a")
            if not link: continue
            
            title = link.get_text(strip=True)
            key = f"{ticker}|{title}"
            
            if key in self._last_keys: continue
            self._last_keys.add(key)
            
            articles.append({"title": title, "ticker": ticker, "is_heartbeat": False})
            
        if len(self._last_keys) > 5000:
            self._last_keys = set(list(self._last_keys)[-3000:])
        return articles

# -----------------------------
# LOGIC
# -----------------------------
def process_text(title, ticker, is_heartbeat, subject_ref):
    global ticker_scores
    
    # 1. Get Last Known Score
    current_val = ticker_scores.get(ticker, 0.0)

    # 2. Update if Real News, Maintain if Heartbeat
    if not is_heartbeat:
        compound = sia.polarity_scores(title)["compound"]
        # Update EWMA
        new_val = ALPHA * compound + (1 - ALPHA) * current_val
        ticker_scores[ticker] = new_val
        source_label = "finviz"
    else:
        # Keep the exact same score
        new_val = current_val
        source_label = "persist"

    display_score = (new_val + 1) / 2 * 100
    
    # 3. Prepare Data (ALWAYS with FRESH timestamp)
    # This ensures Pathway closes the window even if values don't change
    current_time_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    
    data = {
        "symbol": ticker,
        "sentiment_score": new_val,
        "t": current_time_ms,
        "timestamp_str": datetime.now(timezone.utc).isoformat(),
        "source": source_label,
        "title": title,
        "display_score": display_score
    }
    
    # Log only real news to avoid spamming console
    if not is_heartbeat:
        print(f"{ticker}: {display_score:.2f} | {title[:30]}", flush=True)
        # Only write REAL news to the JSONL history file
        with open(JSONL_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")
    
    # BUT... Push EVERYTHING to Kafka so the Portfolio engine keeps running
    subject_ref.push({
        "symbol": data["symbol"],
        "sentiment_score": data["sentiment_score"],
        "t": data["t"]
    })

# -----------------------------
# MAIN
# -----------------------------
class NewsSchema(pw.Schema):
    title: str
    ticker: str
    is_heartbeat: bool

class ScoreSchema(pw.Schema):
    symbol: str
    sentiment_score: float
    t: int

def main():
    print(f"Starting Sentiment (Real + Persistence)...", flush=True)
    kafka_subject = ScoreOutputSubject()
    news_subject = FinvizNewsSubject(TICKERS, poll_interval=60)
    
    def on_news(key, row, time, is_addition):
        if is_addition:
            process_text(row["title"], row["ticker"], row["is_heartbeat"], kafka_subject)

    news_stream = pw.io.python.read(news_subject, schema=NewsSchema, format="json", autocommit_duration_ms=100)
    pw.io.subscribe(news_stream, on_news)
    
    score_stream = pw.io.python.read(kafka_subject, schema=ScoreSchema, format="json")
    pw.io.kafka.write(score_stream, rdkafka_settings, topic_name=TOPIC_NAME, format="json")
    pw.run()

if __name__ == "__main__":
    main()