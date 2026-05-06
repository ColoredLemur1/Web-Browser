from src.search import Search

SAMPLE_INDEX = {
    "good": {
        "https://example.com/p1": {"frequency": 2, "positions": [0, 4]},
        "https://example.com/p2": {"frequency": 1, "positions": [3]},
    },
    "friend": {
        "https://example.com/p2": {"frequency": 1, "positions": [7]},
    },
    "rare": {
        "https://example.com/p3": {"frequency": 1, "positions": [2]},
    },
}


def test_find_single_word_returns_all_matching_pages():
    """Single token returns urls listed under that term"""
    s = Search(SAMPLE_INDEX)
    results = s.find_pages("good")
    assert set(results) == {"https://example.com/p1", "https://example.com/p2"}


def test_find_multi_word_returns_intersection():
    """Multiple tokens, urls must appear under every term"""
    s = Search(SAMPLE_INDEX)
    results = s.find_pages("good friends")
    assert results == ["https://example.com/p2"]


def test_find_nonexistent_word_returns_empty():
    """Missing token yields empty list"""
    s = Search(SAMPLE_INDEX)
    assert s.find_pages("notaword") == []


def test_find_empty_query_returns_empty():
    """Empty string query yields no urls"""
    s = Search(SAMPLE_INDEX)
    assert s.find_pages("") == []


def test_find_whitespace_only_query_returns_empty():
    """Whitespace only splits to no tokens"""
    s = Search(SAMPLE_INDEX)
    assert s.find_pages("   ") == []


def test_find_is_case_insensitive():
    """Upper and mixed case queries match same urls as lower"""
    s = Search(SAMPLE_INDEX)
    assert set(s.find_pages("GOOD")) == {"https://example.com/p1", "https://example.com/p2"}
    assert set(s.find_pages("Good")) == {"https://example.com/p1", "https://example.com/p2"}


def test_find_multi_word_no_shared_pages_returns_empty():
    """Disjoint term footprints, intersection empty"""
    s = Search(SAMPLE_INDEX)
    assert s.find_pages("good rare") == []


def test_print_word_returns_index_entry():
    """Known word returns same postings map as index slice"""
    s = Search(SAMPLE_INDEX)
    entry = s.print_word("friends")
    assert entry == SAMPLE_INDEX["friend"]


def test_print_word_is_case_insensitive():
    """Lookup lowercases before index get"""
    s = Search(SAMPLE_INDEX)
    assert s.print_word("GOOD") == SAMPLE_INDEX["good"]


def test_print_word_not_found_returns_none():
    """Unknown word yields none"""
    s = Search(SAMPLE_INDEX)
    assert s.print_word("notaword") is None


def test_find_returns_results_in_descending_score_order():
    """Pages ordered by summed query term frequency, highest first"""
    s = Search(SAMPLE_INDEX)
    results = s.find_pages("good")
    assert results[0] == "https://example.com/p1"
    assert results[1] == "https://example.com/p2"


def test_find_stems_query_terms():
    """Inflected query form matches documents under same stem"""
    from nltk.stem import PorterStemmer
    stem = PorterStemmer().stem("swim")
    index_with_stem = {
        stem: {"https://example.com/p1": {"frequency": 1, "positions": [0]}},
    }
    s = Search(index_with_stem)
    results = s.find_pages("swimming")
    assert "https://example.com/p1" in results
