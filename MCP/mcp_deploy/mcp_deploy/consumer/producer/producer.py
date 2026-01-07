import pathway as pw
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import os

# --- Configuration ---
TICKER = "TSLA"
KAFKA_TOPIC = "news_data"

# Smart Broker Selection:
# If running in Docker, it grabs "kafka:9092" from the env variable.
# If running locally on WSL, it defaults to "localhost:9092".
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")

class FinvizNewsSubject(pw.io.python.ConnectorSubject):
    def __init__(self, ticker: str, poll_interval: float = 60.0):
        self._ticker = ticker.upper()
        self._url = f"https://finviz.com/quote.ashx?t={self._ticker}"
        self._poll_interval = poll_interval
        self._last_keys = set()
        super().__init__()

    def run(self):
        async def poll_loop():
            # We use a generic user-agent to avoid being blocked by Finviz
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            
            async with aiohttp.ClientSession(headers=headers) as session:
                print(f"🚀 Producer started. Polling Finviz for {self._ticker}...")
                print(f"🔗 Connecting to Kafka at: {KAFKA_BROKER}")
                
                while True:
                    try:
                        async with session.get(self._url) as resp:
                            if resp.status == 200:
                                html = await resp.text()
                                result = await self.on_poll(html)
                                for row in result:
                                    self.next_json(row)
                                    print(f"   Found news: {row['title'][:40]}...")
                            else:
                                print(f"⚠️ Error fetching data: Status {resp.status}")
                    except Exception as e:
                        print(f"❌ Poll error: {e}")
                    
                    await asyncio.sleep(self._poll_interval)
        
        asyncio.new_event_loop().run_until_complete(poll_loop())

    async def on_poll(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find(id="news-table")
        if not table: return []

        articles = []
        for row in table.find_all("tr"):
            tds = row.find_all("td")
            if len(tds) < 2: continue
            
            dt_text = tds[0].get_text(strip=True)
            link = tds[1].find("a")
            title = link.get_text(strip=True) if link else ""
            url = link["href"] if link else ""
            source_span = tds[1].find("span")
            source = source_span.get_text(strip=True) if source_span else "Unknown"

            # Simple date handling for the demo
            dt_parsed = datetime.now(timezone.utc)

            key = url or title
            if key in self._last_keys: continue
            self._last_keys.add(key)

            articles.append({
                "dt_utc": dt_parsed.isoformat(),
                "title": title,
                "url": url,
                "ticker": self._ticker,
                "source": source
            })
        
        # Keep memory usage low by trimming cache
        if len(self._last_keys) > 500:
            self._last_keys = set(list(self._last_keys)[-200:])
            
        return articles

class NewsSchema(pw.Schema):
    dt_utc: str
    title: str
    url: str
    ticker: str
    source: str

# --- Pipeline ---
subject = FinvizNewsSubject(ticker=TICKER, poll_interval=60)
news_table = pw.io.python.read(subject, schema=NewsSchema, format="json", autocommit_duration_ms=100)

rdkafka_settings = {
    "bootstrap.servers": KAFKA_BROKER,
    "group.id": "producer_group",
    "session.timeout.ms": "6000",
}

# WRITE TO KAFKA
pw.io.kafka.write(news_table, rdkafka_settings, topic_name=KAFKA_TOPIC, format="json")

pw.run()