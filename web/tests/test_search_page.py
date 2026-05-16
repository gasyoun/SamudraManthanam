"""Tests for `GET /search` — server-rendered search results.

Covers:
- empty-query landing
- canonical URL normalisation (lowercase / param order / defaults dropped)
- noindex rules (short query, regex mode, zero results)
- JSON-LD SearchResultsPage emitted only when indexable
- form is plain GET (no JS required)
- response routes through dispatch_search and renders fragment content
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.search_page import (
    _canonical_search_url,
    _parse_source_ids,
    _should_noindex,
)

client = TestClient(app)


# ── _canonical_search_url ────────────────────────────────────────────────────

def test_canonical_lowercases_query_and_strips():
    url = _canonical_search_url(
        base="https://samskrtam.ru", query="  Кришна  ",
        mode="plain", case_sensitive=False, whole_word=False, source_ids=None,
    )
    assert url == "https://samskrtam.ru/search?q=%D0%BA%D1%80%D0%B8%D1%88%D0%BD%D0%B0"


def test_canonical_drops_default_params():
    url = _canonical_search_url(
        base="", query="dharma", mode="plain",
        case_sensitive=False, whole_word=False, source_ids=None,
    )
    assert url == "/search?q=dharma"


def test_canonical_keeps_non_default_flags():
    url = _canonical_search_url(
        base="", query="agni", mode="regex",
        case_sensitive=True, whole_word=True, source_ids=None,
    )
    assert "q=agni" in url
    assert "mode=regex" in url
    assert "cs=1" in url
    assert "ww=1" in url


def test_canonical_sorts_source_ids():
    url = _canonical_search_url(
        base="", query="dharma", mode="plain",
        case_sensitive=False, whole_word=False, source_ids=[3, 1, 2],
    )
    assert "src=1%2C2%2C3" in url  # %2C is url-encoded comma


# ── _parse_source_ids ────────────────────────────────────────────────────────

def test_parse_source_ids_basic():
    assert _parse_source_ids("1,2,3") == [1, 2, 3]


def test_parse_source_ids_empty_returns_none():
    assert _parse_source_ids(None) is None
    assert _parse_source_ids("") is None


def test_parse_source_ids_malformed_returns_none():
    # Defense in depth — malformed src filter must NOT 500 the page; it just
    # falls back to "all sources" silently.
    assert _parse_source_ids("1,abc,3") is None
    assert _parse_source_ids("1;2;3") is None
    assert _parse_source_ids("'; DROP TABLE sources;--") is None


# ── _should_noindex ──────────────────────────────────────────────────────────

def test_noindex_for_single_char_query():
    assert _should_noindex(query="a", mode="plain", total=10) is True


def test_noindex_for_regex_mode():
    assert _should_noindex(query="dharma", mode="regex", total=10) is True


def test_noindex_for_zero_results():
    assert _should_noindex(query="dharma", mode="plain", total=0) is True


def test_index_for_normal_plain_query_with_hits():
    assert _should_noindex(query="dharma", mode="plain", total=10) is False


# ── HTTP-level tests ─────────────────────────────────────────────────────────

def test_empty_query_renders_landing_with_noindex():
    r = client.get("/search")
    assert r.status_code == 200
    assert 'name="robots" content="noindex,follow"' in r.text
    # Form should be present and functional without JS.
    assert '<form class="search-form" action="/search" method="get">' in r.text
    # No SearchResultsPage JSON-LD on empty landing.
    assert "SearchResultsPage" not in r.text


def test_normal_query_renders_results_and_canonical():
    # 'svasti' is in the conftest seed (source 1, line 10, link_id 1.10).
    r = client.get("/search?q=svasti")
    assert r.status_code == 200
    assert "svasti" in r.text
    assert 'rel="canonical"' in r.text
    assert "/search?q=svasti" in r.text
    # Indexable (has results, plain mode, multi-char query).
    assert 'name="robots" content="noindex' not in r.text
    # JSON-LD present.
    assert "SearchResultsPage" in r.text


def test_short_query_gets_noindex_even_when_results_exist():
    # Single character — junk landing page.
    r = client.get("/search?q=s")
    # Single 's' might match anything; whatever the count, must be noindex.
    assert 'name="robots" content="noindex,follow"' in r.text


def test_zero_result_query_gets_noindex():
    r = client.get("/search?q=zzznoresultsexpected")
    assert 'name="robots" content="noindex,follow"' in r.text


def test_form_preserves_user_input_on_re_render():
    # User submits a query — form must echo it back so re-refining is easy.
    r = client.get("/search?q=svasti&cs=1")
    body = r.text
    assert 'value="svasti"' in body
    # Case-sensitive checkbox should be re-checked.
    assert 'name="cs" value="1" checked' in body


def test_form_preserves_source_filter():
    # If user filtered by sources, the filter must survive a form re-submit.
    r = client.get("/search?q=svasti&src=1,2")
    assert 'name="src" value="1,2"' in r.text


def test_canonical_url_in_html_is_normalised():
    # Mixed case input should canonicalise to lowercase.
    r = client.get("/search?q=SVASTI")
    body = r.text
    # Canonical link should point at lowercase form.
    assert 'rel="canonical" href="' in body
    # The canonical href contains the lowercased query.
    canon_idx = body.index('rel="canonical"')
    canon_chunk = body[canon_idx:canon_idx + 200]
    assert "svasti" in canon_chunk


def test_regex_mode_renders_but_noindex():
    r = client.get("/search?q=svas.%2A&mode=regex")  # 'svas.*' url-encoded
    assert r.status_code == 200
    assert 'name="robots" content="noindex,follow"' in r.text


def test_malformed_src_does_not_500():
    # Defense-in-depth: bad src filter must yield a clean response, not 500.
    r = client.get("/search?q=svasti&src=abc;DROP")
    assert r.status_code == 200


def test_oversized_query_rejected():
    # FastAPI Query(max_length=1000) → 422.
    r = client.get("/search?q=" + "a" * 1001)
    assert r.status_code == 422


def test_search_page_does_not_break_existing_root_route():
    # Regression: home page must still serve the live-search app.
    r = client.get("/")
    assert r.status_code == 200
    assert "ПАХТАНЬЕ ОКЕАНА" in r.text
