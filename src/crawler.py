import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from collections import deque


class Crawler:
    def __init__(self, delay=6, verbose=False):
        self.delay = delay
        self.verbose = verbose
        self.visited = set()
        self._robot_parsers = {}

    def fetch(self, url):
        """Fetch single url, return html on success, none otherwise"""
        if url in self.visited:
            return None
        if not self._can_fetch(url):
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
        """Breadth first crawl on same domain, return url to html map"""
        pages = {}
        base_netloc = urlparse(start_url).netloc
        enqueued = {start_url}
        frontier = deque([start_url])

        while frontier:
            url = frontier.popleft()
            html = self.fetch(url)
            if html is None:
                continue
            pages[url] = html
            if self.verbose:
                print(f"  [{len(pages)}] {url}")
            for link in self._extract_links(html, url):
                if urlparse(link).netloc == base_netloc and link not in enqueued:
                    enqueued.add(link)
                    frontier.append(link)

        return pages

    def _extract_links(self, html, base_url):
        """Extract absolute urls from anchors, strip fragments"""
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for anchor in soup.find_all("a", href=True):
            full_url = urljoin(base_url, anchor["href"]).split("#")[0]
            if full_url:
                links.append(full_url)
        return links

    def _can_fetch(self, url):
        """Check robots allow fetch for url"""
        netloc = urlparse(url).netloc
        if netloc not in self._robot_parsers:
            self._robot_parsers[netloc] = self._get_robot_parser(url)
        return self._robot_parsers[netloc].can_fetch("*", url)

    def _get_robot_parser(self, url):
        """Load and parse robots rules for url domain"""
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        parser = RobotFileParser()
        parser.set_url(robots_url)
        try:
            response = requests.get(robots_url)
            if response.status_code == 200:
                parser.parse(response.text.splitlines())
            else:
                parser.allow_all = True
        except Exception:
            parser.allow_all = True
        return parser
