"""
Common Sentiment Producer

This unified producer handles sentiment analysis from Finviz news.
It merges functionality from:
- portfolio_2/producer/sentiment.py

Features:
- Polls Finviz for ticker-specific news
- Calculates VADER sentiment scores
- Uses EWMA for score smoothing
- Publishes to 'sentiment_scores' Kafka topic

Output Schema (JSON):
{
    "symbol": str,           # stock symbol
    "sentiment_score": float, # EWMA smoothed score [-1, 1]
    "t": int                 # timestamp (ms)
}
"""

import os
import json
import asyncio
import time
import logging
from datetime import datetime, timezone
from typing import List, Dict

import aiohttp
from bs4 import BeautifulSoup
import pandas as pd
import pathway as pw
from dotenv import load_dotenv
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Download VADER lexicon
try:
    nltk.download("vader_lexicon", quiet=True)
except:
    pass

# Initialize sentiment analyzer
sia = SentimentIntensityAnalyzer()

# Configuration from environment
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9090")
SENTIMENT_ALPHA = float(os.getenv("SENTIMENT_ALPHA", "0.05"))
SENTIMENT_POLL_INTERVAL = float(os.getenv("SENTIMENT_POLL_INTERVAL", "60"))

# Try to load tickers from CSV or environment
TICKERS = os.getenv("SENTIMENT_TICKERS", "TSLA,AAPL,MSFT,NVDA").split(",")

# Kafka settings
RDKAFKA_SETTINGS = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
    "group.id": "common_sentiment_producer",
    "session.timeout.ms": "6000",
}

TOPIC_NAME = "sentiment_scores"
JSONL_FILE = "/app/output/sentiment_live.jsonl"

# Global state for EWMA scores
ticker_scores: Dict[str, float] = {ticker.strip(): 0.0 for ticker in TICKERS}


class ScoreOutputSubject(pw.io.python.ConnectorSubject):
    """Subject for pushing sentiment scores to Pathway."""
    
    def run(self):
        while True:
            time.sleep(10)
    
    def push(self, data: Dict):
        self.next_json(data)


class FinvizSentimentSubject(pw.io.python.ConnectorSubject):
    """Polls Finviz for news and calculates sentiment scores."""
    
    def __init__(self, tickers: List[str], poll_interval: float = 60.0):
        super().__init__()
        self._tickers = [t.strip().upper() for t in tickers]
        self._poll_interval = poll_interval
        self._last_keys: set = set()
        self._headers = {"User-Agent": "Mozilla/5.0"}

    def run(self):
        async def poll_loop():
            async with aiohttp.ClientSession(headers=self._headers) as session:
                while True:
                    logger.info(f"Polling sentiment for {len(self._tickers)} tickers...")
                    
                    for ticker in self._tickers:
                        news_found = False
                        url = f"https://finviz.com/quote.ashx?t={ticker}"
                        
                        try:
                            async with session.get(url, timeout=10) as resp:
                                if resp.status == 200:
                                    html = await resp.text()
                                    articles = self._parse_news(html, ticker)
                                    
                                    if articles:
                                        news_found = True
                                        for article in articles:
                                            score_data = self._process_article(article)
                                            self.next_json(score_data)
                                            
                        except Exception as e:
                            logger.error(f"Error fetching {ticker}: {e}")
                        
                        # If no news, send heartbeat with current score
                        if not news_found:
                            current_score = ticker_scores.get(ticker, 0.0)
                            self.next_json({
                                "symbol": ticker,
                                "sentiment_score": current_score,
                                "t": int(datetime.now(timezone.utc).timestamp() * 1000)
                            })
                        
                        await asyncio.sleep(0.5)
                    
                    await asyncio.sleep(self._poll_interval)
        
        asyncio.new_event_loop().run_until_complete(poll_loop())

    def _parse_news(self, html: str, ticker: str) -> List[Dict]:
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find(id="news-table")
        
        if not table:
            return []
        
        articles = []
        for row in table.find_all("tr"):
            tds = row.find_all("td")
            if len(tds) < 2:
                continue
            
            link = tds[1].find("a")
            if not link:
                continue
            
            title = link.get_text(strip=True)
            key = f"{ticker}|{title}"
            
            if key in self._last_keys:
                continue
            
            self._last_keys.add(key)
            articles.append({"title": title, "ticker": ticker})
        
        # Prevent memory leak
        if len(self._last_keys) > 5000:
            self._last_keys = set(list(self._last_keys)[-3000:])
        
        return articles

    def _process_article(self, article: Dict) -> Dict:
        """Process article and calculate EWMA sentiment score."""
        global ticker_scores
        
        ticker = article["ticker"]
        title = article["title"]
        
        # Get VADER compound score
        compound = sia.polarity_scores(title)["compound"]
        
        # Get current EWMA score
        current_val = ticker_scores.get(ticker, 0.0)
        
        # Update EWMA
        new_val = SENTIMENT_ALPHA * compound + (1 - SENTIMENT_ALPHA) * current_val
        ticker_scores[ticker] = new_val
        
        # Calculate display score [0, 100]
        display_score = (new_val + 1) / 2 * 100
        
        logger.info(f"🔥 {ticker}: {display_score:.2f} | {title[:40]}...")
        
        return {
            "symbol": ticker,
            "sentiment_score": new_val,
            "t": int(datetime.now(timezone.utc).timestamp() * 1000)
        }


class SentimentSchema(pw.Schema):
    """Schema for sentiment score output."""
    symbol: str
    sentiment_score: float
    t: int


def main():
    """Main entry point for the Sentiment producer."""
    
    logger.info("=" * 70)
    logger.info("COMMON SENTIMENT PRODUCER")
    logger.info("=" * 70)
    logger.info(f"Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
    logger.info(f"Topic: {TOPIC_NAME}")
    logger.info(f"Tickers: {TICKERS}")
    logger.info(f"EWMA Alpha: {SENTIMENT_ALPHA}")
    logger.info(f"Poll Interval: {SENTIMENT_POLL_INTERVAL}s")
    logger.info("=" * 70)
    
    # Create output directory
    os.makedirs(os.path.dirname(JSONL_FILE), exist_ok=True)
    
    # Wait for Kafka to be ready
    logger.info("Waiting for Kafka to be ready...")
    time.sleep(5)
    
    # Create sentiment subject
    sentiment_subject = FinvizSentimentSubject(
        tickers=TICKERS,
        poll_interval=SENTIMENT_POLL_INTERVAL
    )
    
    # Create Pathway table
    sentiment_table = pw.io.python.read(
        sentiment_subject,
        schema=SentimentSchema,
        format="json",
        autocommit_duration_ms=1000
    )
    
    # Write to Kafka
    pw.io.kafka.write(
        sentiment_table,
        RDKAFKA_SETTINGS,
        topic_name=TOPIC_NAME,
        format="json"
    )
    
    # Also write to JSONL for debugging
    pw.io.jsonlines.write(sentiment_table, JSONL_FILE)
    
    logger.info(f"✓ Producer initialized. Streaming to '{TOPIC_NAME}'...")
    
    # Run Pathway
    pw.run()


if __name__ == "__main__":
    main()
