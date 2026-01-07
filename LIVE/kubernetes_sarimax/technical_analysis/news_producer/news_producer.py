import os
import pathway as pw
import asyncio
import aiohttp
import csv
import io
from datetime import datetime, timezone, timedelta
from typing import Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

FINVIZ_API = os.getenv("FINVIZ_API") or ""
def _split_filters(f_str: str):
    return [x for x in (f_str or "").split(",") if x]

def _join_filters(filters):
    seen, out = set(), []
    for f in filters:
        f = f.strip()
        if f and f not in seen:
            seen.add(f); out.append(f)
    return ",".join(out)

def finviz_export_update(
    url: str,
    add_filters=None,
    remove_filters=None,
    tickers=None,
    view=None,
):
    add_filters = add_filters or []
    remove_filters = set(remove_filters or [])
    tickers = tickers or []

    u = urlparse(url)
    q = parse_qs(u.query, keep_blank_values=True)

    current_f = q.get("f", [""])[0]
    filt = _split_filters(current_f)
    filt = [x for x in filt if x not in remove_filters]
    filt.extend(add_filters)
    if filt:
        q["f"] = [_join_filters(filt)]
    elif "f" in q:
        del q["f"]

    if tickers:
        q["t"] = [",".join(tickers)]

    if view is not None:
        q["v"] = [str(view)]

    cleaned = {}
    for k, v in q.items():
        if k == "auth":
            cleaned[k] = v
        elif v and any(s.strip() for s in v):
            cleaned[k] = v

    new_query = urlencode(cleaned, doseq=True)
    return urlunparse((u.scheme, u.netloc, u.path, u.params, new_query, u.fragment))

def finviz_groups_update(
    url: str,
    group: str = "sector",
    view: str = "121",
    order: str | None = None
):
    u = urlparse(url)
    q = parse_qs(u.query, keep_blank_values=True)

    q["g"] = [group]
    q["v"] = [str(view)]
    if order is not None:
        q["o"] = [order]

    cleaned = {}
    for k, v in q.items():
        if k == "auth":
            cleaned[k] = v
        elif v and any(s.strip() for s in v):
            cleaned[k] = v

    new_query = urlencode(cleaned, doseq=True)
    return urlunparse((u.scheme, u.netloc, u.path, u.params, new_query, u.fragment))

TICKER = "NVDA"

BASE_URL_SCREENER = (
    f"https://elite.finviz.com/export.ashx?auth={FINVIZ_API}"
)

EXPORT_URL = finviz_export_update(
    url=BASE_URL_SCREENER,
    add_filters=[f"ticker_{TICKER.lower()}"],
    tickers=TICKER,
    view="111"
)

BASE_URL_GROUPS = (
    f"https://elite.finviz.com/grp_export.ashx?auth={FINVIZ_API}"
)

GROUPS_URL = finviz_groups_update(
    url=BASE_URL_GROUPS,
    group="sector",
    view="121"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
}

class AIOHttpPollingSubject(pw.io.python.ConnectorSubject):
    _url: str
    _poll_interval: float
    _headers: dict

    def __init__(self, url: str, poll_interval: float = 15.0, headers: dict = None):
        super().__init__()
        self._url = url
        self._poll_interval = poll_interval
        self._headers = headers or {}

    def run(self):
        async def poll_loop():
            async with aiohttp.ClientSession(headers=self._headers) as session:
                while True:
                    try:
                        async with session.get(self._url) as resp:
                            resp.raise_for_status()
                            data = await resp.text()
                            result = await self.on_poll(data)
                            for row in result:
                                self.next_json(row)
                    except Exception as e:
                        print(f"Poll error: {e}")
                    await asyncio.sleep(self._poll_interval)

        asyncio.new_event_loop().run_until_complete(poll_loop())

    async def on_poll(self, data: str) -> list[dict]:
        raise NotImplementedError("Override this method to process polled data.")

class FinvizSnapshotSubject(AIOHttpPollingSubject):
    _ticker: str

    def __init__(self, url: str, ticker: str, poll_interval: float = 15.0, headers: dict = None):
        super().__init__(url, poll_interval, headers)
        self._ticker = ticker

    async def on_poll(self, data: str) -> list[dict]:
        rows = list(csv.DictReader(io.StringIO(data)))
        if not rows:
            return []

        row = next((r for r in rows if r.get("Ticker", "").upper() == self._ticker.upper()), rows[0])

        def to_float(v):
            try:
                return float(str(v).replace(",", "").strip())
            except:
                return None

        snap = {
            "time_utc": datetime.now(timezone.utc).isoformat(timespec='microseconds'),
            "ticker": self._ticker,
            "price": to_float(row.get("Price") or row.get("Last")),
            "daily_open": to_float(row.get("Open")),
            "daily_high": to_float(row.get("High")),
            "daily_low": to_float(row.get("Low")),
            "volume": to_float(row.get("Volume")) or 0.0,
        }
        if snap["price"] is None:
            return []
        return [snap]

class FinvizNewsSubject(AIOHttpPollingSubject):
    _ticker: str
    _last_keys: set

    def __init__(self, ticker: str, poll_interval: float = 60.0, headers: dict = None):
        url = f"https://finviz.com/quote.ashx?t={ticker}"
        super().__init__(url, poll_interval, headers)
        self._ticker = ticker
        self._last_keys = set()

    async def on_poll(self, data: str) -> list[dict]:
        soup = BeautifulSoup(data, "html.parser")
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
            href = headline_link["href"] if (headline_link and headline_link.has_attr("href")) else ""
            source = source_span.get_text(strip=True) if source_span else ""

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
                print(f"Using fallback timestamp for unparseable date: {dt_text}")
                dt_parsed = datetime.now(timezone.utc).replace(microsecond=0)

            dt_parsed = dt_parsed.replace(tzinfo=timezone.utc)

            items.append({
                "dt_utc": dt_parsed.isoformat(),
                "title": title,
                "url": href,
            "source": source
            })

        new_items = []
        for it in items:
            key = it["url"] or (it["dt_utc"] + "|" + it["title"])
            if key in self._last_keys:
                continue
            self._last_keys.add(key)
            it["ticker"] = self._ticker
            new_items.append(it)

        if len(self._last_keys) > 200:
            self._last_keys = set(list(self._last_keys)[-200:])

        return new_items

class FinvizGroupsSubject(AIOHttpPollingSubject):
    def __init__(self, url: str, poll_interval: float = 30.0, headers: dict = None):
        super().__init__(url, poll_interval, headers)

    async def on_poll(self, data: str) -> list[dict]:
        rows = list(csv.reader(io.StringIO(data)))
        if not rows:
            return []

        header = [h.replace('.', '').replace(' ', '_').strip() for h in rows[0]]

        data_rows = rows[1:]
        ts = datetime.now(timezone.utc).isoformat()

        result = []
        for row in data_rows:
            d = dict(zip(header, row))
            d["timestamp_utc"] = ts

            for field in ['No', 'Name', 'No_in_group', 'Market_Cap', 'Perf_Week']:
                if field not in d:
                    d[field] = None

            def to_int(v):
                try:
                    return int(v.strip()) if v and v.strip() else None
                except:
                    return None

            def to_float(v):
                try:
                    return float(v.strip().replace('%', '').replace(',', '')) if v and v.strip() else None
                except:
                    return None

            d["No"] = to_int(d["No"])
            d["No_in_group"] = to_int(d["No_in_group"])
            d["Market_Cap"] = to_float(d["Market_Cap"])
            d["Perf_Week"] = to_float(d["Perf_Week"])
            d["Name"] = d["Name"] or ""

            result.append(d)
        return result

class SnapshotSchema(pw.Schema):
    time_utc: str
    ticker: str
    price: Optional[float] = pw.column_definition(default_value=None)
    daily_open: Optional[float] = pw.column_definition(default_value=None)
    daily_high: Optional[float] = pw.column_definition(default_value=None)
    daily_low: Optional[float] = pw.column_definition(default_value=None)
    volume: float = pw.column_definition(default_value=0.0)

class NewsSchema(pw.Schema):
    dt_utc: str
    ticker: str
    source: str
    title: str
    url: str

class GroupsSchema(pw.Schema):
    timestamp_utc: str
    No: Optional[int] = pw.column_definition(default_value=None)
    Name: str = pw.column_definition(default_value="")
    No_in_group: Optional[int] = pw.column_definition(default_value=None)
    Market_Cap: Optional[float] = pw.column_definition(default_value=None)
    Perf_Week: Optional[float] = pw.column_definition(default_value=None)

snapshot_subject = FinvizSnapshotSubject(
    url=EXPORT_URL,
    ticker=TICKER,
    poll_interval=15.0,
    headers=HEADERS
)

news_subject = FinvizNewsSubject(
    ticker=TICKER,
    poll_interval=60.0,
    headers=HEADERS
)

groups_subject = FinvizGroupsSubject(
    url=GROUPS_URL,
    poll_interval=30.0,
    headers=HEADERS
)

snapshots = pw.io.python.read(
    snapshot_subject,
    schema=SnapshotSchema,
    format="json",
    autocommit_duration_ms=50
)

news = pw.io.python.read(
    news_subject,
    schema=NewsSchema,
    format="json",
    autocommit_duration_ms=50
)

groups = pw.io.python.read(
    groups_subject,
    schema=GroupsSchema,
    format="json",
    autocommit_duration_ms=50
)

snapshots = snapshots.filter(pw.this.price.is_not_none() & pw.this.volume.is_not_none())

snapshots = snapshots.with_columns(time=pw.this.time_utc.dt.strptime(fmt="%Y-%m-%dT%H:%M:%S.%f%z"))

bar_interval_seconds = 5
bars = snapshots.windowby(
    pw.this.time,
    window=pw.temporal.tumbling(duration=timedelta(seconds=bar_interval_seconds)),
    instance=pw.this.ticker
).reduce(
    start_time=pw.reducers.min(pw.this.time),
    end_time=pw.reducers.max(pw.this.time),
    ticker=pw.reducers.any(pw.this.ticker),
    open=pw.reducers.argmin(pw.this.time, pw.this.price),
    high=pw.reducers.max(pw.this.price),
    low=pw.reducers.min(pw.this.price),
    close=pw.reducers.argmax(pw.this.time, pw.this.price),
    volume_delta=pw.reducers.max(pw.this.volume) - pw.reducers.min(pw.this.volume)
)

pw.io.csv.write(bars, f"/app/output/bars_{TICKER}_{bar_interval_seconds}s.csv")
pw.io.csv.write(news, f"/app/output/news_{TICKER}.csv")
#pw.io.csv.write(groups, "/app/output/groups_snapshots.csv")

NEWS_TOPIC = "news_data"
rdkafka_settings={
            "bootstrap.servers": "kafka:9092",
            "group.id": "stock_calculator",  # New group ID
            "session.timeout.ms": "6000",
        }

pw.io.kafka.write(news, rdkafka_settings , topic_name=NEWS_TOPIC, format="json")

pw.run()