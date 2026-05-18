"""Tests for result-page visualisations: per-source bar chart and KWIC excerpts.

Three layers:
1. `kwic_excerpt` pure helper — context window math, multi-line queries,
   no-match fallback.
2. `build_source_chart_data` pure helper — aggregation, sort, single-source
   suppression.
3. Rendering integration — `render_fragment` emits the SVG bar chart, the
   KWIC preview blocks, the compact-mode toggle button.
"""
from app.services.html_service import (
    build_source_chart_data,
    kwic_excerpt,
    render_fragment,
)


# ── kwic_excerpt ────────────────────────────────────────────────────────────

def test_kwic_returns_centered_excerpt_around_match():
    text = "a" * 60 + "DHARMA" + "b" * 60
    out = kwic_excerpt(text, "DHARMA", window=20)
    assert out["match"] == "DHARMA"
    assert out["before"].startswith("…")
    assert out["after"].endswith("…")
    # Window of 20 each side.
    assert len(out["before"].lstrip("…")) == 20
    assert len(out["after"].rstrip("…")) == 20


def test_kwic_is_case_insensitive():
    out = kwic_excerpt("Краткий текст про ДХАРМА Кришны", "дхарма", window=10)
    assert out["match"] == "ДХАРМА"  # preserves case of source text
    assert "Кришны" in out["after"]


def test_kwic_handles_match_at_start_no_leading_ellipsis():
    out = kwic_excerpt("dharma is the topic", "dharma", window=10)
    assert out["match"] == "dharma"
    assert not out["before"].startswith("…")  # nothing to elide on the left


def test_kwic_handles_match_at_end_no_trailing_ellipsis():
    out = kwic_excerpt("the topic is dharma", "dharma", window=20)
    assert out["match"] == "dharma"
    assert not out["after"].endswith("…")


def test_kwic_multiline_query_picks_first_matching_term():
    # Two-line query: first line doesn't match, second does.
    out = kwic_excerpt("about karma and other concepts", "atman\nkarma", window=10)
    assert out["match"] == "karma"


def test_kwic_no_match_returns_fallback_excerpt():
    # When no query term occurs, return a leading-window slice as `after`
    # so the user still sees the text.
    out = kwic_excerpt("a b c d e " * 20, "zzz_no_match", window=10)
    assert out["match"] == ""
    # Fallback fills `after` from the start of the text.
    assert out["after"]
    assert out["before"] == ""


def test_kwic_empty_text_returns_empty():
    out = kwic_excerpt("", "dharma")
    assert out == {"before": "", "match": "", "after": ""}


def test_kwic_empty_query_returns_leading_slice():
    out = kwic_excerpt("some text here", "")
    assert out["match"] == ""
    assert "some" in out["after"]


def test_kwic_short_text_no_ellipsis():
    out = kwic_excerpt("dharma", "dharma", window=40)
    assert out["match"] == "dharma"
    assert out["before"] == ""
    assert out["after"] == ""


# ── build_source_chart_data ─────────────────────────────────────────────────

def test_chart_returns_empty_for_zero_results():
    assert build_source_chart_data([]) == []


def test_chart_returns_empty_when_only_one_source_hit():
    results = [
        {"source_id": 1, "source_title": "A", "line_text": "x"},
        {"source_id": 1, "source_title": "A", "line_text": "y"},
    ]
    # Chart adds no information when results all come from one source.
    assert build_source_chart_data(results) == []


def test_chart_aggregates_counts_per_source():
    results = [
        {"source_id": 1, "source_title": "A", "line_text": "x"},
        {"source_id": 2, "source_title": "B", "line_text": "y"},
        {"source_id": 1, "source_title": "A", "line_text": "z"},
        {"source_id": 1, "source_title": "A", "line_text": "w"},
    ]
    chart = build_source_chart_data(results)
    # A has 3 hits, B has 1.
    titles = {row["title"]: row["count"] for row in chart}
    assert titles == {"A": 3, "B": 1}


def test_chart_sorted_by_count_descending():
    results = (
        [{"source_id": 1, "source_title": "Few", "line_text": "x"}] +
        [{"source_id": 2, "source_title": "Many", "line_text": "y"}] * 5 +
        [{"source_id": 3, "source_title": "Some", "line_text": "z"}] * 3
    )
    chart = build_source_chart_data(results)
    counts = [row["count"] for row in chart]
    assert counts == sorted(counts, reverse=True)
    assert chart[0]["title"] == "Many"
    assert chart[-1]["title"] == "Few"


def test_chart_anchors_follow_first_seen_order():
    # chart_anchor points at #chapter_N where N is the 1-based position of
    # that source in `groups` (first-seen-in-results order, NOT by-count).
    # If "Few" appears in results before "Many" but has fewer hits, the
    # chart row for "Few" should still target chapter_1.
    results = [
        {"source_id": 1, "source_title": "Few", "line_text": "x"},  # first-seen → chapter_1
        {"source_id": 2, "source_title": "Many", "line_text": "y"}, # second-seen → chapter_2
        {"source_id": 2, "source_title": "Many", "line_text": "y"},
        {"source_id": 2, "source_title": "Many", "line_text": "y"},
    ]
    chart = build_source_chart_data(results)
    by_title = {row["title"]: row["chart_anchor"] for row in chart}
    assert by_title["Few"] == "chapter_1"
    assert by_title["Many"] == "chapter_2"


# ── Rendering integration ───────────────────────────────────────────────────

def _mk_result(sid, title, line_text, **extra):
    return {
        "source_id": sid,
        "source_title": title,
        "source_filename": f"src{sid}.html",
        "line_num": 1,
        "link_id": "1.1",
        "chapter": "",
        "line_html": f"<div>{line_text}</div>",
        "line_text": line_text,
        **extra,
    }


def test_fragment_renders_kwic_block_for_each_result():
    results = [_mk_result(1, "Source A", "found dharma in this corpus line")]
    html = render_fragment("dharma", results)
    assert 'class="kwic-preview"' in html
    # The matched term is wrapped in <mark>.
    assert '<mark' in html and 'dharma' in html


def test_fragment_omits_chart_for_single_source_hit():
    results = [_mk_result(1, "Source A", "v1"), _mk_result(1, "Source A", "v2")]
    html = render_fragment("v", results)
    # Single source → no SVG bar chart.
    assert 'class="search-bar-chart"' not in html


def test_fragment_renders_chart_when_multiple_sources_hit():
    results = [
        _mk_result(1, "Source A", "match here"),
        _mk_result(2, "Source B", "match elsewhere"),
        _mk_result(2, "Source B", "another match"),
    ]
    html = render_fragment("match", results)
    assert 'class="search-bar-chart"' in html
    # SVG element present with rect bars.
    assert '<svg' in html and '<rect' in html
    # Titles appear as labels.
    assert "Source A" in html
    assert "Source B" in html


def test_fragment_chart_links_to_chapter_anchors():
    results = [
        _mk_result(1, "Source A", "x"),
        _mk_result(2, "Source B", "y"),
    ]
    html = render_fragment("x y", results)
    # Each bar wraps in an <a href="#chapter_N">.
    assert 'href="#chapter_1"' in html
    assert 'href="#chapter_2"' in html


def test_fragment_emits_compact_toggle_button_when_more_than_one_result():
    results = [
        _mk_result(1, "Source A", "first"),
        _mk_result(1, "Source A", "second"),
    ]
    html = render_fragment("first second", results)
    assert 'id="toggleCompactBtn"' in html


def test_fragment_omits_compact_toggle_for_single_result():
    results = [_mk_result(1, "Source A", "only one")]
    html = render_fragment("only", results)
    assert 'id="toggleCompactBtn"' not in html


def test_fragment_kwic_block_hidden_by_default_via_inline_style():
    # The block exists in markup but has display:none so the user only sees
    # it after toggling compact mode. Avoids visual clutter on first paint.
    results = [_mk_result(1, "Source A", "found dharma in text")]
    html = render_fragment("dharma", results)
    # Look for the kwic-preview div with display:none in its inline style.
    import re
    m = re.search(r'class="kwic-preview"[^>]*style="[^"]*display:none', html)
    assert m is not None, "kwic-preview should be hidden by default"
