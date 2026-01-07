import os
import pathway as pw
import json
import asyncio
import aiohttp
from aiohttp.client_ws import ClientWebSocketResponse
from dotenv import load_dotenv
import time
from abc import abstractmethod

load_dotenv()


class AIOHttpWebSocketSubject(pw.io.python.ConnectorSubject):
    def __init__(self, url: str):
        super().__init__()
        self._url = url

    def run(self):
        async def consume():
            while True:
                try:
                    async with aiohttp.ClientSession() as session:
                        print(f"Connecting to {self._url}...")
                        async with session.ws_connect(self._url) as ws:
                            await self._on_open(ws)
                            async for msg in ws:
                                if msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.ERROR):
                                    print("WebSocket connection closed/error.")
                                    break
                                else:
                                    try:
                                        result = await self.on_ws_message(msg, ws)
                                        for row in result:
                                            self.next_json(row)
                                    except Exception as e:
                                        print(f"Error processing message row: {e}")

                except Exception as e:
                    print(f"Connection failed: {e}. Retrying in 5s...")
                    await asyncio.sleep(5)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(consume())

    @abstractmethod
    async def on_ws_message(self, msg, ws: ClientWebSocketResponse) -> list[dict]:
        ...

    @abstractmethod
    async def _on_open(self, ws: ClientWebSocketResponse):
        ...


class FinnhubSubject(AIOHttpWebSocketSubject):
    _symbols: list[str]

    def __init__(self, api_key: str, symbols: list[str]):
        if not api_key:
            raise ValueError("API Key is missing")
        url = f"wss://ws.finnhub.io?token={api_key}"
        self._symbols = symbols
        super().__init__(url)

    async def _on_open(self, ws: ClientWebSocketResponse):
        print(f"Finnhub connection opened. Subscribing to {len(self._symbols)} symbols...")
        for symbol in self._symbols:
            try:
                await ws.send_json({"type": "subscribe", "symbol": symbol})
                print(f"Subscribed to {symbol}")
            except Exception as e:
                print(f"Failed to subscribe to {symbol}: {e}")

    async def on_ws_message(self, msg, ws: ClientWebSocketResponse) -> list[dict]:
        if msg.type == aiohttp.WSMsgType.TEXT:
            try:
                payload = json.loads(msg.data)

                if payload.get("type") == "trade":
                    return payload.get("data", [])

                elif payload.get("type") == "ping":
                    # print("Ping received")
                    pass
                elif payload.get("type") == "error":
                    print(f"Finnhub API Error: {payload.get('msg')}")
            except json.JSONDecodeError:
                print("Failed to decode JSON from Finnhub")

        return []



API_KEY = os.getenv("FINNHUB_API_KEY") or ""

STOCK_LIST_RAW = os.getenv("STOCK_LIST", "BINANCE:BTCUSDT")
try:
    symbols = json.loads(STOCK_LIST_RAW)
    if not isinstance(symbols, list):
        raise ValueError  # fallback
except (json.JSONDecodeError, ValueError):
    symbols = [s.strip() for s in STOCK_LIST_RAW.split(",") if s.strip()]

if not API_KEY:
    print("Error: FINNHUB_API_KEY not found in env.")

if not symbols:
    print("Warning: No symbols found to subscribe to.")

print("Waiting for Kafka to startup.....")
time.sleep(5)

rdkafka_settings = {
    "bootstrap.servers": "kafka:9092",
    "group.id": "pathway_finnhub_group",
    "session.timeout.ms": "6000",
}

class StockAggregates(pw.Schema):
    s: str 
    p: float 
    t: int 
    v: float  

subject = FinnhubSubject(api_key=API_KEY, symbols=symbols)

table = pw.io.python.read(subject, schema=StockAggregates, autocommit_duration_ms=1000)

pw.io.kafka.write(table, rdkafka_settings, topic_name=os.getenv("KAFKA_TOPIC", "stock_data"), format="json")

#start pathway
pw.run()