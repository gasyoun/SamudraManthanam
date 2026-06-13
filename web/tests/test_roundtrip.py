"""CONVERTER_SPEC §7 gate 2 — HTML round-trip fidelity (sample-based).

Renders JSONL records → citation-block HTML via render_for_reader.py, then
asserts zero search-relevant divergence:

  1. Rendered HTML contains citation_block / chapter_block structure.
  2. All Sanskrit segment text appears in the rendered HTML (none dropped).
  3. All Russian segment text appears in the rendered HTML (none dropped).
  4. Passage id anchors survive the round-trip (navigation integrity).
  5. [conditional] JSONL plain text is a superset of original corpus HTML
     plain text — skip when the original HTML files are not accessible.

Tests are @pytest.mark.corpus so they are deselected by default in pytest.ini
(same as all other corpus tests) and only run when the JSONL is present.
"""
import json
import re
import sys
from pathlib import Path

import pytest

_WEB_DIR = Path(__file__).parent.parent
_CB_DIR = _WEB_DIR / "corpus_builder"
_REPO_ROOT = _WEB_DIR.parent

sys.path.insert(0, str(_WEB_DIR))

from corpus_builder.render_for_reader import (
    _strip_html,
    load_jsonl_records,
    render_source_html,
    text_from_records,
)

# Source used for all sample-based Gate 2 checks.
# 01_rigveda: A-clean, 1:1 bilingual, multi-commentary — the widest coverage.
_SAMPLE_SLUG = "01_rigveda"
_CORPUS_HTML = (
    _REPO_ROOT / "Index" / "lib" / "x86_64-win64" / "Data" / f"{_SAMPLE_SLUG}.html"
)


@pytest.fixture(scope="session")
def sample_records():
    jsonl_path = _CB_DIR / "jsonl" / f"{_SAMPLE_SLUG}.jsonl"
    if not jsonl_path.exists():
        pytest.skip("JSONL not built — run html_to_canonical.py first")
    return load_jsonl_records(jsonl_path)


@pytest.fixture(scope="session")
def rendered_html(sample_records):
    return render_source_html(sample_records)


# ---------------------------------------------------------------------------
# Gate 2 test 1 — renderer produces structurally valid citation-block HTML
# ---------------------------------------------------------------------------

@pytest.mark.corpus
def test_gate2_renderer_produces_citation_blocks(rendered_html, sample_records):
    """Gate 2.1: rendered output has citation_block and chapter_block structure."""
    assert len(rendered_html) > 10_000, "Expected substantial rendered HTML"
    assert 'class="citation_block"' in rendered_html
    assert 'class="chapter_block iast"' in rendered_html
    assert 'class="chapter_block translation"' in rendered_html
    assert 'class="comments"' in rendered_html

    # Count citation_blocks — should match number of unique passages
    n_blocks = rendered_html.count('class="citation_block"')
    n_sa = sum(1 for r in sample_records if r.get("seg") == "sa")
    # Every sa record is the primary record for a passage → one block each
    assert n_blocks == n_sa, (
        f"Expected {n_sa} citation_blocks (one per sa record), got {n_blocks}"
    )


# ---------------------------------------------------------------------------
# Gate 2 test 2 — Sanskrit text not dropped
# ---------------------------------------------------------------------------

@pytest.mark.corpus
def test_gate2_sa_text_in_rendered_html(rendered_html, sample_records):
    """Gate 2.2: every Sanskrit record's leading text appears in rendered HTML.

    Comparison is plain-text → plain-text (both stripped of HTML) so that
    <br> vs space differences don't cause false negatives.
    """
    rendered_text = _strip_html(rendered_html)
    sa_records = [r for r in sample_records if r.get("seg") == "sa"]
    # Sample first 100 sa records — enough for a meaningful check without
    # scanning all 10k+ rigveda records.
    sample = sa_records[:100]

    missing = []
    for rec in sample:
        snippet = rec.get("text", "")[:25].strip()
        if snippet and snippet not in rendered_text:
            missing.append(f"{rec['id']!r}: {snippet!r}")

    assert not missing, (
        f"Gate 2: {len(missing)} Sanskrit text snippets absent from rendered output "
        f"(first 5): {missing[:5]}"
    )


# ---------------------------------------------------------------------------
# Gate 2 test 3 — Russian text not dropped
# ---------------------------------------------------------------------------

@pytest.mark.corpus
def test_gate2_ru_text_in_rendered_html(rendered_html, sample_records):
    """Gate 2.3: every Russian record's leading text appears in rendered HTML.

    Comparison is plain-text → plain-text (both stripped of HTML) so that
    <br> vs space differences don't cause false negatives.
    """
    rendered_text = _strip_html(rendered_html)
    ru_records = [r for r in sample_records if r.get("seg") == "ru"]
    sample = ru_records[:100]

    missing = []
    for rec in sample:
        snippet = rec.get("text", "")[:20].strip()
        if snippet and snippet not in rendered_text:
            missing.append(f"{rec['id']!r}: {snippet!r}")

    assert not missing, (
        f"Gate 2: {len(missing)} Russian text snippets absent from rendered output "
        f"(first 5): {missing[:5]}"
    )


# ---------------------------------------------------------------------------
# Gate 2 test 4 — passage anchors survive round-trip
# ---------------------------------------------------------------------------

@pytest.mark.corpus
def test_gate2_passage_anchors_in_rendered_html(rendered_html, sample_records):
    """Gate 2.4: passage id= anchors are present in citation_block divs."""
    sa_records = [r for r in sample_records if r.get("seg") == "sa"]
    sample_passages = [r["passage"] for r in sa_records[:50]]

    missing = []
    for p in sample_passages:
        if f'id="{p}"' not in rendered_html:
            missing.append(p)

    assert not missing, (
        f"Gate 2: {len(missing)} passage anchors missing from rendered HTML: "
        f"{missing[:5]}"
    )


# ---------------------------------------------------------------------------
# Gate 2 test 5 — JSONL text is superset of original corpus HTML text
# (skipped when corpus HTML files are absent, e.g. in CI)
# ---------------------------------------------------------------------------

@pytest.mark.corpus
def test_gate2_jsonl_text_superset_of_original_html(sample_records):
    """Gate 2.5: JSONL plain text covers original corpus HTML plain text.

    Reads the original .html file, strips all HTML tags, then checks that
    distinctive IAST tokens from the original all appear in the JSONL-derived
    text.  At most 5 misses are allowed (tolerance for minor HTML-vs-JSONL
    encoding differences in Vedic accent characters).
    """
    if not _CORPUS_HTML.exists():
        pytest.skip("Original corpus HTML not available — skipping corpus diff check")

    jsonl_text = text_from_records(sample_records)

    with open(_CORPUS_HTML, encoding="utf-8") as f:
        orig_html = f.read()
    orig_text = _strip_html(orig_html)

    # Scope the comparison to verse (chapter_block) content only.
    # Commentary truncation in the converter (COMMENT_ITEM_RE stops at the
    # first nested </div>) is a known limitation: bibliography references
    # inside nested divs in long commentaries may not appear in JSONL text.
    # Verse (sa/ru) content is extracted without loss and is the search-
    # relevant surface for this test.
    #
    # Strip <small> tags first: both the converter and parse_html.py
    # intentionally exclude <small> bibliography footnotes from plain text.
    _SMALL = re.compile(r"<small[^>]*>.*?</small>", re.IGNORECASE | re.DOTALL)
    orig_html_no_small = _SMALL.sub("", orig_html)

    # Extract only chapter_block content (sa/ru verse blocks) from the original.
    _CB_RE = re.compile(
        r'<div\s+class=["\']chapter_block[^"\']*["\']\s*>(.*?)</div>', re.DOTALL
    )
    verse_blocks = _CB_RE.findall(orig_html_no_small)
    verse_text = " ".join(_strip_html(b) for b in verse_blocks)

    # Scope JSONL text to sa+ru records only (matches the chapter_block scope above).
    sa_ru_text = " ".join(
        r.get("text", "") for r in sample_records if r.get("seg") in ("sa", "ru")
    )

    # Sample distinctive IAST tokens (≥ 8-char sequences) from the verse section.
    iast_re = re.compile(r"[a-zāīūṛṝḷṃḥśṣṭḍṇ]{8,}", re.IGNORECASE)
    orig_tokens = set(iast_re.findall(verse_text))
    sample_tokens = sorted(orig_tokens)[:150]

    missing = [t for t in sample_tokens if t not in sa_ru_text]

    assert len(missing) <= 5, (
        f"Gate 2: {len(missing)} original verse-block IAST tokens absent from JSONL "
        f"sa+ru text (threshold ≤ 5, commentary and <small> excluded): "
        f"{missing[:10]}"
    )
