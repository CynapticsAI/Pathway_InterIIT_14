import os
import pathway as pw
import json
import asyncio
import aiohttp
from aiohttp.client_ws import ClientWebSocketResponse
from dotenv import load_dotenv
import time
from abc import abstractmethod

class AIOHttpWebSocketSubject(pw.io.python.ConnectorSubject):
    def __init__(self, url: str):
        super().__init__()
        self._url = url
    
    def run(self):
        async def consume():
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(self._url) as ws:
                    while True:
                        await self._on_open(ws)
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.CLOSE:
                                break
                            else:
                                result = await self.on_ws_message(msg,ws)
                                for row in result:
                                    self.next_json(row)
        asyncio.new_event_loop().run_until_complete(consume())

    @abstractmethod
    async def on_ws_message(self, msg, ws: ClientWebSocketResponse) -> list[dict]:
        ...

    @abstractmethod
    async def _on_open(self, ws: ClientWebSocketResponse):
        ...


class FinnhubSubject(AIOHttpWebSocketSubject):
    _symbols: list[str]

    def __init__(self, api_key: str, symbols: list[str]):
        url = f"wss://ws.finnhub.io?token={api_key}"
        self._symbols = symbols
        super().__init__(url)

    async def _on_open(self, ws: ClientWebSocketResponse):
        print("Finnhub connection opened. Subscribing to symbols...")
        for symbol in self._symbols:
            await ws.send_json({"type": "subscribe", "symbol": symbol})
            print(f"Subscribed to {symbol}")
    
    async def on_ws_message(self, msg, ws: ClientWebSocketResponse) -> list[dict]:
        if msg.type == aiohttp.WSMsgType.TEXT:
            payload = json.loads(msg.data)

            if payload.get("type") == "trade":
                trade_data = payload.get("data", [])
                if trade_data:
                    return [trade_data[0]]
            elif payload.get("type") == "ping":
                print("Finnhub ping received")
            else:
                raise RuntimeError(payload.get("msg"))
        return []

load_dotenv()

API_KEY = os.getenv("FINNHUB_API_KEY") or ""
symbols = ["NVDA", "AAPL", "MSFT", "GOOGL"]
if API_KEY == "":
    raise Exception("no API_KEY in .env.sample")

print("Waiting for kafka to startup.....")
time.sleep(2)
rdkafka_settings = {
    "bootstrap.servers": "kafka:9092",
    "group.id": "pathway_consumer_group",
    "session.timeout.ms": "6000",
}

class StockAggregates(pw.Schema):
    s: str
    p: float
    t: int  
    v: float

subject  = FinnhubSubject(api_key=API_KEY,symbols=symbols)

table = pw.io.python.read(subject, schema=StockAggregates,autocommit_duration_ms=1000)
pw.io.kafka.write(table, rdkafka_settings, topic_name="stock_data", format="json")

output_path = "../output/highValue.jsonl"

#pw.io.jsonlines.write(table, output_path)

pw.run()
