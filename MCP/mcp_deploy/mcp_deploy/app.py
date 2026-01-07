import os
import yaml
import asyncio
from typing import Optional
from datetime import datetime
import httpx
import trafilatura
from dateutil import parser as dateparser
from limits import parse
from limits.aio.storage import MemoryStorage
from limits.aio.strategies import MovingWindowRateLimiter
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row
from typing import Literal, List
from pydantic import BaseModel

import aiohttp
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
load_dotenv()

SERPER_API_KEY = os.environ["SERPER_API_KEY"]
SERPER_SEARCH_ENDPOINT = "https://google.serper.dev/search"
SERPER_NEWS_ENDPOINT = "https://google.serper.dev/news"
HEADERS = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}

storage = MemoryStorage()
limiter = MovingWindowRateLimiter(storage)
rate_limit = parse("360/hour")

with open("app.yaml", "r") as f:
    cfg = yaml.safe_load(f)

mcp = FastMCP("mcp-client", port = cfg['port'], host = "0.0.0.0")
SERVER_URL_SEC = cfg['live_rag_server_sec']
SERVER_URL_TAX = cfg['live_rag_server_tax']



aconn : psycopg.AsyncConnection
async def init_connection(postgres_str : str):
    global aconn
    aconn = await psycopg.AsyncConnection.connect(
        postgres_str,
    )

SECTOR_LITERAL = Literal[
    "Energy",
    "Materials",
    "Industrials",
    "Consumer Discretionary",
    "Consumer Staples",
    "Health Care",
    "Financials",
    "Information Technology",
    "Communication Services",
    "Utilities",
    "Real Estate"
]


CHRONOS_PRED_URL = cfg['pred_url']
PORTFOLIO_URL = cfg['portfolio_url']
MACRODATA_URL = cfg['macrodata_url']
STRATEGY_URL = cfg['strategy_url']


async def _fetch(session, url, headers, retries=3):
    while retries > 0:
        try:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                return await response.json()

        except (aiohttp.ServerTimeoutError, aiohttp.ClientError) as e:
            retries -= 1
            if retries == 0:
                return "Couldnot Process request"
            
            await asyncio.sleep(1)

@mcp.tool()
async def get_portfolio(user_id : str):
    """
    MCP Tool

    Retrieve the stored portfolio for the specified user.

    Args:
        user_id (str): Unique identifier of the user.

    Returns:
        list[dict]: Portfolio allocation as a list of objects with `symbol` and `weight` fields.
    """
    port = [
               { "symbol": "AAPL", "weight": 0.5 },
               { "symbol": "MSFT", "weight": 0.5 }
           ] #return dummy for now
    return port

@mcp.tool()
async def get_macro(sectors : List[SECTOR_LITERAL]):
    headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
    }
    sector_urls = [MACRODATA_URL + '/' + sector for sector in sectors]
    timeout = aiohttp.ClientTimeout(
        total=cfg['timeout_macro']['total'],            
        connect=cfg['timeout_macro']['connect'],           
        sock_read=cfg['timeout_macro']['sock_read'],
        sock_connect=cfg['timeout_macro']['sock_connect']
    )
    async with aiohttp.ClientSession(timeout= timeout) as session:
        results = await asyncio.gather(*[_fetch(session, url, headers) for url in sector_urls], return_exceptions= True)
        return results


@mcp.tool()
async def get_ohlc(tickers : List[Literal["BINANCE:BTCUSDT", "BINANCE:ETHUSDT", "BINANCE:SOLUSDT", "BINANCE:BNBUSDT", "BINANCE:XRPUSDT"]]) -> list:
    """
    get_ohlc(tickers : list[dict]) -> list

    Retreives the current OHLCV data for a list of stocks provided

    Parameters:
        tickers (list[str]): the list of tickers for which the current stock data the user wants
    
    Returns:
        list : the raw OHLCV data for the tickers
    """

    global aconn
    async with aconn.cursor(row_factory= dict_row) as cur:
            await cur.execute("SELECT * FROM ohlc_bars WHERE symbol IN (%s)", tickers)

            rows = await cur.fetchall()
        
    return rows


@mcp.tool()
async def get_preds(tickers : List[Literal["BINANCE:BTCUSDT", "BINANCE:ETHUSDT"]], limit : int = 5) -> list:
    """
    get_preds(tickers : list[dict]) -> list

    Retreives the current predictions data for a list of stocks provided

    Parameters:
        tickers (list[str]): the list of tickers for which the current predictions data the user wants
    
    Returns:
        list : the raw predictions data for the tickers
    """
    headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
    }

    timeout = aiohttp.ClientTimeout(
        total=cfg['timeout_preds']['total'],            
        connect=cfg['timeout_preds']['connect'],           
        sock_read=cfg['timeout_preds']['sock_read'],
        sock_connect=cfg['timeout_preds']['sock_connect']
    )
    urls = [f"{CHRONOS_PRED_URL}/prediction?limit={limit}"]
    async with aiohttp.ClientSession(timeout= timeout) as session:
        results = await asyncio.gather(*[_fetch(session, url, headers) for url in urls], return_exceptions= True)
        return results


@mcp.tool()
async def live_rag_sec(query : str, k : int = 2, retries = 2):
    """
    live_rag(query: str, k: int = 2) → dict

    Retrieve top-k relevant chunks for a query using the remote RAG retrieval endpoint.

    Parameters:
        query (str): the natural language input query
        k     (int): how many top results to retrieve (default: 2)

    Returns:
        dict: the raw JSON result from POST /v1/retrieve
    """

    out = []
    headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
    }
    timeout = aiohttp.ClientTimeout(
        total=cfg['timeout_rag']['total'],            
        connect=cfg['timeout_rag']['connect'],           
        sock_read=cfg['timeout_rag']['sock_read'],
        sock_connect=cfg['timeout_rag']['sock_connect']
    )
    async with aiohttp.ClientSession(timeout= timeout) as session:
        while retries>0:
            try:
                async with session.post(url = f"{SERVER_URL_SEC}/v1/retrieve", json = {"query" : query, "k" : k}, headers= headers) as response:
                    result = await response.json()
            

                for res in result:
                    out.append({'text' : res['text'], 'document' : res['metadata']['path'], 'page' : res['metadata']['pages']})

                return out
            except (aiohttp.ServerTimeoutError, aiohttp.ClientError) as e:
                retries -= 1
                if retries == 0:
                    return "Couldnot Process request"
                
                await asyncio.sleep(1)
    

@mcp.tool()
async def live_rag_tax(query : str, k : int = 2, retries = 2):
    """
    live_rag_tax(query: str, k: int = 2) → dict

    Retrieve top-k relevant chunks for a query using the remote RAG retrieval endpoint.

    Parameters:
        query (str): the natural language input query
        k     (int): how many top results to retrieve (default: 2)

    Returns:
        dict: the raw JSON result from POST /v1/retrieve
    """

    out = []
    headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
    }

    timeout = aiohttp.ClientTimeout(
        total=cfg['timeout_rag']['total'],            
        connect=cfg['timeout_rag']['connect'],           
        sock_read=cfg['timeout_rag']['sock_read'],
        sock_connect=cfg['timeout_rag']['sock_connect']
    )
    async with aiohttp.ClientSession(timeout= timeout) as session:
        while retries>0:
            try:
                async with session.post(url = f"{SERVER_URL_TAX}/v1/retrieve", json = {"query" : query, "k" : k}, headers= headers) as response:
                    result = await response.json()
            

                for res in result:
                    out.append({'text' : res['text'], 'document' : res['metadata']['path'], 'page' : res['metadata']['pages']})

                return out
            except (aiohttp.ServerTimeoutError, aiohttp.ClientError) as e:
                retries -= 1
                if retries == 0:
                    return "Couldnot Process request"
                
                await asyncio.sleep(1)

async def list_document_tax(retries = 2):
    headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
    }
    timeout = aiohttp.ClientTimeout(
        total=cfg['timeout_rag']['total'],            
        connect=cfg['timeout_rag']['connect'],           
        sock_read=cfg['timeout_rag']['sock_read'],
        sock_connect=cfg['timeout_rag']['sock_connect']
    )

    async with aiohttp.ClientSession(timeout= timeout) as session:
        while retries>0:
            try:
                async with session.post(url = f"{SERVER_URL_TAX}/v2/list_documents", json = {}, headers= headers) as response:
                    result = await response.json()
            
                return result
            except (aiohttp.ServerTimeoutError, aiohttp.ClientError) as e:
                retries -= 1
                if retries == 0:
                    return "Couldnot Process request"
                
                await asyncio.sleep(1)

@mcp.tool()
async def list_documents_sec(retries = 2):
    """
    Tool: list_documents_sec

    Description:
        Returns a list of available SEC document paths from the SEC RAG service.

    Input:
        retries (optional, int): Number of retry attempts if the request fails.

    Output:
        - On success: List of strings representing document paths.
        - On failure: "Couldnot Process request"
    """
    
    headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
    }
    timeout = aiohttp.ClientTimeout(
        total=cfg['timeout_rag']['total'],            
        connect=cfg['timeout_rag']['connect'],           
        sock_read=cfg['timeout_rag']['sock_read'],
        sock_connect=cfg['timeout_rag']['sock_connect']
    )

    async with aiohttp.ClientSession(timeout= timeout) as session:
        while retries>0:
            try:
                async with session.post(url = f"{SERVER_URL_SEC}/v2/list_documents", json = {}, headers= headers) as response:
                    out = []
                    result = await response.json()
                    for res in result:
                        out.append(res['path'])

            
                return out
            except (aiohttp.ServerTimeoutError, aiohttp.ClientError) as e:
                retries -= 1
                if retries == 0:
                    return "Couldnot Process request"
                
                await asyncio.sleep(1)


@mcp.tool()
async def list_documents_tax(retries = 2):
    """
    Tool: list_documents_tax

    Description:
        Returns a list of available TAX document paths from the TAX RAG service.

    Input:
        retries (optional, int): Number of retry attempts if the request fails.

    Output:
        - On success: List of strings representing document paths.
        - On failure: "Couldnot Process request"
    """
    
    headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
    }
    timeout = aiohttp.ClientTimeout(
        total=cfg['timeout_rag']['total'],            
        connect=cfg['timeout_rag']['connect'],           
        sock_read=cfg['timeout_rag']['sock_read'],
        sock_connect=cfg['timeout_rag']['sock_connect']
    )

    async with aiohttp.ClientSession(timeout= timeout) as session:
        while retries>0:
            try:
                async with session.post(url = f"{SERVER_URL_TAX}/v2/list_documents", json = {}, headers= headers) as response:
                    out = []
                    result = await response.json()
                    for res in result:
                        out.append(res['path'])

            
                return out
            except (aiohttp.ServerTimeoutError, aiohttp.ClientError) as e:
                retries -= 1
                if retries == 0:
                    return "Couldnot Process request"
                
                await asyncio.sleep(1)


@mcp.tool()
async def search_web(
    query: str, search_type: str = "search", num_results: Optional[int] = 4
) -> str:
    """
    Search the web for information or fresh news, returning extracted content.

    This tool can perform two types of searches:
    - "search" (default): General web search for diverse, relevant content from various sources
    - "news": Specifically searches for fresh news articles and breaking stories

    Use "news" mode when looking for:
    - Breaking news or very recent events
    - Time-sensitive information
    - Current affairs and latest developments
    - Today's/this week's happenings

    Use "search" mode (default) for:
    - General information and research
    - Technical documentation or guides
    - Historical information
    - Diverse perspectives from various sources

    Args:
        query (str): The search query. This is REQUIRED. Examples: "apple inc earnings",
                    "climate change 2024", "AI developments"
        search_type (str): Type of search. This is OPTIONAL. Default is "search".
                          Options: "search" (general web search) or "news" (fresh news articles).
                          Use "news" for time-sensitive, breaking news content.
        num_results (int): Number of results to fetch. This is OPTIONAL. Default is 4.
                          Range: 1-20. More results = more context but longer response time.

    Returns:
        str: Formatted text containing extracted content with metadata (title,
             source, date, URL, and main text) for each result, separated by dividers.
             Returns error message if API key is missing or search fails.

    Examples:
        - search_web("OpenAI GPT-5", "news") - Get 5 fresh news articles about OpenAI
        - search_web("python tutorial", "search") - Get 4 general results about Python (default count)
        - search_web("stock market today", "news", 10) - Get 10 news articles about today's market
        - search_web("machine learning basics") - Get 4 general search results (all defaults)
    """
    if not SERPER_API_KEY:
        return "Error: SERPER_API_KEY environment variable is not set. Please set it to use this tool."

    if num_results is None:
        num_results = 4
    num_results = max(1, min(30, num_results))

    if search_type not in ["search", "news"]:
        search_type = "search"

    try:
        if not await limiter.hit(rate_limit, "global"):
            print(f"[{datetime.now().isoformat()}] Rate limit exceeded")
            return "Error: Rate limit exceeded. Please try again later (limit: 500 requests per hour)."

        endpoint = (
            SERPER_NEWS_ENDPOINT if search_type == "news" else SERPER_SEARCH_ENDPOINT
        )

        payload = {"q": query, "num": num_results}
        if search_type == "news":
            payload["type"] = "news"
            payload["page"] = 1

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(endpoint, headers=HEADERS, json=payload)

        if resp.status_code != 200:
            return f"Error: Search API returned status {resp.status_code}. Please check your API key and try again."

        if search_type == "news":
            results = resp.json().get("news", [])
        else:
            results = resp.json().get("organic", [])

        if not results:
            return f"No {search_type} results found for query: '{query}'. Try a different search term or search type."

        urls = [r["link"] for r in results]
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            tasks = [client.get(u) for u in urls]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

        chunks = []
        successful_extractions = 0

        for meta, response in zip(results, responses):
            if isinstance(response, Exception):
                continue

            body = trafilatura.extract(
                response.text, include_formatting=False, include_comments=False
            )

            if not body:
                continue

            successful_extractions += 1
            print(
                f"[{datetime.now().isoformat()}] Successfully extracted content from {meta['link']}"
            )

            if search_type == "news":
                try:
                    date_str = meta.get("date", "")
                    if date_str:
                        date_iso = dateparser.parse(date_str, fuzzy=True).strftime(
                            "%Y-%m-%d"
                        )
                    else:
                        date_iso = "Unknown"
                except Exception:
                    date_iso = "Unknown"

                chunk = (
                    f"## {meta['title']}\n"
                    f"**Source:** {meta.get('source', 'Unknown')}   "
                    f"**Date:** {date_iso}\n"
                    f"**URL:** {meta['link']}\n\n"
                    f"{body.strip()}\n"
                )
            else:
                domain = meta["link"].split("/")[2].replace("www.", "")

                chunk = (
                    f"## {meta['title']}\n"
                    f"**Domain:** {domain}\n"
                    f"**URL:** {meta['link']}\n\n"
                    f"{body.strip()}\n"
                )

            chunks.append(chunk)

        if not chunks:
            return f"Found {len(results)} {search_type} results for '{query}', but couldn't extract readable content from any of them. The websites might be blocking automated access."

        result = "\n---\n".join(chunks)
        summary = f"Successfully extracted content from {successful_extractions} out of {len(results)} {search_type} results for query: '{query}'\n\n---\n\n"

        print(
            f"[{datetime.now().isoformat()}] Extraction complete: {successful_extractions}/{len(results)} successful for query '{query}'"
        )

        return summary + result

    except Exception as e:
        return f"Error occurred while searching: {str(e)}. Please try again or check your query."



@mcp.tool()
async def search_web_whitelist(
    query: str, search_type: str = "search", num_results: Optional[int] = 4) -> str:
    """
    Search the web for information or fresh news, returning extracted content.

    This tool can perform two types of searches:
    - "search" (default): General web search for diverse, relevant content from various sources
    - "news": Specifically searches for fresh news articles and breaking stories

    Use "news" mode when looking for:
    - Breaking news or very recent events
    - Time-sensitive information
    - Current affairs and latest developments
    - Today's/this week's happenings

    Use "search" mode (default) for:
    - General information and research
    - Technical documentation or guides
    - Historical information
    - Diverse perspectives from various sources

    Args:
        query (str): The search query. This is REQUIRED. Examples: "apple inc earnings",
                    "climate change 2024", "AI developments"
        search_type (str): Type of search. This is OPTIONAL. Default is "search".
                          Options: "search" (general web search) or "news" (fresh news articles).
                          Use "news" for time-sensitive, breaking news content.
        num_results (int): Number of results to fetch. This is OPTIONAL. Default is 4.
                          Range: 1-20. More results = more context but longer response time.
        whitelist_path (str): Path to JSON file containing whitelisted domains. This is OPTIONAL.
                             If provided, query will be restricted to these domains only.

    Returns:
        str: Formatted text containing extracted content with metadata (title,
             source, date, URL, and main text) for each result, separated by dividers.
             Returns error message if API key is missing or search fails.

    Examples:
        - search_web("OpenAI GPT-5", "news") - Get 5 fresh news articles about OpenAI
        - search_web("python tutorial", "search") - Get 4 general results about Python (default count)
        - search_web("stock market today", "news", 10) - Get 10 news articles about today's market
        - search_web("machine learning basics") - Get 4 general search results (all defaults)
        - search_web("earnings report", "search", 5, "whitelist.json") - Search only whitelisted domains
    """


    if not SERPER_API_KEY:
        return "Error: SERPER_API_KEY environment variable is not set. Please set it to use this tool."

    if num_results is None:
        num_results = 4
    num_results = max(1, min(30, num_results))

    if search_type not in ["search", "news"]:
        search_type = "search"

    # Load whitelist domains if path is provided
    whitelist_domains = [
        "sec.gov",
        "irs.gov",
        "yahoo.com",
        "bloomberg.com",
        "reuters.com",
        "cnbc.com",
        "marketwatch.com",
        "investopedia.com",
        "ft.com",
        "morningstar.com",
        "nasdaq.com",
        "nyse.com",
        "stlouisfed.org",
        "bea.gov",
        "home.treasury.gov",
        "spglobal.com",
        "moodys.com",
        "koyfin.com",
        "tickertape.in"
    ]

    # Append site filter to query if whitelist is available
    original_query = query
    if whitelist_domains:
        site_filters = " OR ".join([f"site:{domain}" for domain in whitelist_domains])
        query = f"{query} ({site_filters})"
        print(f"[{datetime.now().isoformat()}] Modified query with {len(whitelist_domains)} domain filters")

    try:
        if not await limiter.hit(rate_limit, "global"):
            print(f"[{datetime.now().isoformat()}] Rate limit exceeded")
            return "Error: Rate limit exceeded. Please try again later (limit: 500 requests per hour)."

        endpoint = (
            SERPER_NEWS_ENDPOINT if search_type == "news" else SERPER_SEARCH_ENDPOINT
        )

        payload = {"q": query, "num": num_results}
        if search_type == "news":
            payload["type"] = "news"
            payload["page"] = 1

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(endpoint, headers=HEADERS, json=payload)

        if resp.status_code != 200:
            return f"Error: Search API returned status {resp.status_code}. Please check your API key and try again."

        if search_type == "news":
            results = resp.json().get("news", [])
        else:
            results = resp.json().get("organic", [])

        if not results:
            filter_msg = f" (filtered to {len(whitelist_domains)} whitelisted domains)" if whitelist_domains else ""
            return f"No {search_type} results found for query: '{original_query}'{filter_msg}. Try a different search term or search type."

        urls = [r["link"] for r in results]
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            tasks = [client.get(u) for u in urls]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

        chunks = []
        successful_extractions = 0

        for meta, response in zip(results, responses):
            if isinstance(response, Exception):
                continue

            body = trafilatura.extract(
                response.text, include_formatting=False, include_comments=False
            )

            if not body:
                continue

            successful_extractions += 1
            print(
                f"[{datetime.now().isoformat()}] Successfully extracted content from {meta['link']}"
            )

            if search_type == "news":
                try:
                    date_str = meta.get("date", "")
                    if date_str:
                        date_iso = dateparser.parse(date_str, fuzzy=True).strftime(
                            "%Y-%m-%d"
                        )
                    else:
                        date_iso = "Unknown"
                except Exception:
                    date_iso = "Unknown"

                chunk = (
                    f"## {meta['title']}\n"
                    f"*Source:* {meta.get('source', 'Unknown')}   "
                    f"*Date:* {date_iso}\n"
                    f"*URL:* {meta['link']}\n\n"
                    f"{body.strip()}\n"
                )
            else:
                domain = meta["link"].split("/")[2].replace("www.", "")

                chunk = (
                    f"## {meta['title']}\n"
                    f"*Domain:* {domain}\n"
                    f"*URL:* {meta['link']}\n\n"
                    f"{body.strip()}\n"
                )

            chunks.append(chunk)

        if not chunks:
            filter_msg = f" from {len(whitelist_domains)} whitelisted domains" if whitelist_domains else ""
            return f"Found {len(results)} {search_type} results for '{original_query}'{filter_msg}, but couldn't extract readable content from any of them. The websites might be blocking automated access."

        result = "\n---\n".join(chunks)
        filter_info = f" (filtered to {len(whitelist_domains)} whitelisted domains)" if whitelist_domains else ""
        summary = f"Successfully extracted content from {successful_extractions} out of {len(results)} {search_type} results for query: '{original_query}'{filter_info}\n\n---\n\n"

        print(
            f"[{datetime.now().isoformat()}] Extraction complete: {successful_extractions}/{len(results)} successful for query '{original_query}'"
        )

        return summary + result

    except Exception as e:
        return f"Error occurred while searching: {str(e)}. Please try again or check your query."


class RiskParameters(BaseModel):
    hurdle_rate: float = 0.0
    target_beta: Optional[float] = None
    max_sector_exposure: float = 0.30


@mcp.tool()
async def rebalance_portfolio(current_portfolio : list, strategy_name :Literal['CVaR', 'Omega', 'Mean-Variance'], risk_parameters : RiskParameters, retries = 2):
    """
    Rebalance a portfolio based on specified strategies and risk parameters.

    Args:
        portfolio (dict): Current portfolio holdings.
        strategy_name (List[Literal['CVaR', 'Omega', 'Mean-Variance']]): List of strategies to apply.
        risk_parameters [hurdle_rate, target_beta (optional), max_sector_exposure]: Risk constraints and parameters.

    Returns:
        dict: The rebalanced portfolio result or error message.
    """
    headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
    }

    timeout = aiohttp.ClientTimeout(
        total=cfg['timeout_port']['total'],            
        connect=cfg['timeout_port']['connect'],           
        sock_read=cfg['timeout_port']['sock_read'],
        sock_connect=cfg['timeout_port']['sock_connect']
    )

    data = {
        "user_id" : "John Doe",
        "strategy_name" : strategy_name,
        "risk_params" : risk_parameters.model_dump(mode='json'),
        "current_portfolio" : current_portfolio
    }

    async with aiohttp.ClientSession(timeout= timeout) as session:
        while retries>0:
            try:
                async with session.post(url = f"{PORTFOLIO_URL}/rebalance_portfolio", json = data, headers= headers) as response:
                    result = await response.json()
        
                return result
            except (aiohttp.ServerTimeoutError, aiohttp.ClientError) as e:
                retries -= 1
                if retries == 0:
                    return "Couldnot Process request"
                
                await asyncio.sleep(1)


@mcp.tool()
async def diversify_portfolio(current_portfolio : list, strategy_name : Literal['CVaR', 'Omega', 'Mean-Variance'], risk_parameters : RiskParameters, hard_to_borrow : list, retries = 2):
    """
    Diversify a portfolio using specified strategies, considering hard-to-borrow assets.

    Args:
        portfolio (list): Current portfolio holdings.
        strategy_name (List[Literal['CVaR', 'Omega', 'Mean-Variance']]): List of strategies to apply.
         risk_parameters [hurdle_rate, target_beta (optional), max_sector_exposure]: Risk constraints and parameters.
        hard_to_borrow (list): List of assets that are hard to borrow.

    Returns:
        dict: The diversified portfolio result or error message.
    """
    headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
    }

    timeout = aiohttp.ClientTimeout(
        total=cfg['timeout_port']['total'],            
        connect=cfg['timeout_port']['connect'],           
        sock_read=cfg['timeout_port']['sock_read'],
        sock_connect=cfg['timeout_port']['sock_connect']
    )

    data = {
        "user_id" : "John Doe",
        "strategy_name" : strategy_name,
        "risk_params" : risk_parameters.model_dump(mode='json'),
        "current_portfolio" : current_portfolio,
        "hard_to_borrow" : hard_to_borrow
    }

    async with aiohttp.ClientSession(timeout= timeout) as session:
        while retries>0:
            try:
                async with session.post(url = f"{PORTFOLIO_URL}/diversify_portfolio", json = data, headers= headers) as response:
                    result = await response.json()
        
                return result
            except (aiohttp.ServerTimeoutError, aiohttp.ClientError) as e:
                retries -= 1
                if retries == 0:
                    return "Couldnot Process request"
                
                await asyncio.sleep(1)


@mcp.tool()
async def create_portfolio(strategy_name :Literal['CVaR', 'Omega', 'Mean-Variance'], risk_parameters : RiskParameters, hard_to_borrow : list, retries = 2):
    """
    Create a new portfolio based on strategies and risk parameters.

    Args:
        strategy_name (List[Literal['CVaR', 'Omega', 'Mean-Variance']]): List of strategies to apply.
         risk_parameters [hurdle_rate, target_beta (optional), max_sector_exposure]: Risk constraints and parameters.
        hard_to_borrow (list): List of assets that are hard to borrow.

    Returns:
        dict: The created portfolio result or error message.
    """
    headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
    }

    timeout = aiohttp.ClientTimeout(
        total=cfg['timeout_port']['total'],            
        connect=cfg['timeout_port']['connect'],           
        sock_read=cfg['timeout_port']['sock_read'],
        sock_connect=cfg['timeout_port']['sock_connect']
    )

    data = {
        "user_id" : "John Doe",
        "strategy_name" : strategy_name,
        "risk_params" : risk_parameters.model_dump(mode='json'),
        "hard_to_borrow" : hard_to_borrow
    }

    async with aiohttp.ClientSession(timeout= timeout) as session:
        while retries>0:
            try:
                async with session.post(url = f"{PORTFOLIO_URL}/create_portfolio", json = data, headers= headers) as response:
                    result = await response.json()
        
                return result
            except (aiohttp.ServerTimeoutError, aiohttp.ClientError) as e:
                retries -= 1
                if retries == 0:
                    return "Couldnot Process request"
                
                await asyncio.sleep(1)


@mcp.tool()
async def get_backtest_data(ticker : Literal['MSFT', 'TSLA', 'AMZN']):

    #currently only supports 3 stocks
    """
    Retrieves a predefined backtest dataset URL for a supported ticker symbol.

    Parameters:
        ticker (Literal['MSFT', 'TSLA', 'AMZN']):
            The stock symbol used to select a matching dataset reference.

    Returns:
        str | None:
            The URL of the corresponding CSV file if found; otherwise returns None.

    Notes:
        - Only predefined tickers are supported.
        - No network request is made in this function; it simply returns a stored URL.
    """
    tickers = {
    "tickers": [
        {
        "symbol": "MSFT",
        "url": "https://v3b.fal.media/files/b/0a855a22/M0aF-PmlTajqtvugi7xED_data_MSFT_2021-09_to_2022-09.csv"
        },
        {
        "symbol": "TSLA",
        "url": "https://v3b.fal.media/files/b/0a855a1f/mkDyURJzR8NxFH5OXWJWE_data_TSLA_sorted.csv"
        },
        {
        "symbol": "AMZN",
        "url": "https://v3b.fal.media/files/b/0a855a24/-xHnypvyW3i8zDTBepG0R_data_AMZN_2021-09_to_2022-09.csv"
        }
        ]
        }

    for data in tickers['tickers']:
        if data['symbol'] == ticker:
            return data['url']
    
    return None




@mcp.tool()
async def create_strategy(csv_url : str):
    retries = 2
    """
    Sends a request to the Strategy Optimization service using a
    Genetic Programming (GP) algorithm and returns the generated strategy results.

    Parameters:
        csv_url (str):
            The URL path to the CSV dataset used as input for strategy evaluation.

    Returns:
        dict | str:
            The optimization response payload if processing succeeds. 
            A failure string is returned if retries are exhausted.

    Behavior:
        - Makes a POST request to the `/gp` endpoint.
        - Retry logic is applied on connection-related failures.
        - Uses timeout configuration from `cfg['timeout_strat']`.

    Errors:
        - Returns `"Couldnot Process request"` if all retry attempts fail.
    """

    headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
    }

    timeout = aiohttp.ClientTimeout(
        total=cfg['timeout_strat']['total'],            
        connect=cfg['timeout_strat']['connect'],           
        sock_read=cfg['timeout_strat']['sock_read'],
        sock_connect=cfg['timeout_strat']['sock_connect']
    )

    data = {
        "csv_url": csv_url,
        "csv_path": None,
        "out_dir": "stvgp_out"
    }

    async with aiohttp.ClientSession(timeout= timeout) as session:
        while retries>0:
            try:
                async with session.post(url = f"{STRATEGY_URL}/gp", json = data, headers= headers) as response:
                    result = await response.json()
        
                return result
            except (aiohttp.ServerTimeoutError, aiohttp.ClientError) as e:
                retries -= 1
                if retries == 0:
                    return "Couldnot Process request"
                
                await asyncio.sleep(1)


@mcp.tool()
async def optimize_strategy(csv_url : str):
    retries = 2
    """
    Triggers a strategy optimization request using a Genetic Algorithm (GA)
    based approach and returns the evaluation results.

    Parameters:
        csv_url (str):
            Public dataset URL path used for training and validation.

    Returns:
        dict | str:
            Response payload from the optimizer if successful,
            otherwise a failure notice string when retry attempts are exhausted.

    Behavior:
        - Makes a POST request to the `/ga` strategy endpoint.
        - Uses internally defined train/validation window sizes.
        - Includes retry and timeout logic for network robustness.

    Errors:
        - `"Couldnot Process request"` returned upon repeated connection failures.
    """

    headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
    }

    timeout = aiohttp.ClientTimeout(
        total=cfg['timeout_strat']['total'],            
        connect=cfg['timeout_strat']['connect'],           
        sock_read=cfg['timeout_strat']['sock_read'],
        sock_connect=cfg['timeout_strat']['sock_connect']
    )

    data = {
        "csv_url": csv_url,
        "csv_path": None,
        "train_months": 6,
        "valid_months" : 1
    }

    async with aiohttp.ClientSession(timeout= timeout) as session:
        while retries>0:
            try:
                async with session.post(url = f"{STRATEGY_URL}/ga", json = data, headers= headers) as response:
                    result = await response.json()
        
                return result
            except (aiohttp.ServerTimeoutError, aiohttp.ClientError) as e:
                retries -= 1
                if retries == 0:
                    return "Couldnot Process request"
                
                await asyncio.sleep(1)

def main():
    acon : psycopg.AsyncConnection
    postgres_str = cfg['pg_conninfo']
    postgres_str_front = cfg['pg_conninfo_user']
    asyncio.run(init_connection(postgres_str))
    asyncio.run(init_connection(postgres_str_front))
    mcp.run(transport= 'streamable-http')

if __name__ == "__main__":
    main()
