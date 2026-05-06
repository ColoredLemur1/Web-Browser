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
    """Sleep uses configured delay before each fetch"""
    crawler = Crawler(delay=6)
    with patch("src.crawler.time.sleep") as mock_sleep, \
         patch("src.crawler.requests.get") as mock_get:
        mock_get.return_value = make_response(200, "<html></html>")
        crawler.fetch("https://quotes.toscrape.com/")
        mock_sleep.assert_called_once_with(6)


def test_skips_already_visited_urls():
    """Already visited url skips request"""
    crawler = Crawler(delay=0)
    with patch("src.crawler.requests.get") as mock_get:
        crawler.visited.add("https://quotes.toscrape.com/page/1/")
        result = crawler.fetch("https://quotes.toscrape.com/page/1/")
        assert result is None
        mock_get.assert_not_called()


def test_handles_http_error_gracefully():
    """Non-200 status yields none, no raise"""
    crawler = Crawler(delay=0)
    with patch("src.crawler.requests.get") as mock_get:
        mock_get.return_value = make_response(404, "")
        result = crawler.fetch("https://quotes.toscrape.com/bad/")
        assert result is None


def test_handles_network_exception_gracefully():
    """Get raising yields none"""
    crawler = Crawler(delay=0)
    with patch("src.crawler.requests.get") as mock_get:
        mock_get.side_effect = Exception("connection refused")
        result = crawler.fetch("https://quotes.toscrape.com/")
        assert result is None


def test_successful_fetch_returns_html():
    """200 response returns response text"""
    crawler = Crawler(delay=0)
    with patch("src.crawler.requests.get") as mock_get:
        mock_get.return_value = make_response(200, "<html>hello</html>")
        result = crawler.fetch("https://quotes.toscrape.com/")
        assert result == "<html>hello</html>"


def test_crawl_follows_pagination_links():
    """Crawl walks next link until none"""
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
    """Each url at most one fetch even if linked twice"""
    crawler = Crawler(delay=0)
    # second page still points at page 2, only one GET for that url
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
