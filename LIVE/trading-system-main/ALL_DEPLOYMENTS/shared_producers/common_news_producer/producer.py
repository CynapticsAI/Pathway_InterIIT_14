"""
Common News Producer

This unified producer handles news data from Finviz.
It merges functionality from:
- chronos_deploy_main/news_producer

Features:
- Polls Finviz for ticker-specific news
- Polls Finviz for sector group data
- Configurable polling intervals
- Publishes to 'news_data' Kafka topic

Output Schema (JSON) for News:
{
    "dt_utc": str,     # datetime in ISO format
    "ticker": str,     # stock symbol
    "source": str,     # news source
    "title": str,      # headline
    "url": str         # article URL
}
"""

import os
import csv
import io
import asyncio
import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import aiohttp
from bs4 import BeautifulSoup
import pathway as pw
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

# Configuration from environment
FINVIZ_API_KEY = os.getenv("FINVIZ_API_KEY", "")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9090")
TICKERS = os.getenv("NEWS_TICKERS", "NVDA,AAPL,TSLA,MSFT").split(",")
NEWS_POLL_INTERVAL = float(os.getenv("NEWS_POLL_INTERVAL", "60"))

# Kafka settings
RDKAFKA_SETTINGS = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
    "group.id": "common_news_producer",
    "session.timeout.ms": "6000",
}

NEWS_TOPIC = "news_data"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


class AIOHttpPollingSubject(pw.io.python.ConnectorSubject):
    """Base class for HTTP polling connectors."""
    
    def __init__(self, poll_interval: float = 60.0, headers: dict = None):
        super().__init__()
        self._poll_interval = poll_interval
        self._headers = headers or {}

    def run(self):
        async def poll_loop():
            async with aiohttp.ClientSession(headers=self._headers) as session:
                while True:
                    try:
                        results = await self.poll(session)
                        for row in results:
                            self.next_json(row)
                    except Exception as e:
                        logger.error(f"Poll error: {e}")
                    
                    await asyncio.sleep(self._poll_interval)
        
        asyncio.new_event_loop().run_until_complete(poll_loop())

    async def poll(self, session: aiohttp.ClientSession) -> List[Dict]:
        raise NotImplementedError("Override this method")


class FinvizNewsSubject(AIOHttpPollingSubject):
    """Polls Finviz for news headlines for multiple tickers."""
    
    def __init__(self, tickers: List[str], poll_interval: float = 60.0, headers: dict = None):
        super().__init__(poll_interval, headers)
        self._tickers = [t.strip().upper() for t in tickers]
        self._last_keys: set = set()

    async def poll(self, session: aiohttp.ClientSession) -> List[Dict]:
        all_news = []
        
        for ticker in self._tickers:
            try:
                url = f"https://finviz.com/quote.ashx?t={ticker}"
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        news = self._parse_news(html, ticker)
                        all_news.extend(news)
                    else:
                        logger.warning(f"Failed to fetch news for {ticker}: HTTP {resp.status}")
                
                # Be nice to the server
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error fetching news for {ticker}: {e}")
        
        return all_news

    def _parse_news(self, html: str, ticker: str) -> List[Dict]:
        soup = BeautifulSoup(html, "html.parser")
        news_table = soup.find(id="news-table")
        
        if not news_table:
            return []
        
        items = []
        current_date = None
        
        for row in news_table.find_all("tr"):
            tds = row.find_all("td")
            if len(tds) < 2:
                continue
            
            dt_text = tds[0].get_text(strip=True)
            headline_link = tds[1].find("a")
            source_span = tds[1].find("span")
            
            title = headline_link.get_text(strip=True) if headline_link else ""
            href = headline_link.get("href", "") if headline_link else ""
            source = source_span.get_text(strip=True) if source_span else ""
            
            # Parse datetime
            try:
                if "AM" in dt_text or "PM" in dt_text:
                    if current_date is None:
                        dt_parsed = datetime.strptime(dt_text, "%b-%d-%y %I:%M%p")
                        current_date = dt_parsed.date()
                    else:
                        tm = datetime.strptime(dt_text, "%I:%M%p").time()
                        dt_parsed = datetime.combine(current_date, tm)
                else:
                    d = datetime.strptime(dt_text, "%b-%d-%y")
                    current_date = d.date()
                    continue
            except:
                dt_parsed = datetime.now(timezone.utc).replace(microsecond=0)
            
            dt_parsed = dt_parsed.replace(tzinfo=timezone.utc)
            
            # Deduplicate
            key = href or (dt_parsed.isoformat() + "|" + title)
            if key in self._last_keys:
                continue
            
            self._last_keys.add(key)
            
            items.append({
                "dt_utc": dt_parsed.isoformat(),
                "ticker": ticker,
                "source": source,
                "title": title,
                "url": href
            })
        
        # Prevent memory leak
        if len(self._last_keys) > 5000:
            self._last_keys = set(list(self._last_keys)[-3000:])
        
        return items


class NewsSchema(pw.Schema):
    """Schema for news data output."""
    dt_utc: str
    ticker: str
    source: str
    title: str
    url: str


def main():
    """Main entry point for the News producer."""
    
    logger.info("=" * 70)
    logger.info("COMMON NEWS PRODUCER")
    logger.info("=" * 70)
    logger.info(f"Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
    logger.info(f"Topic: {NEWS_TOPIC}")
    logger.info(f"Tickers: {TICKERS}")
    logger.info(f"Poll Interval: {NEWS_POLL_INTERVAL}s")
    logger.info("=" * 70)
    
    # Wait for Kafka to be ready
    logger.info("Waiting for Kafka to be ready...")
    time.sleep(5)
    
    # Create news subject
    news_subject = FinvizNewsSubject(
        tickers=TICKERS,
        poll_interval=NEWS_POLL_INTERVAL,
        headers=HEADERS
    )
    
    # Create Pathway table
    news_table = pw.io.python.read(
        news_subject,
        schema=NewsSchema,
        format="json",
        autocommit_duration_ms=1000
    )
    
    # Write to Kafka
    pw.io.kafka.write(
        news_table,
        RDKAFKA_SETTINGS,
        topic_name=NEWS_TOPIC,
        format="json"
    )
    
    logger.info(f"✓ Producer initialized. Streaming to '{NEWS_TOPIC}'...")
    
    # Run Pathway
    pw.run()


if __name__ == "__main__":
    main()
