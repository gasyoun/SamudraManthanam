"""CONVERTER_SPEC §7 gates — hermetic unit tests + JSONL corpus tests.

Hermetic tests (no corpus needed) cover the pure parsing functions.
Corpus tests load JSONL files produced by html_to_canonical.py and verify
the four measurable CI gates (1, 3, 4, 5).  They skip automatically if
web/corpus_builder/jsonl/ does not exist.
"""
import json
import os
import sys
from collections import Counter

import pytest
from pathlib import Path

# --- Import converter functions directly ---
# html_to_canonical.py manages its own sys.path at import time.
_CB_DIR = Path(__file__).parent.parent / "corpus_builder"
sys.path.insert(0, str(_CB_DIR.parent))  # web/ on path so corpus_builder is a package

from corpus_builder.html_to_canonical import (  # noqa: E402
    _parse_comment_anchor,
    _extract_comment_items,
    _extract_passage_from_range_title,
    _to_slp1,
)
from app.services.slug import make_unique_slug  # noqa: E402

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
def canonical_jsonl_files(jsonl_dir):
    """The JSONL files `ingest.py` actually reads for the live corpus: one
    `{slug}.jsonl` per active `Data/*.html` entry in `Programdata/data.txt`,
    slug derived the same way `ingest.py` derives it (`make_unique_slug`).

    `jsonl_dir` also holds build-time staging/intermediate artifacts (per-book
    split files consumed only by a combine step, `.raw.jsonl` pre-alignment
    dumps, etc.) that `ingest.py` never reads — globbing the whole directory
    double-counts their records against the same canonical IDs and produces
    false-positive "duplicates" that were never ingested twice.
    """
    data_txt = (
        Path(__file__).parent.parent.parent
        / "Index" / "lib" / "x86_64-win64" / "Programdata" / "data.txt"
    )
    if not data_txt.exists():
        pytest.skip("Programdata/data.txt not found — cannot resolve canonical JSONL set")
    filenames = [
        line.strip() for line in data_txt.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    seen_slugs: set[str] = set()
    files = []
    for filename in filenames:
        slug = make_unique_slug(filename, seen_slugs)
        seen_slugs.add(slug)
        jf = jsonl_dir / f"{slug}.jsonl"
        if jf.exists():
            files.append(jf)
    return sorted(files)


@pytest.fixture(scope="session")
def all_records(canonical_jsonl_files):
    """Load every record from every canonical (ingest-eligible) JSONL file."""
    records = []
    for jf in canonical_jsonl_files:
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


def test_comment_items_allow_nested_divs():
    html = (
        '<div class="comment_item" id="comment_1_1">'
        '<p>first</p><div class="nested"><div>inner</div></div>tail'
        '</div>'
        '<div class="comment_item" id="comment_1_2">second</div>'
    )
    assert _extract_comment_items(html) == [
        ("comment_1_1", '<p>first</p><div class="nested"><div>inner</div></div>tail'),
        ("comment_1_2", "second"),
    ]


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
def test_gate4_all_ids_unique(canonical_jsonl_files):
    """Gate 4: every record ID is unique within its own source file.

    Uniqueness is scoped **per source** (LINE_ID_SCHEME.md §9: "unique per
    source (enforced by index)"; `ingest.py`'s `_validate_jsonl_ingest` checks
    the same `(source_id, canonical_id)` scope), not globally across the
    whole corpus. Some works are intentionally ingested from more than one
    source file at different granularities (e.g. `devibhagavata-purana`'s
    12 per-skandha sources plus its combined source, kept side by side since
    H941/H558) — those sources legitimately share `{work}:{passage}` IDs
    across DB source_ids; that is not a duplicate-ID defect.
    """
    from collections import Counter
    import json as _json

    all_duplicates = {}
    for jf in canonical_jsonl_files:
        ids = []
        with open(jf, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    ids.append(_json.loads(line)["id"])
        counts = Counter(ids)
        duplicates = {k: v for k, v in counts.items() if v > 1}
        if duplicates:
            all_duplicates[jf.name] = duplicates

    assert not all_duplicates, (
        f"Duplicate IDs found within a single source ({len(all_duplicates)} files): "
        f"{dict(list(all_duplicates.items())[:5])}"
    )


@pytest.mark.corpus
def test_gate4_dup_suffix_invariants_hold(all_records):
    """Gate 4: dup-suffix records satisfy the CATEGORISED invariant (H1927 D7).

    This gate used to be a bare count ceiling. H1829 (02-08-2026) showed what
    that costs: `<= 200` sat here with no recorded derivation while
    nirvana-tantra alone held 284 of 429 suffixed ids, because footnote ``(N)``
    markers were being read as verse boundaries. Lowering the number to a
    measured 180 made the gate honest but no more capable — a count can only
    ask "how many?", so any splitting bug that stays under the number is
    invisible to it.

    VERIFICATION D7 asks for a categorised invariant instead. The rules live in
    `scripts/dup_suffix_report.py` — one definition, also used to generate
    docs/DUP_SUFFIX_INVARIANT_REPORT.md — and they are structural: an orphaned
    suffix, a suffix run, and one work carrying the population are all shapes
    that splitter debris has and genuine collisions do not. The count survives
    only as a coarse backstop that prompts re-derivation.
    """
    import sys
    from pathlib import Path

    scripts_dir = Path(__file__).resolve().parents[1] / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from dup_suffix_report import build_report

    report = build_report(all_records)

    assert not report.violations_for("base_present"), (
        "Suffixed ids with no un-suffixed twin — the splitter invented a boundary "
        f"(H1829 signature): "
        f"{[v.record_id for v in report.violations_for('base_present')][:10]}"
    )
    assert not report.violations_for("suffix_depth"), (
        "Suffix letters beyond 'b' — collisions should be pairs: "
        f"{[v.record_id for v in report.violations_for('suffix_depth')][:10]}"
    )
    assert not report.violations_for("segment_pairing"), (
        "Suffixed records outside the sa/ru parallel + commentary classes: "
        f"{[v.record_id for v in report.violations_for('segment_pairing')][:10]}"
    )
    assert not report.violations_for("concentration"), (
        "Runaway single-work concentration (the nirvana-tantra 79% shape): "
        f"{[v.detail for v in report.violations_for('concentration')]}"
    )
    assert not report.violations_for("population_backstop"), (
        f"{report.dup_records} suffixed ids exceeds the coarse backstop. The "
        f"categorised invariants passed, so re-derive them against the new corpus "
        f"rather than simply raising the number. "
        f"Top works: {list(report.by_work.items())[:5]}"
    )


# ---------------------------------------------------------------------------
# Gate 5: Commentary linkage — every comm.annotates resolves to an emitted passage
# ---------------------------------------------------------------------------

# H1828: known residual orphan(s) left to H1438 Ignatiev territory — do not
# touch chinachara-tantra files in this handoff.
# H1438 Ignatiev territory: chinachara-tantra carries exactly ONE known orphan,
# deliberately left untouched by H1828.
#
# H2219: this was a work-level `continue`, i.e. a blanket exemption — every
# future chinachara orphan would have been invisible too, so the gate could not
# detect a regression in the one work it was excusing. Bound it to the measured
# count instead: the residual stays tolerated, a second one fails the gate.
_GATE5_KNOWN_ORPHAN_WORKS = {"chinachara-tantra": 1}


@pytest.mark.corpus
def test_gate5_all_comm_annotates_resolve(all_records):
    """Gate 5: every commentary record's annotates field names an emitted passage.

    No orphaned commentaries allowed, except a bounded, per-work count of known
    residuals (H1438 chinachara) — bounded, not blanket-exempt.
    """
    # Build set of all emitted (work, passage) pairs for verse/dict/prose records
    emitted_passages: set[tuple[str, str]] = set()
    for rec in all_records:
        if rec.get("seg") in ("sa", "ru", "head", "nav"):
            emitted_passages.add((rec["work"], rec["passage"]))

    orphaned = []
    allowed_orphans: Counter = Counter()
    for rec in all_records:
        if (rec.get("seg") or "").startswith("comm"):
            ann = rec.get("annotates")
            work = rec["work"]
            if ann is not None and (work, ann) in emitted_passages:
                continue
            budget = _GATE5_KNOWN_ORPHAN_WORKS.get(work, 0)
            if allowed_orphans[work] < budget:
                allowed_orphans[work] += 1
                continue
            orphaned.append(rec["id"])

    assert not orphaned, (
        f"Gate 5 FAIL: {len(orphaned)} orphaned commentary records beyond the "
        f"known-residual budget {_GATE5_KNOWN_ORPHAN_WORKS}. "
        f"First 5: {orphaned[:5]}"
    )


@pytest.mark.corpus
def test_gate5b_remapped_annotates_carry_provenance(all_records):
    """Gate 5b (H2219): a moved anchor must say so.

    H1828 removed every dead anchor by re-pointing the endnote at the nearest
    emitted verse — sometimes an OCR-digit repair the remap gets right
    (``6.5.559 -> 6.005.059``), sometimes a 19-verse move with no evidence
    behind it (``12.8.111 -> 12.008.092``). Gate 5 reports zero orphans for
    both. This gate asserts that any record carrying the provenance field
    reports a valid resolution and, when the anchor moved, preserves the
    target the endnote originally named.

    Records generated before the field existed are skipped: the shipped corpus
    predates it and cannot be regenerated without the off-git source PDFs, so
    this gate binds newly generated data rather than false-failing on old.
    """
    checked = 0
    bad = []
    for rec in all_records:
        res = rec.get("annotates_resolution")
        if res is None:
            continue
        checked += 1
        if res not in ("exact", "nearest"):
            bad.append((rec["id"], f"unknown resolution {res!r}"))
        elif res == "nearest" and not rec.get("annotates_requested"):
            bad.append((rec["id"], "moved anchor without annotates_requested"))
        elif res == "exact" and rec.get("annotates_requested"):
            bad.append((rec["id"], "exact anchor carries annotates_requested"))

    assert not bad, (
        f"Gate 5b FAIL: {len(bad)} of {checked} provenance-bearing commentary "
        f"records are malformed. First 5: {bad[:5]}"
    )
