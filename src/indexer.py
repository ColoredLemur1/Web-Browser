import json
import re
from bs4 import BeautifulSoup


class Indexer:
    def __init__(self):
        self.index = {}

    def build(self, pages):
        """Word to url postings from html pages dict"""
        self.index = {}
        for url, html in pages.items():
            text = BeautifulSoup(html, "html.parser").get_text()
            tokens = re.findall(r"[a-zA-Z]+", text)
            for position, token in enumerate(tokens):
                word = token.lower()
                if word not in self.index:
                    self.index[word] = {}
                if url not in self.index[word]:
                    self.index[word][url] = {"frequency": 0, "positions": []}
                self.index[word][url]["frequency"] += 1
                self.index[word][url]["positions"].append(position)

    def save(self, path):
        """Serialize index to JSON at path"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.index, f)

    def load(self, path):
        """Restore index from JSON file at path"""
        with open(path, "r", encoding="utf-8") as f:
            self.index = json.load(f)
