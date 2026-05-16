"""Tests for web/ingest/parse_html.py — link_id extraction.

The Mahābhārata Bhīṣma-parvan and Gītagovinda HTML files lack `id="..."` on
`citation_block` divs and carry the verse coordinate only on a nested
`<div class="range" title="...">` element. The original ingest regex picked up
the *first* `id=` on the line, which is the `range` div's page-style id
(e.g. "Махабхарата 2009 (VI): 9") — unique but not URL-routable. The new
helper falls back to parsing the `range` title's trailing "CHAPTER. VERSE"
segment to produce a clean "1.1" anchor.
"""
from ingest.parse_html import _extract_link_id


def test_citation_block_id_is_preferred_over_range_id():
    # Smirnov Bhagavadgītā shape: citation_block has clean id, range carries
    # a bibliographic-page id. The clean id wins.
    line = (
        '<div class="citation_block" id="1.1">'
        '<div class="range" title="Бхагавад-Гита I. 1. 1" '
        'id="Бхагавад-Гита (Б.Л.Смирнов, 1977): 1">1</div>text'
    )
    assert _extract_link_id(line) == "1.1"


def test_range_title_fallback_bhishma_parvan():
    # MBh Bhīṣma-parvan: citation_block has no id, range title is
    # "Махабхарата VI. CHAPTER. VERSE".
    line = (
        '<div class="citation_block">'
        '<div class="range" title="Махабхарата VI. 1. 1" '
        'id="Махабхарата 2009 (VI): 9">1</div>text'
    )
    assert _extract_link_id(line) == "1.1"


def test_range_title_fallback_gitagovinda():
    line = (
        '<div class="citation_block">'
        '<div class="range" title="Гитаговинда, 1. 1" '
        'id="Гитаговинда, 2020: 1">1</div>text'
    )
    assert _extract_link_id(line) == "1.1"


def test_range_title_handles_merged_verse_range():
    # Erman merges some stanzas: title is "VI. 1. 3-6" → "1.3-6".
    line = (
        '<div class="citation_block">'
        '<div class="range" title="Махабхарата VI. 1. 3-6" '
        'id="Махабхарата 2009 (VI): 12">range</div>'
    )
    assert _extract_link_id(line) == "1.3-6"


def test_gita_chapter_in_bhishma_uses_mbh_internal_numbering():
    # Bhagavadgītā chapter 1 = MBh Bhīṣma-parvan adhyāya 23. The fallback
    # surfaces MBh-internal coordinates (callers handle the +22 offset).
    line = (
        '<div class="citation_block">'
        '<div class="range" title="Махабхарата VI. 23. 1" '
        'id="МБх 2009: 100">1</div>'
    )
    assert _extract_link_id(line) == "23.1"


def test_chapter_title_falls_through_to_any_id():
    # No citation_block, no range — chapter heading. Existing behavior:
    # return whatever `id=` is on the line.
    line = '<div class="chapter_title" id="chapter_1">Глава 1</div>'
    assert _extract_link_id(line) == "chapter_1"


def test_line_without_any_id_returns_empty_string():
    line = '<div class="header header_1">МАХАБХАРАТА</div>'
    assert _extract_link_id(line) == ""


def test_range_present_but_unparseable_title_does_not_leak_page_id():
    # If a `range` div exists but its title isn't "CHAPTER. VERSE", we must
    # NOT fall through to priority-3 and return the range's bibliographic
    # id — that's the very regression this helper fixes.
    line = (
        '<div class="citation_block">'
        '<div class="range" title="Введение" '
        'id="Махабхарата 2009 (VI): 1">intro</div>'
    )
    assert _extract_link_id(line) == ""


def test_three_part_id_preserved():
    # The yoga-sutry anthology has one anomalous "1.1.1" id. Don't collapse it.
    line = '<div class="citation_block" id="1.1.1">text'
    assert _extract_link_id(line) == "1.1.1"


def test_single_digit_id_preserved():
    # Yāmunācārya's 32-verse summary uses bare verse numbers as ids.
    line = '<div class="citation_block" id="32">text'
    assert _extract_link_id(line) == "32"
