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
    """Non 200 status yields none, no raise"""
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


MULTI_LINK_HTML = """
<html><body>
  <a href="/page/about/">About</a>
  <a href="/page/contact/">Contact</a>
</body></html>
"""

LEAF_HTML = """<html><body><p>No outbound links here.</p></body></html>"""


def test_crawl_follows_all_same_domain_links():
    """Bfs finds every same domain page from start url"""
    crawler = Crawler(delay=0)
    responses = {
        "https://example.com/": make_response(200, MULTI_LINK_HTML),
        "https://example.com/page/about/": make_response(200, LEAF_HTML),
        "https://example.com/page/contact/": make_response(200, LEAF_HTML),
    }
    with patch(
        "src.crawler.requests.get",
        side_effect=lambda url, **kw: responses.get(url, make_response(404, "")),
    ):
        pages = crawler.crawl("https://example.com/")
    assert "https://example.com/" in pages
    assert "https://example.com/page/about/" in pages
    assert "https://example.com/page/contact/" in pages


def test_crawl_does_not_follow_external_links():
    """Bfs stays on seed domain, ignore external hrefs"""
    external_html = """
    <html><body>
      <a href="https://external.com/other/">External</a>
      <a href="/internal/">Internal</a>
    </body></html>
    """
    crawler = Crawler(delay=0)
    responses = {
        "https://example.com/": make_response(200, external_html),
        "https://example.com/internal/": make_response(200, LEAF_HTML),
    }
    with patch(
        "src.crawler.requests.get",
        side_effect=lambda url, **kw: responses.get(url, make_response(404, "")),
    ):
        pages = crawler.crawl("https://example.com/")
    assert "https://external.com/other/" not in pages
    assert "https://example.com/internal/" in pages


def test_fetch_skips_disallowed_url():
    """Urls blocked by robots txt are not fetched"""
    crawler = Crawler(delay=0)
    with patch.object(crawler, "_can_fetch", return_value=False), \
         patch("src.crawler.requests.get") as mock_get:
        result = crawler.fetch("https://example.com/private/")
        assert result is None
        mock_get.assert_not_called()


def test_fetch_proceeds_when_robots_allows():
    """Urls allowed by robots txt fetch normally"""
    crawler = Crawler(delay=0)
    with patch.object(crawler, "_can_fetch", return_value=True), \
         patch("src.crawler.requests.get") as mock_get:
        mock_get.return_value = make_response(200, "<html>ok</html>")
        result = crawler.fetch("https://example.com/public/")
        assert result == "<html>ok</html>"


def test_crawl_does_not_visit_same_url_twice():
    """Each URL is fetched at most once even if multiple pages link to it"""
    html_a = "<html><body><a href='/b/'>B</a></body></html>"
    html_b = "<html><body><a href='/'>Home</a></body></html>"
    call_counts = {}

    def side_effect(url, **kw):
        call_counts[url] = call_counts.get(url, 0) + 1
        if url == "https://example.com/":
            return make_response(200, html_a)
        if url == "https://example.com/b/":
            return make_response(200, html_b)
        return make_response(404, "")

    crawler = Crawler(delay=0)
    with patch("src.crawler.requests.get", side_effect=side_effect):
        crawler.crawl("https://example.com/")

    assert call_counts.get("https://example.com/", 0) == 1
    assert call_counts.get("https://example.com/b/", 0) == 1
