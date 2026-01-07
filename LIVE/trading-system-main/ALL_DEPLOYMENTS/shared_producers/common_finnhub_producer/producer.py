"""
Common Finnhub Stock Data Producer

This unified producer handles real-time stock/crypto data from Finnhub WebSocket.
It merges functionality from:
- chronos_deploy_main/finnhub_producer
- portfolio_2/producer (live streaming portion)

Features:
- WebSocket connection to Finnhub
- Support for multiple symbols (stocks and crypto)
- Configurable via environment variables
- Publishes to 'stock_data' Kafka topic

Output Schema (JSON):
{
    "s": str,   # symbol
    "p": float, # price
    "t": int,   # timestamp (ms)
    "v": float, # volume
    "r": float  # return (optional, 0.0 if not available)
}
"""

import os
import json
import asyncio
import time
import logging
from typing import List, Dict, Optional
from abc import abstractmethod

import aiohttp
from aiohttp.client_ws import ClientWebSocketResponse
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
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9090")
SYMBOLS = os.getenv("FINNHUB_SYMBOLS", "BINANCE:BTCUSDT").split(",")

# Kafka settings
RDKAFKA_SETTINGS = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
    "group.id": "common_finnhub_producer",
    "session.timeout.ms": "6000",
}

TOPIC_NAME = "stock_data"


class AIOHttpWebSocketSubject(pw.io.python.ConnectorSubject):
    """Base class for WebSocket connections using aiohttp."""
    
    def __init__(self, url: str):
        super().__init__()
        self._url = url
    
    def run(self):
        async def consume():
            retry_count = 0
            max_retries = 10
            
            while retry_count < max_retries:
                try:
                    async with aiohttp.ClientSession() as session:
                        logger.info(f"Connecting to WebSocket...")
                        async with session.ws_connect(self._url) as ws:
                            retry_count = 0  # Reset on successful connection
                            await self._on_open(ws)
                            
                            async for msg in ws:
                                if msg.type == aiohttp.WSMsgType.CLOSE:
                                    logger.warning("WebSocket closed by server")
                                    break
                                elif msg.type == aiohttp.WSMsgType.ERROR:
                                    logger.error(f"WebSocket error: {msg.data}")
                                    break
                                else:
                                    result = await self.on_ws_message(msg, ws)
                                    for row in result:
                                        self.next_json(row)
                                        
                except aiohttp.ClientError as e:
                    logger.error(f"Connection error: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                
                retry_count += 1
                wait_time = min(30, 2 ** retry_count)
                logger.info(f"Reconnecting in {wait_time}s (attempt {retry_count}/{max_retries})...")
                await asyncio.sleep(wait_time)
            
            logger.error("Max retries reached. Exiting.")
        
        asyncio.new_event_loop().run_until_complete(consume())

    @abstractmethod
    async def on_ws_message(self, msg, ws: ClientWebSocketResponse) -> List[Dict]:
        ...

    @abstractmethod
    async def _on_open(self, ws: ClientWebSocketResponse):
        ...


class FinnhubSubject(AIOHttpWebSocketSubject):
    """Finnhub WebSocket connector for real-time stock/crypto data."""
    
    def __init__(self, api_key: str, symbols: List[str]):
        if not api_key:
            raise ValueError("FINNHUB_API_KEY is required")
        
        url = f"wss://ws.finnhub.io?token={api_key}"
        self._symbols = symbols
        self._last_prices: Dict[str, float] = {}
        super().__init__(url)

    async def _on_open(self, ws: ClientWebSocketResponse):
        logger.info("Finnhub WebSocket opened. Subscribing to symbols...")
        for symbol in self._symbols:
            await ws.send_json({"type": "subscribe", "symbol": symbol})
            logger.info(f"✓ Subscribed to {symbol}")
    
    async def on_ws_message(self, msg, ws: ClientWebSocketResponse) -> List[Dict]:
        if msg.type == aiohttp.WSMsgType.TEXT:
            payload = json.loads(msg.data)
            
            if payload.get("type") == "trade":
                trade_data = payload.get("data", [])
                results = []
                
                for trade in trade_data:
                    symbol = trade.get("s")
                    price = float(trade.get("p", 0))
                    timestamp = int(trade.get("t", 0))
                    volume = float(trade.get("v", 0))
                    
                    # Calculate return
                    prev_price = self._last_prices.get(symbol)
                    if prev_price and prev_price > 0:
                        ret = (price - prev_price) / prev_price
                    else:
                        ret = 0.0
                    
                    self._last_prices[symbol] = price
                    
                    results.append({
                        "s": symbol,
                        "p": price,
                        "t": timestamp,
                        "v": volume,
                        "r": ret
                    })
                
                return results
                
            elif payload.get("type") == "ping":
                logger.debug("Finnhub ping received")
                
            elif payload.get("type") == "error":
                logger.error(f"Finnhub error: {payload.get('msg')}")
                
        return []


class StockAggregatesSchema(pw.Schema):
    """Schema for stock data output."""
    s: str      # symbol
    p: float    # price
    t: int      # timestamp (ms)
    v: float    # volume
    r: float    # return


def main():
    """Main entry point for the Finnhub producer."""
    
    logger.info("=" * 70)
    logger.info("COMMON FINNHUB PRODUCER")
    logger.info("=" * 70)
    logger.info(f"Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
    logger.info(f"Topic: {TOPIC_NAME}")
    logger.info(f"Symbols: {SYMBOLS}")
    logger.info("=" * 70)
    
    if not FINNHUB_API_KEY:
        raise ValueError("FINNHUB_API_KEY environment variable is required")
    
    # Wait for Kafka to be ready
    logger.info("Waiting for Kafka to be ready...")
    time.sleep(5)
    
    # Create Finnhub subject
    finnhub_subject = FinnhubSubject(
        api_key=FINNHUB_API_KEY,
        symbols=SYMBOLS
    )
    
    # Create Pathway table from WebSocket
    stock_table = pw.io.python.read(
        finnhub_subject,
        schema=StockAggregatesSchema,
        autocommit_duration_ms=1000
    )
    
    # Write to Kafka
    pw.io.kafka.write(
        stock_table,
        RDKAFKA_SETTINGS,
        topic_name=TOPIC_NAME,
        format="json"
    )
    
    logger.info(f"✓ Producer initialized. Streaming to '{TOPIC_NAME}'...")
    
    # Run Pathway
    pw.run()


if __name__ == "__main__":
    main()
