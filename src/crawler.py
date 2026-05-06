import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


class Crawler:
    def __init__(self, delay=6):
        self.delay = delay
        self.visited = set()

    def fetch(self, url):
        """Fetch a single URL, returns HTML string on success"""
        if url in self.visited:
            return None

        time.sleep(self.delay)

        try:
            response = requests.get(url)
            if response.status_code != 200:
                return None
            self.visited.add(url)
            return response.text
        except Exception:
            return None

    def crawl(self, start_url):
        """Crawl all pages reachable via pagination from start_url this returns a dictionary mapping {url: html_text}"""
        pages = {}
        url = start_url

        while url and url not in self.visited:
            html = self.fetch(url)
            if html is None:
                break
            pages[url] = html
            url = self._next_page_url(html, url)

        return pages

    def _next_page_url(self, html, base_url):
        """Extract the next pagination URL from an HTML page"""
        soup = BeautifulSoup(html, "html.parser")
        next_li = soup.find("li", class_="next")
        if next_li:
            anchor = next_li.find("a")
            if anchor and anchor.get("href"):
                return urljoin(base_url, anchor["href"])
        return None
