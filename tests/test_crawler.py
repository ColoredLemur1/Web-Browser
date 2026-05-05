from unittest.mock import patch, MagicMock, call
from src.crawler import Crawler


def make_response(status=200, text="<html></html>"):
    r = MagicMock()
    r.status_code = status
    r.text = text
    return r


PAGINATED_HTML = """
<html><body>
  <p>Some quote text here.</p>
  <li class="next"><a href="/page/2/">Next</a></li>
</body></html>
"""

LAST_PAGE_HTML = """
<html><body>
  <p>Last page quote.</p>
</body></html>
"""


def test_politeness_window_respected():
    """time.sleep is called with the configured delay on every fetch."""
    crawler = Crawler(delay=6)
    with patch("src.crawler.time.sleep") as mock_sleep, \
         patch("src.crawler.requests.get") as mock_get:
        mock_get.return_value = make_response(200, "<html></html>")
        crawler.fetch("https://quotes.toscrape.com/")
        mock_sleep.assert_called_once_with(6)


def test_skips_already_visited_urls():
    """fetch() returns None without making a request for visited URLs."""
    crawler = Crawler(delay=0)
    with patch("src.crawler.requests.get") as mock_get:
        crawler.visited.add("https://quotes.toscrape.com/page/1/")
        result = crawler.fetch("https://quotes.toscrape.com/page/1/")
        assert result is None
        mock_get.assert_not_called()


def test_handles_http_error_gracefully():
    """fetch() returns None for non-200 responses without raising."""
    crawler = Crawler(delay=0)
    with patch("src.crawler.requests.get") as mock_get:
        mock_get.return_value = make_response(404, "")
        result = crawler.fetch("https://quotes.toscrape.com/bad/")
        assert result is None


def test_handles_network_exception_gracefully():
    """fetch() returns None when requests.get raises a connection error."""
    crawler = Crawler(delay=0)
    with patch("src.crawler.requests.get") as mock_get:
        mock_get.side_effect = Exception("connection refused")
        result = crawler.fetch("https://quotes.toscrape.com/")
        assert result is None


def test_successful_fetch_returns_html():
    """fetch() returns the response text on a 200 response."""
    crawler = Crawler(delay=0)
    with patch("src.crawler.requests.get") as mock_get:
        mock_get.return_value = make_response(200, "<html>hello</html>")
        result = crawler.fetch("https://quotes.toscrape.com/")
        assert result == "<html>hello</html>"


def test_crawl_follows_pagination_links():
    """crawl() follows /page/N/ links and returns all fetched pages."""
    crawler = Crawler(delay=0)
    responses = [
        make_response(200, PAGINATED_HTML),
        make_response(200, LAST_PAGE_HTML),
    ]
    with patch("src.crawler.requests.get", side_effect=responses):
        pages = crawler.crawl("https://quotes.toscrape.com/")
    assert len(pages) == 2
    assert "https://quotes.toscrape.com/" in pages
    assert "https://quotes.toscrape.com/page/2/" in pages


def test_crawl_does_not_visit_same_url_twice():
    """crawl() visits each URL exactly once even if it appears in multiple pages."""
    crawler = Crawler(delay=0)
    # Both pages link back to /page/2/ — should only fetch it once
    html_with_self_link = """
    <html><body>
      <li class="next"><a href="/page/2/">Next</a></li>
    </body></html>
    """
    responses = [
        make_response(200, html_with_self_link),
        make_response(200, LAST_PAGE_HTML),
    ]
    with patch("src.crawler.requests.get", side_effect=responses) as mock_get:
        crawler.crawl("https://quotes.toscrape.com/")
    assert mock_get.call_count == 2
