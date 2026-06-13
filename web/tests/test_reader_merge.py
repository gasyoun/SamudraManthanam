"""Hermetic tests for the reader JSONL-segment merge logic.

`_merge_jsonl_lines` groups per-segment corpus_lines rows (JSONL ingest) into
passage-level citation_block HTML, matching the structure produced by the
legacy HTML-parsed ingest path.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.routers.reader import _merge_jsonl_lines


def _make_row(
    line_num: int,
    link_id: str,
    canonical_id: str,
    line_html: str,
    line_text: str = "",
    chapter: str | None = None,
) -> dict:
    return {
        "line_num": line_num,
        "link_id": link_id,
        "canonical_id": canonical_id,
        "line_html": line_html,
        "line_text": line_text,
        "chapter": chapter,
    }


def test_merge_bilingual_passage():
    """sa + ru segments merge into a single citation_block with chapter_content."""
    rows = [
        _make_row(1, "1.1", "w:1.1#sa", "<b>अग्निमीळे</b>", "अग्निमीळे", "Мандала 1"),
        _make_row(2, "1.1", "w:1.1#ru", "<i>Агни воспеваю</i>", "Агни воспеваю"),
    ]
    result = _merge_jsonl_lines(rows)
    assert len(result) == 1
    r = result[0]
    assert r["link_id"] == "1.1"
    assert r["line_num"] == 1
    assert r["chapter"] == "Мандала 1"
    assert r["line_text"] == "अग्निमीळे"
    html = r["line_html"]
    assert '<div class="chapter_content">' in html
    assert '<div class="chapter_block iast">' in html
    assert '<div class="chapter_block translation">' in html
    assert "अग्निमीळे" in html
    assert "Агни воспеваю" in html
    assert '<div class="comments">' not in html


def test_merge_with_commentary():
    """Passage with sa + ru + two commentaries produces both chapter_content
    and comments divs."""
    rows = [
        _make_row(1, "1.1", "w:1.1#sa", "<b>sa text</b>"),
        _make_row(2, "1.1", "w:1.1#ru", "<i>ru text</i>"),
        _make_row(3, "1.1", "w:1.1#comm0", "<p>comm A</p>"),
        _make_row(4, "1.1", "w:1.1#comm1", "<p>comm B</p>"),
    ]
    result = _merge_jsonl_lines(rows)
    assert len(result) == 1
    html = result[0]["line_html"]
    assert '<div class="chapter_content">' in html
    assert '<div class="comments">' in html
    assert html.count('<div class="comment_item">') == 2
    assert "comm A" in html
    assert "comm B" in html


def test_merge_monolingual_ru_only():
    """Russian-only passage (0:1) has translation block but no iast block."""
    rows = [
        _make_row(1, "1.1", "w:1.1#ru", "<i>ru only</i>", "ru only"),
    ]
    result = _merge_jsonl_lines(rows)
    assert len(result) == 1
    html = result[0]["line_html"]
    assert '<div class="chapter_block translation">' in html
    assert '<div class="chapter_block iast">' not in html
    # line_text falls back to ru record when sa absent
    assert result[0]["line_text"] == "ru only"


def test_merge_two_passages_ordering():
    """Two passages preserve order; each is its own entry."""
    rows = [
        _make_row(1, "1.1", "w:1.1#sa", "sa1"),
        _make_row(2, "1.1", "w:1.1#ru", "ru1"),
        _make_row(3, "1.2", "w:1.2#sa", "sa2"),
        _make_row(4, "1.2", "w:1.2#ru", "ru2"),
    ]
    result = _merge_jsonl_lines(rows)
    assert len(result) == 2
    assert result[0]["link_id"] == "1.1"
    assert result[1]["link_id"] == "1.2"


def test_merge_html_fallback_passthrough():
    """Rows without '#' in canonical_id (HTML-parse fallback) pass through as-is."""
    rows = [
        _make_row(1, "1.1", "", "<div class='citation_block'>legacy html</div>", "text"),
        _make_row(2, "1.2", "", "<div class='citation_block'>legacy 2</div>", "text2"),
    ]
    result = _merge_jsonl_lines(rows)
    assert len(result) == 2
    assert "legacy html" in result[0]["line_html"]
    assert "legacy 2" in result[1]["line_html"]


def test_merge_preserves_chapter_from_sa():
    """Chapter field comes from the sa record in a bilingual group."""
    rows = [
        _make_row(1, "2.1", "w:2.1#sa", "sa", chapter="Chapter II"),
        _make_row(2, "2.1", "w:2.1#ru", "ru", chapter=None),
    ]
    result = _merge_jsonl_lines(rows)
    assert result[0]["chapter"] == "Chapter II"


def test_merge_empty_input():
    assert _merge_jsonl_lines([]) == []
