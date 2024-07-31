import asyncio
import json
import httpx
from nested_lookup import nested_lookup
from parsel import Selector
import os
import time
import csv


# create HTTPX client with headers that resemble a web browser
class Scraper:
    
    def __init__(self) -> None:
        self.http_client = httpx.AsyncClient(
            http2=True,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "Accept-Language": "en-US,en;q=0.9",
                "Cache-Control": "no-cache",
            },
        )
        self.base_url = "https://stockx.com/"

    def _parse_nextjs(self, html: str) -> dict:
        """extract nextjs cache from page"""
        selector = Selector(html)
        data = selector.css("script#__NEXT_DATA__::text").get()
        if not data:
            data = selector.css("script[data-name=query]::text").get()
            # print (data)
            data = data.split("=", 1)[-1].strip().strip(";")
        data = json.loads(data)
        return data

    async def scrape_product(self, url: str, product) -> dict:
        """scrape a single stockx product page for product data"""
        for i in range(1, 26):
            if i == 1:
                scrape_url = url
            else :
                scrape_url = url + "?page=" + str(i)
                
            response = await self.http_client.get(scrape_url)
            print (response.status_code)
            print (response.text)
            assert response.status_code == 200
            data = self._parse_nextjs(response.text)
            self._save_json(data, product + str(i))
            time.sleep(5)

    def _save_json(self, data, file_name):
        json_data = json.dumps(data)
        f = open(self.base_folder + file_name + '.json', 'wb')
        f.write(json_data.encode('utf-8'))


class StockXScraper(Scraper):                   
    
    def __init__(self) -> None:
        super().__init__()
        self.list_of_products = [
            "watches",
            "shoes",
            "apparel",
            "sneakers",
            # "electronics",
            # "collectibles"
        ]
        self.base_folder = "products/"
        
    async def scrape_products_info(self):
        for product in self.list_of_products:
            product_list_url = self.base_url + product
            await self.scrape_product(product_list_url, product)


class ScrapeProduct(Scraper):

    def __init__(self) -> None:                            
        super().__init__()
        self.base_product_folder = "products/"
        self.base_folder = "products_details/"

    async def scrape_product_info(self):
        for file_name in os.listdir(self.base_product_folder):
            f = open(self.base_product_folder + file_name)
            data = json.load(f)
            products = nested_lookup('edges', data)
            
            for product in products:
                for item in product:
                    print (item['node']['urlKey'])
                    url_key = item['node']['urlKey']
                    await self.scrape_product_detail(url_key)


    async def scrape_product_detail(self, url_key):
        if url_key is not None:
            scrape_url = self.base_url + url_key
            response = await self.http_client.get(scrape_url, timeout=30.0)
            print (response.status_code)
            if response.status_code == 200:
                data = self._parse_nextjs(response.text)
                self._save_json(data, url_key)
            if response.status_code == 403:
                time.sleep(300)
            time.sleep(15)

    def generate_csv_report(self):
        with open('result.csv', 'w', newline='') as file:
            writer = csv.writer(file,delimiter=';')
            writer.writerow(['title', 'primary title', 'secondary title', 'url key', 'condition', 'last price', 'lowest bid', 'highest bid', 'number of bids'])

            for file_name in os.listdir(self.base_folder):
                f = open(self.base_folder + file_name)
                data = json.load(f)
                product_info = nested_lookup('product', data)[0]
                product_title = product_info['title']
                product_primary_title = product_info['primaryTitle']
                product_secondary_title = product_info['secondaryTitle']
                product_condition = product_info['condition']
                product_url_key = product_info['urlKey']
                product_last_price = product_info['market']['salesInformation']['lastSale']
                product_lowest_bids = product_info['market']['state']['lowestAsk']
                product_highest_bids = product_info['market']['state']['highestBid']
                product_no_bids = product_info['market']['state']['numberOfBids']
                writer.writerow(
                    [
                        product_title,
                        product_primary_title,
                        product_secondary_title,
                        product_url_key,
                        product_condition,
                        product_last_price,
                        product_lowest_bids,
                        product_highest_bids,
                        product_no_bids
                    ]
                )

if __name__ == "__main__":
    stockx_scraper_client = StockXScraper()
    asyncio.run(stockx_scraper_client.scrape_products_info())
    product_scraper = ScrapeProduct()
    # asyncio.run(product_scraper.scrape_product_info())
    product_scraper.generate_csv_report()
