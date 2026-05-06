import os
import tempfile
from src.indexer import Indexer

SAMPLE_PAGES = {
    "https://example.com/page1": "<html><body><p>Good people do Good things</p></body></html>",
    "https://example.com/page2": "<html><body><p>Nonsense words here</p></body></html>",
}


def test_case_insensitive_indexing():
    """Terms keyed lowercased only"""
    idx = Indexer()
    idx.build(SAMPLE_PAGES)
    assert "good" in idx.index
    assert "Good" not in idx.index


def test_frequency_count():
    """Frequency counts occurrences per url"""
    idx = Indexer()
    idx.build(SAMPLE_PAGES)
    assert idx.index["good"]["https://example.com/page1"]["frequency"] == 2


def test_positions_recorded():
    """Positions one entry per hit on page"""
    idx = Indexer()
    idx.build(SAMPLE_PAGES)
    positions = idx.index["good"]["https://example.com/page1"]["positions"]
    assert len(positions) == 2


def test_word_appears_on_correct_page_only():
    """Word only under urls where it appears"""
    from nltk.stem import PorterStemmer
    stemmed = PorterStemmer().stem("nonsense")
    idx = Indexer()
    idx.build(SAMPLE_PAGES)
    assert "https://example.com/page1" not in idx.index[stemmed]
    assert "https://example.com/page2" in idx.index[stemmed]


def test_word_across_multiple_pages():
    """Same term split across urls both recorded"""
    pages = {
        "https://example.com/p1": "<html><body><p>hello world</p></body></html>",
        "https://example.com/p2": "<html><body><p>hello there</p></body></html>",
    }
    idx = Indexer()
    idx.build(pages)
    assert "https://example.com/p1" in idx.index["hello"]
    assert "https://example.com/p2" in idx.index["hello"]


def test_punctuation_stripped_from_tokens():
    """Letters regex drops trailing punctuation on tokens"""
    pages = {
        "https://example.com/p1": "<html><body><p>life, is good.</p></body></html>",
    }
    idx = Indexer()
    idx.build(pages)
    assert "good" in idx.index
    assert "good." not in idx.index
    assert "life" in idx.index
    assert "life," not in idx.index


def test_html_tags_not_indexed():
    """Tag soup text only, markup names out of index"""
    pages = {
        "https://example.com/p1": "<html><body><p>hello</p></body></html>",
    }
    idx = Indexer()
    idx.build(pages)
    assert "html" not in idx.index
    assert "body" not in idx.index


def test_save_and_load_roundtrip():
    """Save then load restores same dict"""
    idx = Indexer()
    idx.build(SAMPLE_PAGES)
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        idx.save(path)
        idx2 = Indexer()
        idx2.load(path)
        assert idx2.index == idx.index
    finally:
        os.unlink(path)


def test_load_raises_when_file_missing():
    """Missing path raises file not found"""
    idx = Indexer()
    try:
        idx.load("nonexistent_index_file.json")
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError:
        pass


def test_stopwords_not_indexed():
    """Common function words are absent from the index"""
    pages = {
        "https://example.com/p1": "<html><body><p>the quick brown fox</p></body></html>",
    }
    idx = Indexer()
    idx.build(pages)
    assert "the" not in idx.index
    assert "quick" in idx.index
    assert "brown" in idx.index
    assert "fox" in idx.index


def test_stopword_a_not_indexed():
    """Single letter stopword a is removed"""
    pages = {
        "https://example.com/p1": "<html><body><p>a quick fix</p></body></html>",
    }
    idx = Indexer()
    idx.build(pages)
    assert "a" not in idx.index
    assert "quick" in idx.index
    assert "fix" in idx.index


def test_numbers_are_indexed():
    """Digit only tokens like model numbers are captured"""
    pages = {
        "https://example.com/p1": "<html><body><p>iPhone 12 screen</p></body></html>",
    }
    idx = Indexer()
    idx.build(pages)
    assert "12" in idx.index


def test_stemming_reduces_inflected_forms():
    """Swimming and swim produce the same index key"""
    from nltk.stem import PorterStemmer as _PS
    _ps = _PS()
    pages_swim = {
        "https://example.com/swim": "<html><body><p>swim</p></body></html>",
    }
    pages_swimming = {
        "https://example.com/swimming": "<html><body><p>swimming</p></body></html>",
    }
    idx_a = Indexer()
    idx_a.build(pages_swim)
    idx_b = Indexer()
    idx_b.build(pages_swimming)
    stem = _ps.stem("swim")
    assert stem in idx_a.index
    assert stem in idx_b.index
    assert set(idx_a.index[stem].keys()) != set(idx_b.index[stem].keys())
