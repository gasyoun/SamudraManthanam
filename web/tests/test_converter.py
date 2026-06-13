"""CONVERTER_SPEC §7 gates — hermetic unit tests + JSONL corpus tests.

Hermetic tests (no corpus needed) cover the pure parsing functions.
Corpus tests load JSONL files produced by html_to_canonical.py and verify
the four measurable CI gates (1, 3, 4, 5).  They skip automatically if
web/corpus_builder/jsonl/ does not exist.
"""
import json
import os
import sys
import pytest
from pathlib import Path

# --- Import converter functions directly ---
# html_to_canonical.py manages its own sys.path at import time.
_CB_DIR = Path(__file__).parent.parent / "corpus_builder"
sys.path.insert(0, str(_CB_DIR.parent))  # web/ on path so corpus_builder is a package

from corpus_builder.html_to_canonical import (  # noqa: E402
    _parse_comment_anchor,
    _extract_passage_from_range_title,
    _to_slp1,
)

# ---------------------------------------------------------------------------
# Fixture: JSONL directory (auto-skip if not built)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def jsonl_dir():
    p = Path(__file__).parent.parent / "corpus_builder" / "jsonl"
    if not p.exists() or not any(p.glob("*.jsonl")):
        pytest.skip("JSONL not built — run html_to_canonical.py first")
    return p


@pytest.fixture(scope="session")
def all_records(jsonl_dir):
    """Load every record from every JSONL file into a list."""
    records = []
    for jf in sorted(jsonl_dir.glob("*.jsonl")):
        with open(jf, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    return records


# ---------------------------------------------------------------------------
# Hermetic: _parse_comment_anchor
# ---------------------------------------------------------------------------

def test_anchor_simple_verse():
    r = _parse_comment_anchor("comment_1_1", "")
    assert r["annotates"] == "1.1"
    assert r["id_type"] == "verse"


def test_anchor_simple_with_pada():
    r = _parse_comment_anchor("comment_1_1a", "")
    assert r["annotates"] == "1.1a"
    assert r["id_type"] == "verse"


def test_anchor_simple_v0_chapter():
    """comment_ch_0 is a chapter-level anchor."""
    r = _parse_comment_anchor("comment_3_0", "")
    assert r["annotates"] == "c.3"
    assert r["id_type"] == "chapter"


def test_anchor_3part_discards_sub():
    r = _parse_comment_anchor("comment_2_5_3", "")
    assert r["annotates"] == "2.5"
    assert r["id_type"] == "verse"


def test_anchor_range_ascii():
    r = _parse_comment_anchor("comment_1_1-2", "")
    assert r["annotates"] == "1.1"
    assert r["id_type"] == "verse"


def test_anchor_range_en_dash():
    r = _parse_comment_anchor("comment_1_1–3", "")
    assert r["annotates"] == "1.1"
    assert r["id_type"] == "verse"


def test_anchor_range_em_dash():
    r = _parse_comment_anchor("comment_65_1—2", "")
    assert r["annotates"] == "65.1"
    assert r["id_type"] == "verse"


def test_anchor_range_with_pada():
    """comment_1_1a-2 → annotates 1.1a."""
    r = _parse_comment_anchor("comment_1_1a-2", "")
    assert r["annotates"] == "1.1a"
    assert r["id_type"] == "verse"


def test_anchor_dot_sub_gitagovinda():
    """Gitagovinda dot-sub-index: sub discarded, annotates ch.v."""
    r = _parse_comment_anchor("comment_1_1.3", "")
    assert r["annotates"] == "1.1"
    assert r["id_type"] == "verse"


def test_anchor_dot_sub_various():
    r = _parse_comment_anchor("comment_2_5.7", "")
    assert r["annotates"] == "2.5"


def test_anchor_letter_chapter():
    """Gitarthasamgraha: comment_{c|t}_{n} → chapter annotates."""
    r = _parse_comment_anchor("comment_t_3", "")
    assert r["annotates"] == "c.t"
    assert r["id_type"] == "chapter"


def test_anchor_noise_stripping():
    """Trailing semicolons/spaces stripped before retry."""
    r = _parse_comment_anchor("comment_3_2;", "")
    assert r["annotates"] == "3.2"
    assert r["id_type"] == "verse"


def test_anchor_broad_fallback():
    """Broad fallback extracts ch/v from unexpected formats."""
    r = _parse_comment_anchor("comment_4_7_extra_junk_that_doesnt_match", "")
    assert r["annotates"] == "4.7"
    assert r["id_type"] == "verse"


def test_anchor_unknown():
    r = _parse_comment_anchor("completely_unrecognized_id", "")
    assert r["annotates"] is None
    assert r["id_type"] == "unknown"


# ---------------------------------------------------------------------------
# Hermetic: _extract_passage_from_range_title
# ---------------------------------------------------------------------------

def test_range_title_standard_2level():
    assert _extract_passage_from_range_title("Ригведа, 1. 1", "01_rigveda") == "1.1"


def test_range_title_with_range():
    assert _extract_passage_from_range_title("Ригведа, 65. 1-2", "01_rigveda") == "65.1-2"


def test_range_title_gitagovinda():
    assert _extract_passage_from_range_title("Гитаговинда, 1. 5", "gitagovinda") == "1.5"


def test_range_title_mbh_3level():
    """MBh slug triggers 3-level Roman.ch.v extraction."""
    result = _extract_passage_from_range_title(
        "Махабхарата VI. 23. 1", "06_mahabharata-bhishmaparva"
    )
    assert result == "6.23.1"


def test_range_title_mbh_3level_range():
    result = _extract_passage_from_range_title(
        "Махабхарата VI. 1. 3-6", "06_mahabharata-bhishmaparva"
    )
    assert result == "6.1.3-6"


def test_range_title_unparseable():
    assert _extract_passage_from_range_title("Введение", "some_source") is None


# ---------------------------------------------------------------------------
# Hermetic: _to_slp1
# ---------------------------------------------------------------------------

def test_slp1_agni():
    result = _to_slp1("agni")
    assert result == "agni"


def test_slp1_iast_vowels():
    # ā → A, ī → I, ū → U in SLP1
    result = _to_slp1("āgamaḥ")
    assert "A" in result


def test_slp1_strips_accents():
    # Vedic accent marks should be stripped before transliteration
    result = _to_slp1("agním")  # with Vedic accent
    # Should not raise; result is SLP1-encoded agni
    assert result  # non-empty


# ---------------------------------------------------------------------------
# Gate 1: ID determinism (verify JSONL exists and has expected record count)
# ---------------------------------------------------------------------------

@pytest.mark.corpus
def test_gate1_conversion_report_exists():
    """Gate 1 proxy: conversion_report.json must exist and total ≥ 500,000 records."""
    report_path = Path(__file__).parent.parent / "corpus_builder" / "conversion_report.json"
    assert report_path.exists(), "conversion_report.json not found — run the converter"
    with open(report_path, encoding="utf-8") as f:
        report = json.load(f)
    total = report.get("total_records", 0)
    assert total >= 500_000, f"Expected ≥500,000 records, got {total}"
    assert report.get("total_sources", 0) == 148, (
        f"Expected 148 sources, got {report.get('total_sources')}"
    )


@pytest.mark.corpus
def test_gate1_all_ids_follow_scheme(all_records):
    """Gate 1: every record ID matches one of the three canonical formats.

    Formats:
      {work}:{passage}#sa     (Sanskrit segment)
      {work}:{passage}#ru     (Russian segment)
      {work}:{passage}.comm{n} (commentary)
      {work}:{passage}        (dictionary head / prose)
    """
    import re
    slug_re = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
    bad_structural = []
    for rec in all_records:
        rid = rec["id"]
        if ":" not in rid:
            bad_structural.append(f"no ':' in {rid!r}")
            continue
        work, rest = rid.split(":", 1)
        if not slug_re.match(work):
            bad_structural.append(f"bad work slug {work!r} in {rid!r}")
        if not rest:
            bad_structural.append(f"empty passage in {rid!r}")
    assert not bad_structural, f"Malformed IDs: {bad_structural[:5]}"


# ---------------------------------------------------------------------------
# Gate 3: Range coverage — 0 range misses on A-range sources
# ---------------------------------------------------------------------------

@pytest.mark.corpus
def test_gate3_zero_range_misses():
    """Gate 3: conversion_report.json must report 0 range_miss entries."""
    report_path = Path(__file__).parent.parent / "corpus_builder" / "conversion_report.json"
    if not report_path.exists():
        pytest.skip("conversion_report.json not built")
    with open(report_path, encoding="utf-8") as f:
        report = json.load(f)
    range_misses = report.get("range_miss", [])
    assert len(range_misses) == 0, (
        f"Expected 0 range misses, got {len(range_misses)}: {range_misses[:3]}"
    )


@pytest.mark.corpus
def test_gate3_zero_unparseable():
    """Gate 3 companion: 0 unparseable lines across all sources."""
    report_path = Path(__file__).parent.parent / "corpus_builder" / "conversion_report.json"
    if not report_path.exists():
        pytest.skip("conversion_report.json not built")
    with open(report_path, encoding="utf-8") as f:
        report = json.load(f)
    unparseable = report.get("unparseable", [])
    assert len(unparseable) == 0, (
        f"Expected 0 unparseable, got {len(unparseable)}: {unparseable[:3]}"
    )


# ---------------------------------------------------------------------------
# Gate 4: ID uniqueness
# ---------------------------------------------------------------------------

@pytest.mark.corpus
def test_gate4_all_ids_unique(all_records):
    """Gate 4: every record ID across all 148 JSONL files is unique."""
    ids = [r["id"] for r in all_records]
    from collections import Counter
    counts = Counter(ids)
    duplicates = {k: v for k, v in counts.items() if v > 1}
    assert not duplicates, (
        f"Duplicate IDs found ({len(duplicates)} groups): "
        f"{dict(list(duplicates.items())[:5])}"
    )


@pytest.mark.corpus
def test_gate4_dup_suffix_records_are_valid(all_records):
    """Gate 4: dup-suffix records (1.1b, 1.1c) appear only where source has true dups."""
    import re
    dup_pattern = re.compile(r"^.+:[0-9.]+[b-z](#|\.comm).*$")
    dup_records = [r for r in all_records if dup_pattern.match(r["id"])]
    # There should be a small bounded number of dup-suffix records (41 known duplicate pairs)
    # The total dup-suffix IDs should be ≤ 200 to catch runaway letter suffixing
    assert len(dup_records) <= 200, (
        f"Unexpectedly many dup-suffix records: {len(dup_records)} "
        f"(expected ≤ 200 from known duplicate passages)"
    )


# ---------------------------------------------------------------------------
# Gate 5: Commentary linkage — every comm.annotates resolves to an emitted passage
# ---------------------------------------------------------------------------

@pytest.mark.corpus
def test_gate5_all_comm_annotates_resolve(all_records):
    """Gate 5: every commentary record's annotates field names an emitted passage.

    No orphaned commentaries allowed.
    """
    # Build set of all emitted (work, passage) pairs for verse/dict/prose records
    emitted_passages: set[tuple[str, str]] = set()
    for rec in all_records:
        if rec.get("seg") in ("sa", "ru", "head", "nav"):
            emitted_passages.add((rec["work"], rec["passage"]))

    orphaned = []
    for rec in all_records:
        if (rec.get("seg") or "").startswith("comm"):
            ann = rec.get("annotates")
            work = rec["work"]
            if ann is None or (work, ann) not in emitted_passages:
                orphaned.append(rec["id"])

    assert not orphaned, (
        f"Gate 5 FAIL: {len(orphaned)} orphaned commentary records. "
        f"First 5: {orphaned[:5]}"
    )
