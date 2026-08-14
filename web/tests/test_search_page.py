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
    _should_noindex,
)

client = TestClient(app)


# ── _canonical_search_url ────────────────────────────────────────────────────

def test_canonical_strips_to_pretty_unicode_path():
    url = _canonical_search_url(
        base="https://samskrtam.ru", query="  Кришна  ",
        mode="plain", case_sensitive=False, whole_word=False, source_slugs=None,
    )
    assert url == "https://samskrtam.ru/search/Кришна"
    assert "%D0" not in url


def test_canonical_drops_default_params():
    url = _canonical_search_url(
        base="", query="dharma", mode="plain",
        case_sensitive=False, whole_word=False, source_slugs=None,
    )
    assert url == "/search/dharma"


def test_canonical_keeps_non_default_flags():
    url = _canonical_search_url(
        base="", query="agni", mode="regex",
        case_sensitive=True, whole_word=True, source_slugs=None,
    )
    assert "q=agni" in url
    assert "mode=regex" in url
    assert "cs=1" in url
    assert "ww=1" in url


def test_canonical_sorts_source_slugs():
    url = _canonical_search_url(
        base="", query="dharma", mode="plain",
        case_sensitive=False, whole_word=False,
        source_slugs=["source2", "source1"],
    )
    assert "src=source1%2Csource2" in url  # %2C is url-encoded comma


# ── source filter resolution (slugs + legacy ids) ───────────────────────────

def test_src_slug_filter_narrows_results():
    # 'svasti' lives in source1 only — filtering to source2 must hide it.
    r = client.get("/search/source1/svasti")
    assert r.status_code == 200
    assert "svasti arjuna" in r.text
    r = client.get("/search/source2/svasti")
    assert r.status_code == 200
    assert "svasti arjuna" not in r.text


def test_src_legacy_numeric_ids_still_resolve():
    # Pre-slug bookmarks carried numeric ids; they 301 onto the slug path.
    r = client.get("/search?q=svasti&src=1", follow_redirects=False)
    assert r.status_code == 301
    assert r.headers["location"].endswith("/search/source1/svasti")
    r = client.get("/search/source1/svasti")
    assert r.status_code == 200
    assert "svasti arjuna" in r.text
    canon_idx = r.text.index('rel="canonical"')
    assert "/search/source1/svasti" in r.text[canon_idx:canon_idx + 300]


def test_src_unknown_tokens_fall_back_to_all_sources():
    # Unresolvable filter degrades to "all sources" rather than erroring.
    r = client.get("/search?q=svasti&src=no-such-slug", follow_redirects=False)
    assert r.status_code == 301
    assert r.headers["location"].endswith("/search/svasti")


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


def test_query_string_301s_to_pretty_path():
    r = client.get("/search?q=svasti", follow_redirects=False)
    assert r.status_code == 301
    assert r.headers["location"].endswith("/search/svasti")
    assert "%D0" not in r.headers["location"]


def test_cyrillic_pretty_path_is_not_percent_encoded_in_canonical():
    r = client.get("/search/Хастинапур")
    assert r.status_code == 200
    canon_idx = r.text.index('rel="canonical"')
    chunk = r.text[canon_idx:canon_idx + 220]
    assert "Хастинапур" in chunk
    assert "%D0" not in chunk


def test_normal_query_renders_results_and_canonical():
    # 'svasti' is in the conftest seed (source 1, line 10, link_id 1.10).
    r = client.get("/search/svasti")
    assert r.status_code == 200
    assert "svasti" in r.text
    assert 'rel="canonical"' in r.text
    assert "/search/svasti" in r.text
    # Indexable (has results, plain mode, multi-char query).
    assert 'name="robots" content="noindex' not in r.text
    # JSON-LD present.
    assert "SearchResultsPage" in r.text


def test_short_query_gets_noindex_even_when_results_exist():
    # Single character — junk landing page.
    r = client.get("/search/s")
    # Single 's' might match anything; whatever the count, must be noindex.
    assert 'name="robots" content="noindex,follow"' in r.text


def test_zero_result_query_gets_noindex():
    r = client.get("/search/zzznoresultsexpected")
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


def test_canonical_url_in_html_is_pretty_path():
    r = client.get("/search/SVASTI")
    body = r.text
    assert 'rel="canonical" href="' in body
    canon_idx = body.index('rel="canonical"')
    canon_chunk = body[canon_idx:canon_idx + 200]
    assert "/search/SVASTI" in canon_chunk
    assert "?q=" not in canon_chunk


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
