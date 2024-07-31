import asyncio
import json
import math
from typing import Dict, List
import httpx

from nested_lookup import nested_lookup
from parsel import Selector

# create HTTPX client with headers that resemble a web browser
client = httpx.AsyncClient(
    http2=True,
    follow_redirects=True,
    limits=httpx.Limits(max_connections=3),  # keep this low to avoid being blocked
    headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
    },
)

# From previous chapter:
def parse_nextjs(html: str) -> dict:
    """extract nextjs cache from page"""
    selector = Selector(html)
    data = selector.css("script#__NEXT_DATA__::text").get()
    if not data:
        data = selector.css("script[data-name=query]::text").get()
        data = data.split("=", 1)[-1].strip().strip(";")
    data = json.loads(data)
    return data


async def scrape_search(url: str, max_pages: int = 25) -> List[Dict]:
    """Scrape StockX search"""
    print(f"scraping first search page: {url}")
    first_page = await client.get(url)
    assert first_page.status_code == 200, "scrape was blocked"  # this should be retried, handled etc.

    # parse first page for product search data and total amount of pages:
    data = parse_nextjs(first_page.text)
    json_data = json.dumps(data)
    f = open('scrape_single_2.json', 'wb')
    f.write(json_data.encode('utf-8'))

# example run
result = asyncio.run(scrape_search("https://stockx.com/burberry-grainy-leather-international-bifold-wallet-black", max_pages=2))
print(json.dumps(result, indent=2))
