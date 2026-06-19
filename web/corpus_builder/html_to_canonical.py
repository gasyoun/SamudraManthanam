#!/usr/bin/env python3
"""HTML→JSONL converter for the Samudra Manthanam corpus.

Implements:
  - CONVERTER_SPEC.md  (4 parse paths, segment schema, commentary, SLP1, 7 gates)
  - ALIGNMENT_SPEC.md  (group model, cardinality, refrain/alt_ref handling)
  - LINE_ID_SCHEME.md  (canonical passage IDs, duplicate disambiguation)

Usage:
    python web/corpus_builder/html_to_canonical.py \\
        --corpus-path Index/lib/x86_64-win64 \\
        --output-dir  web/corpus_builder/jsonl
"""

import sys
import os
import re
import json
import argparse
from pathlib import Path
from typing import Iterator, Optional

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_WEB_DIR = _REPO_ROOT / "web"
sys.path.insert(0, str(_WEB_DIR))

from app.services.slug import make_unique_slug  # noqa: E402
from ingest.parse_html import (  # noqa: E402
    remove_html_tags,
    VEDIC_MAP,
    _CITATION_BLOCK_ID,
    _RANGE_DIV_TITLE,
    _RANGE_TITLE_VERSE,
)
from indic_transliteration import sanscript  # noqa: E402

# ---------------------------------------------------------------------------
# Roman numeral table (for MBh 3-level passage IDs — LINE_ID_SCHEME §8.1)
# ---------------------------------------------------------------------------
_ROMAN_MAP = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7,
    "VIII": 8, "IX": 9, "X": 10, "XI": 11, "XII": 12, "XIII": 13,
    "XIV": 14, "XV": 15, "XVI": 16, "XVII": 17, "XVIII": 18, "XIX": 19,
    "XX": 20,
}
_RANGE_TITLE_3LEVEL = re.compile(
    r"([IVXLC]+)\.\s*(\d+)\.\s*(\d+(?:-\d+)?)\s*$"
)

# ---------------------------------------------------------------------------
# Regex patterns for verse parsing
# ---------------------------------------------------------------------------

# Detect A-clean vs A-range: does the citation_block div itself have an id?
# (parse_html.py already exports _CITATION_BLOCK_ID for the same check)
_CB_HAS_ID = re.compile(r"class=[\"']citation_block[\"'][^>]*\sid=[\"']")

# Chapter-title div: <div class="chapter_title" id="...">text</div>
_CHAPTER_TITLE_RE = re.compile(
    r'<div\s+class=["\']chapter_title["\']\s+id=["\']([^"\']+)["\']\s*>(.*?)</div>',
    re.DOTALL,
)
# H1 header (some sources)
_H1_RE = re.compile(r"<H1\b[^>]*>(.*?)</H1>", re.IGNORECASE | re.DOTALL)

# Sanskrit block: <div class="chapter_block iast">…</div>
_IAST_BLOCK_RE = re.compile(
    r'<div\s+class=["\']chapter_block\s+iast["\']\s*>(.*?)</div>', re.DOTALL
)
# Russian block: <div class="chapter_block translation">…</div>
_TRANS_BLOCK_RE = re.compile(
    r'<div\s+class=["\']chapter_block\s+translation["\']\s*>(.*?)</div>',
    re.DOTALL,
)

# Comments section: <div class="comments">…</div>  (lazy up to first </div>…)
# We extract the entire inner body then find individual comment_items.
_COMMENTS_SECTION_RE = re.compile(
    r'<div\s+class=["\']comments["\']\s*>(.*?)</div>\s*</div>\s*$', re.DOTALL
)

# Individual comment items — depth-counting to handle nested <div> elements correctly.
_COMMENT_ITEM_START_RE = re.compile(
    r'<div\s+class=["\']comment_item["\']\s+id=["\']([^"\']+)["\']\s*>',
    re.DOTALL,
)


def _extract_comment_items(html: str) -> list[tuple[str, str]]:
    items = []
    pos = 0
    while pos < len(html):
        m = _COMMENT_ITEM_START_RE.search(html, pos)
        if not m:
            break
        anchor_id = m.group(1)
        inner_start = m.end()
        depth = 1
        i = inner_start
        while i < len(html) and depth > 0:
            if html[i : i + 4] == "<div":
                depth += 1
                i += 4
            elif html[i : i + 6] == "</div>":
                depth -= 1
                if depth == 0:
                    break
                i += 6
            else:
                i += 1
        items.append((anchor_id, html[inner_start:i]))
        pos = i + 6
    return items

# Parse comment_item id: comment_{chapter}_{verse}[{pada}]  (simple: exact match)
_COMMENT_ID_RE = re.compile(r"^comment_(\d+)_(\d+)([a-z]?)$")
# Three-part: comment_{ch}_{v}_{sub_index} — {sub_index} is discarded; annotates = ch.v
_COMMENT_ID_3PART_RE = re.compile(r"^comment_(\d+)_(\d+)_\d+$")
# Range anchors (ASCII hyphen, figure-dash U+2012, en-dash U+2013, em-dash U+2014):
#   comment_{ch}_{v1}[{pada1}][-‒–—]{v2_or_pada2}
# We extract only the start of the range; the end is discarded.
_COMMENT_ID_RANGE_RE = re.compile(
    r"^comment_(\d+)_(\d+)([a-z]?)[-‒–—]\S+$"
)
# Chapter-level comment: chapter_{N}C or chapter_{N}c
_CHAPTER_C_ID_RE = re.compile(r"^chapter_(\d+)[Cc]$")

# Translation-author span (strip from text, keep in html)
_AUTHOR_SPAN_RE = re.compile(
    r'<span\s+class=["\']translation_author["\']\s*>(.*?)</span>', re.DOTALL
)
# IAST author span (Sanskrit speaker label)
_IAST_AUTHOR_RE = re.compile(
    r'<span\s+class=["\']iast_author["\']\s*>(.*?)</span>', re.DOTALL
)
# Inline comment-reference anchor (keep in html, strip from text)
_COMMENT_SUB_RE = re.compile(
    r"<a\s[^>]*class=['\"]comment_sub['\"][^>]*>.*?</a>", re.DOTALL
)

# Dhruva (Gitagovinda refrain) markers
_DHRUVA_SA_RE = re.compile(r"॥dhruva॥")
_DHRUVA_RU_RE = re.compile(
    r'<span\s+class=["\']translation_dhruva["\']\s*>', re.DOTALL
)

# Gitagovinda alt_ref: song-relative (N.N) at end of iast text
_GG_ALT_REF_RE = re.compile(r"\((\d+\.\d+)\)\s*$")

# Detect HTML/head/body wrapper lines to skip
_SKIP_RE = re.compile(r"^\s*</?(?:html|head|body)[^>]*>\s*$", re.IGNORECASE)

# endchapter span to trim from lines (existing logic)
_ENDCHAPTER_RE = re.compile(r'<span\s+class=["\']endchapter["\']>.*', re.IGNORECASE | re.DOTALL)

# ---------------------------------------------------------------------------
# Dictionary patterns
# ---------------------------------------------------------------------------

# 5-field tab format: /deva/\t/iast/\t/slp1/\t/cyrillic/\tgloss
_DICT_5FIELD_RE = re.compile(
    r"^/([^/]*)/\t/([^/]*)/\t/([^/]*)/\t/([^/]*)/\t(.*)$"
)

# Non-tab Kochergina: °headword /iast/ definition
_DICT_KOCHERGINA_RE = re.compile(r"^°(.+?)\s+/([^/]+)/\s+(.*)$")

# Non-tab Kossovich: N deva /iast/ /iast_variant/ /cyrillic/ definition
# (has numeric prefix)
_DICT_KOSSOVICH_RE = re.compile(
    r"^\d+\s+(\S+)\s+/([^/]+)/\s+/([^/]+)/\s+/([^/]+)/\s+(.*)$"
)

# Generic non-tab with /iast/ somewhere
_DICT_GENERIC_IAST_RE = re.compile(r"/([^/]+)/")

# ---------------------------------------------------------------------------
# Script-detection helpers
# ---------------------------------------------------------------------------
_DEVANAGARI_RE = re.compile(r"[ऀ-ॿ]")
_IAST_DIACRIT_RE = re.compile(
    r"[āīūṛṝḷḹṅñṭḍṇśṣṃḥĀĪŪṚṜḶḸṄÑṬḌṆŚṢṂḤ]"
)
_CYRILLIC_RE = re.compile(r"[Ѐ-ӿ]")


def _detect_script(text: str) -> str:
    if _DEVANAGARI_RE.search(text):
        return "devanagari"
    if _IAST_DIACRIT_RE.search(text):
        return "iast"
    if _CYRILLIC_RE.search(text):
        return "cyrillic"
    return "mixed"


# ---------------------------------------------------------------------------
# SLP1 / accent normalization
# ---------------------------------------------------------------------------

def _strip_accents(text: str) -> str:
    """Remove Vedic accent diacritics for search-ready text."""
    for accented, plain in VEDIC_MAP.items():
        text = text.replace(accented, plain)
    return text


def _to_slp1(iast_text: str) -> str:
    """Transliterate IAST text to SLP1 (accent-stripped first)."""
    plain = _strip_accents(iast_text)
    try:
        return sanscript.transliterate(plain, sanscript.IAST, sanscript.SLP1)
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Roman numeral helper
# ---------------------------------------------------------------------------

def _roman_to_int(s: str) -> Optional[int]:
    return _ROMAN_MAP.get(s.upper())


_MBH_SLUG_RE = re.compile(r"^(\d+)_mahabharata")


def _get_mbh_book_num(slug: str) -> Optional[int]:
    """Extract numeric book number from MBh parvan slug (e.g. '06_mahabharata…' → 6)."""
    m = _MBH_SLUG_RE.match(slug)
    return int(m.group(1)) if m else None


# ---------------------------------------------------------------------------
# Passage extraction for range-title sources
# ---------------------------------------------------------------------------

def _extract_passage_from_range_title(title: str, slug: str) -> Optional[str]:
    """Extract canonical passage from range div title.

    For MBh parvans (slug contains 'mahabharata'), returns 3-level N.N.N
    per LINE_ID_SCHEME §8.1.  All other sources return 2-level N.N.
    """
    if "mahabharata" in slug:
        m3 = _RANGE_TITLE_3LEVEL.search(title)
        if m3:
            book_num = _roman_to_int(m3.group(1))
            if book_num is not None:
                return f"{book_num}.{m3.group(2)}.{m3.group(3)}"
    # Standard 2-level
    cv = _RANGE_TITLE_VERSE.search(title)
    if cv:
        return f"{cv.group(1)}.{cv.group(2)}"
    return None


# ---------------------------------------------------------------------------
# Commentary ID parsing  (CONVERTER_SPEC §4, LINE_ID_SCHEME §4)
# ---------------------------------------------------------------------------

def _parse_comment_anchor(anchor_id: str, current_chapter: str) -> dict:
    """Parse a comment_item id into annotates metadata.

    Returns dict with keys: annotates, id_type ('verse'|'chapter'|'unknown')

    Handled anchor formats (in order tried):
      comment_{ch}_{v}[{pada}]          — simple exact
      comment_{ch}_{v}_{sub_index}      — 3-part; sub_index discarded
      comment_{ch}_{v1}[{pada}][-–—‒]… — ASCII/Unicode range; end discarded
      comment_{ch}_{v}.{sub_index}      — dot-sub-index (Gitagovinda)
      comment_{letter}_{n}              — letter chapter (Gitarthasamgraha)
      chapter_{N}C|c                    — chapter-level

    A best-effort pre-strip removes trailing noise chars before retrying.
    """
    def _try(aid: str) -> Optional[dict]:
        # Simple exact
        m = _COMMENT_ID_RE.match(aid)
        if m:
            ch, v, pada = m.group(1), m.group(2), m.group(3)
            if v == "0":
                return {"annotates": f"c.{ch}", "id_type": "chapter"}
            return {"annotates": f"{ch}.{v}{pada}", "id_type": "verse"}

        # Three-part underscore: comment_ch_v_sub
        m3 = _COMMENT_ID_3PART_RE.match(aid)
        if m3:
            ch, v = m3.group(1), m3.group(2)
            if v == "0":
                return {"annotates": f"c.{ch}", "id_type": "chapter"}
            return {"annotates": f"{ch}.{v}", "id_type": "verse"}

        # Range with ASCII hyphen / en-dash / em-dash / figure-dash (U+2012)
        mr = _COMMENT_ID_RANGE_RE.match(aid)
        if mr:
            ch, v, pada = mr.group(1), mr.group(2), mr.group(3)
            if v == "0":
                return {"annotates": f"c.{ch}", "id_type": "chapter"}
            return {"annotates": f"{ch}.{v}{pada}", "id_type": "verse"}

        # Dot-sub-index: comment_ch_v.sub (e.g. comment_1_1.3 in Gitagovinda)
        mdot = re.match(r"^comment_(\d+)_(\d+)\.(\d+)$", aid)
        if mdot:
            ch, v = mdot.group(1), mdot.group(2)
            if v == "0":
                return {"annotates": f"c.{ch}", "id_type": "chapter"}
            return {"annotates": f"{ch}.{v}", "id_type": "verse"}

        # Letter chapter: comment_{c|t|...}_{n} (Gitarthasamgraha: c=canto, t=tantra)
        mlc = re.match(r"^comment_([a-z])_(\d+)$", aid)
        if mlc:
            letter = mlc.group(1)
            return {"annotates": f"c.{letter}", "id_type": "chapter"}

        # Chapter-level: chapter_NC
        mc = _CHAPTER_C_ID_RE.match(aid)
        if mc:
            return {"annotates": f"c.{mc.group(1)}", "id_type": "chapter"}

        return None

    result = _try(anchor_id)
    if result is not None:
        return result

    # Best-effort: strip trailing noise chars and retry once
    stripped = re.sub(r"[;,*):\-\s]+$", "", anchor_id)
    if stripped != anchor_id:
        result = _try(stripped)
        if result is not None:
            return result

    # Broad fallback: extract comment_{ch}_{v}[optional_pada] from the start,
    # ignoring all trailing content (multi-pada, Cyrillic pada, appended text).
    # Pada match covers ASCII and Cyrillic single letters (Latin a-z, а-яёА-ЯЁ).
    mbroad = re.match(
        r"^comment_(\d+)_(\d+)([a-zA-Zа-яёА-ЯЁ]?)", anchor_id
    )
    if mbroad:
        ch, v, pada = mbroad.group(1), mbroad.group(2), mbroad.group(3)
        if v == "0":
            return {"annotates": f"c.{ch}", "id_type": "chapter"}
        return {"annotates": f"{ch}.{v}{pada}", "id_type": "verse"}

    return {"annotates": None, "id_type": "unknown"}


# ---------------------------------------------------------------------------
# HTML inner-content extraction helpers
# ---------------------------------------------------------------------------

def _inner_html(match_group: str) -> str:
    """Return raw inner HTML with endchapter trimmed."""
    return _ENDCHAPTER_RE.sub("", match_group).strip()


def _strip_for_text(html: str) -> str:
    """Convert inner HTML to plain searchable text."""
    # Remove comment-sub reference anchors
    html = _COMMENT_SUB_RE.sub("", html)
    return remove_html_tags(html)


def _extract_author(html: str) -> Optional[str]:
    """Extract and strip translation_author / iast_author from html.

    Returns (stripped_html, author_text_or_None).
    """
    author = None
    m = _AUTHOR_SPAN_RE.search(html)
    if m:
        author = remove_html_tags(m.group(1)).strip().rstrip("$:").strip()
        html = _AUTHOR_SPAN_RE.sub("", html, count=1)
    m2 = _IAST_AUTHOR_RE.search(html)
    if m2:
        if not author:
            author = remove_html_tags(m2.group(1)).strip()
        html = _IAST_AUTHOR_RE.sub("", html, count=1)
    return html, author


# ---------------------------------------------------------------------------
# ID-minting state per source
# ---------------------------------------------------------------------------

class SourceIDState:
    """Tracks minted passage IDs within a source to detect/disambiguate dups."""

    def __init__(self):
        self._seen: dict[str, int] = {}  # passage_key → count of occurrences
        self._seq: int = 0              # for e{n} / p{n} sequences

    def mint_verse_passage(self, raw_passage: str) -> str:
        """Return stable canonical passage with letter-suffix for dups."""
        count = self._seen.get(raw_passage, 0)
        self._seen[raw_passage] = count + 1
        if count == 0:
            return raw_passage
        # 2nd occurrence → 'b', 3rd → 'c', …
        suffix = chr(ord("a") + count)  # 1→'b', 2→'c', ...
        return f"{raw_passage}{suffix}"

    def mint_seq(self) -> int:
        """Return next 1-based sequence number (for e{n}, p{n})."""
        self._seq += 1
        return self._seq

    def mint_comm_seq(self, passage: str) -> int:
        """Return next commentary sequence for a given passage."""
        key = f"__comm__{passage}"
        count = self._seen.get(key, 0)
        self._seen[key] = count + 1
        return count + 1


# ---------------------------------------------------------------------------
# Verse record builders
# ---------------------------------------------------------------------------

def _build_sa_record(
    slug: str, passage: str, group: str, sa_html: str,
    chapter: str, seq: int, structure: str,
) -> dict:
    sa_html_clean, author = _extract_author(sa_html)
    sa_html_clean = sa_html_clean.strip()
    sa_text_accented = _strip_for_text(sa_html_clean)
    sa_text = _strip_accents(sa_text_accented)
    slp1 = _to_slp1(sa_text_accented)

    # Dhruva detection
    dhruva = bool(_DHRUVA_SA_RE.search(sa_html_clean))

    # Gitagovinda alt_ref: extract from raw iast text
    alt_ref = None
    if "gitagovinda" in slug:
        agm = _GG_ALT_REF_RE.search(sa_text_accented)
        if agm:
            alt_ref = agm.group(1)

    record = {
        "id": f"{slug}:{passage}#sa",
        "work": slug,
        "passage": passage,
        "seg": "sa",
        "group": group,
        "lang": "sa",
        "script": "iast",
        "text": sa_text,
        "html": sa_html_clean,
        "slp1": slp1,
        "structure": structure,
        "chapter": chapter,
        "seq": seq,
        "deleted": False,
    }
    if author:
        record["author"] = author
    if dhruva:
        record["dhruva"] = True
    if alt_ref:
        record["alt_ref"] = alt_ref
    return record


def _build_ru_record(
    slug: str, passage: str, group: str, ru_html: str,
    chapter: str, seq: int, structure: str,
) -> dict:
    ru_html_clean, author = _extract_author(ru_html)
    ru_html_clean = ru_html_clean.strip()
    ru_text = _strip_for_text(ru_html_clean)

    dhruva = bool(_DHRUVA_RU_RE.search(ru_html))

    record = {
        "id": f"{slug}:{passage}#ru",
        "work": slug,
        "passage": passage,
        "seg": "ru",
        "group": group,
        "lang": "ru",
        "script": "cyrillic",
        "text": ru_text,
        "html": ru_html_clean,
        "structure": structure,
        "chapter": chapter,
        "seq": seq,
        "deleted": False,
    }
    if author:
        record["author"] = author
    if dhruva:
        record["dhruva"] = True
    return record


def _build_comm_record(
    slug: str, annotates: str, comm_html: str,
    chapter: str, seq: int, structure: str,
    comm_n: int, needs_review: bool = False,
) -> dict:
    """Build a commentary record.

    The id and group are keyed to the ANNOTATED verse (annotates), not to
    the host citation_block the comment_item physically lives in.
    LINE_ID_SCHEME §4: commentary is addressed as '{work}:{annotates}.comm{n}'.
    """
    comm_text = _strip_for_text(comm_html)
    comm_id_passage = f"{annotates}.comm{comm_n}"
    # The group is the annotated verse — commentary is a member of that group
    group = f"{slug}:{annotates}"
    record = {
        "id": f"{slug}:{comm_id_passage}",
        "work": slug,
        "passage": comm_id_passage,
        "seg": f"comm{comm_n}",
        "group": group,
        "lang": "ru",
        "script": "cyrillic",
        "text": comm_text,
        "html": comm_html.strip(),
        "structure": structure,
        "chapter": chapter,
        "annotates": annotates,
        "seq": seq,
        "deleted": False,
    }
    if needs_review:
        record["needs_review"] = True
    return record


# ---------------------------------------------------------------------------
# Annotates resolution helper (Gate 5)
# ---------------------------------------------------------------------------

def _collect_verse_passages(lines: list[str], slug: str, path: str) -> set[str]:
    """Fast pre-scan — collect passage IDs of citation_blocks that have content.

    Only citation_blocks with non-empty IAST or translation text are included.
    This mirrors which blocks will actually emit sa/ru records, so the set can be
    used as the resolution universe for commentary annotates (Gate 5).
    """
    passages: set[str] = set()
    for raw in lines[1:]:
        line = raw.strip()
        if not line or _SKIP_RE.match(line) or "citation_block" not in line:
            continue
        if path == "clean":
            m = _CITATION_BLOCK_ID.search(line)
            pid = m.group(1) if m else None
        else:
            rtm = _RANGE_DIV_TITLE.search(line)
            pid = _extract_passage_from_range_title(rtm.group(1), slug) if rtm else None
        if not pid:
            continue
        # Include only if the citation_block has non-empty IAST or translation text
        sa_m = _IAST_BLOCK_RE.search(line)
        ru_m = _TRANS_BLOCK_RE.search(line)
        has_sa = sa_m and _strip_for_text(sa_m.group(1)).strip()
        has_ru = ru_m and _strip_for_text(ru_m.group(1)).strip()
        if has_sa or has_ru:
            passages.add(pid)
    return passages


def _resolve_annotates(ann: str, verse_passages: set[str], host_passage: str) -> str:
    """Return a resolved annotates that exists in verse_passages.

    Resolution order:
      1. Exact match → keep as-is
      2. Trailing ASCII/Cyrillic pada letter stripped → use stripped form
         (e.g. Rigveda comment_1_1a → annotates '1.1a' → stripped '1.1')
      3. Fall back to host_passage (always valid — the citation_block this
         comment physically lives in, e.g. ch-up '1.1' → host '1.1.1')
    """
    if ann in verse_passages:
        return ann
    if ann and ann[-1].isalpha():
        stripped = ann[:-1]
        if stripped in verse_passages:
            return stripped
    return host_passage


# ---------------------------------------------------------------------------
# Main parse paths
# ---------------------------------------------------------------------------

def _parse_verse_line(
    line: str, slug: str, path: str,
    current_chapter: str, seq_counter: list,
    id_state: SourceIDState, structure: str,
    report_data: dict,
    verse_passages: set,
) -> list[dict]:
    """Parse one citation_block line → list of JSONL records.

    path: 'clean' or 'range'
    seq_counter: [int] mutable box for current sequence number.
    verse_passages: pre-scanned set of all raw passage IDs for this source
        (used to resolve commentary annotates — Gate 5).
    """
    records = []

    # --- Extract passage key ---
    if path == "clean":
        m = _CITATION_BLOCK_ID.search(line)
        raw_passage = m.group(1) if m else None
    else:  # range
        rtm = _RANGE_DIV_TITLE.search(line)
        if rtm:
            raw_passage = _extract_passage_from_range_title(rtm.group(1), slug)
            if raw_passage is None:
                # Range title present but couldn't extract verse key
                report_data.setdefault("range_miss", []).append(
                    {"slug": slug, "title": rtm.group(1)}
                )
                raw_passage = None
        else:
            raw_passage = None

    if raw_passage is None:
        report_data.setdefault("unparseable", []).append(
            {"slug": slug, "line_prefix": line[:80]}
        )
        return records

    # Disambiguate duplicates
    passage = id_state.mint_verse_passage(raw_passage)
    if passage != raw_passage:
        report_data.setdefault("dup_suffixes", []).append(
            {"slug": slug, "raw": raw_passage, "minted": passage}
        )

    group = f"{slug}:{passage}"

    # --- Extract Sanskrit block ---
    sa_m = _IAST_BLOCK_RE.search(line)
    sa_html = _inner_html(sa_m.group(1)) if sa_m else ""

    # --- Extract Russian block ---
    ru_m = _TRANS_BLOCK_RE.search(line)
    ru_html = _inner_html(ru_m.group(1)) if ru_m else ""

    # --- Build sa/ru records ---
    sa_empty = not sa_html or not _strip_for_text(sa_html).strip()
    ru_empty = not ru_html or not _strip_for_text(ru_html).strip()

    if not sa_empty:
        seq_counter[0] += 1
        records.append(_build_sa_record(
            slug, passage, group, sa_html,
            current_chapter, seq_counter[0], structure,
        ))

    if not ru_empty:
        seq_counter[0] += 1
        records.append(_build_ru_record(
            slug, passage, group, ru_html,
            current_chapter, seq_counter[0], structure,
        ))

    # --- Commentary blocks ---
    # Find the comments section, then individual comment_items
    comm_m = _COMMENTS_SECTION_RE.search(line)
    comments_body = comm_m.group(1) if comm_m else ""
    # Also search the full line in case the section regex missed
    if not comments_body:
        comments_body = line

    comm_items = _extract_comment_items(comments_body)
    mbh_book = _get_mbh_book_num(slug) if "mahabharata" in slug else None
    for anchor_id, comm_inner in comm_items:
        comm_meta = _parse_comment_anchor(anchor_id, current_chapter)
        annotates = comm_meta["annotates"]
        needs_review = comm_meta["id_type"] == "unknown"

        # For MBh parvans, comment anchors are chapter.verse within the parvan;
        # prepend the book number to match the 3-level canonical passage format.
        if mbh_book and annotates and re.match(r"^\d+\.\d", annotates):
            annotates = f"{mbh_book}.{annotates}"

        if annotates is None:
            # Unknown comment anchor — fall back to document-order paragraph
            # keyed to the current chapter per LINE_ID_SCHEME §4
            ch = current_chapter or "0"
            annotates = f"c.{ch}.p{id_state.mint_seq()}"
            needs_review = True
            report_data.setdefault("comm_review", []).append(
                {"slug": slug, "anchor_id": anchor_id}
            )
        else:
            # Resolve annotates: exact → pada-stripped → host passage (Gate 5).
            # verse_passages only contains content-bearing citation_blocks, so
            # empty-content blocks (e.g. image-only) don't appear as targets.
            annotates = _resolve_annotates(annotates, verse_passages, passage)

        # Sequence is keyed to the annotated verse, not the host verse
        comm_n = id_state.mint_comm_seq(annotates)
        seq_counter[0] += 1
        records.append(_build_comm_record(
            slug, annotates, comm_inner,
            current_chapter, seq_counter[0], structure,
            comm_n, needs_review,
        ))

    return records


def parse_verse_file(
    slug: str, lines: list[str], path: str, structure: str, report_data: dict
) -> Iterator[dict]:
    """A-clean or A-range: process all lines of a verse source."""
    # Pre-scan to collect all verse passage IDs for annotates resolution
    verse_passages = _collect_verse_passages(lines, slug, path)

    current_chapter = ""
    seq_counter = [0]
    id_state = SourceIDState()

    for line in lines[1:]:  # skip title comment
        line = line.strip()
        if not line:
            continue
        if _SKIP_RE.match(line):
            continue

        # Chapter-title line
        ct_m = _CHAPTER_TITLE_RE.search(line)
        if ct_m and "citation_block" not in line:
            raw_id = ct_m.group(1)
            # Update running chapter label
            chapter_text = remove_html_tags(ct_m.group(2)).strip()
            # Determine chapter number from id for tracking
            if re.match(r"^\d+$", raw_id):
                current_chapter = raw_id
            elif re.match(r"^chapter_(\d+)", raw_id, re.IGNORECASE):
                m = re.match(r"^chapter_(\d+)", raw_id, re.IGNORECASE)
                current_chapter = m.group(1)
            continue

        # H1 header
        h1_m = _H1_RE.search(line)
        if h1_m and "citation_block" not in line:
            current_chapter = remove_html_tags(h1_m.group(1)).strip()
            continue

        # Citation block
        if "citation_block" in line:
            recs = _parse_verse_line(
                line, slug, path, current_chapter,
                seq_counter, id_state, structure, report_data,
                verse_passages,
            )
            yield from recs


def parse_dict_file(
    slug: str, lines: list[str], structure: str, report_data: dict
) -> Iterator[dict]:
    """Path B: dictionary / lexicon."""
    # Determine format: count tabs in first data line
    tab_count = 0
    for l in lines[1:]:
        l = l.strip()
        if l:
            tab_count = l.count("\t")
            break

    five_field = tab_count >= 4  # expects /deva/\t/iast/\t/slp1/\t/cyrillic/\tgloss

    seq = 0
    for raw_line in lines[1:]:  # skip title
        line = raw_line.strip()
        if not line:
            continue
        # Skip html wrappers
        if _SKIP_RE.match(line):
            continue

        seq += 1
        passage = f"e{seq}"
        record_id = f"{slug}:{passage}"

        if five_field:
            m = _DICT_5FIELD_RE.match(line)
            if m:
                deva, iast, slp1_val, cyrillic, gloss = (
                    m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
                )
                text = f"{gloss} {deva} {iast} {slp1_val} {cyrillic}".strip()
                slp1_comp = _to_slp1(iast) if iast else slp1_val
                yield {
                    "id": record_id,
                    "work": slug,
                    "passage": passage,
                    "seg": "head",
                    "group": record_id,
                    "lang": "sa",
                    "script": "devanagari",
                    "text": text,
                    "html": line,
                    "slp1": slp1_comp,
                    "structure": structure,
                    "chapter": "",
                    "forms": {
                        "deva": deva,
                        "iast": iast,
                        "slp1": slp1_val or slp1_comp,
                        "cyrillic": cyrillic,
                    },
                    "seq": seq,
                    "deleted": False,
                }
                continue

        # Non-tab formats
        # Try Kochergina: °headword /iast/ definition
        mk = _DICT_KOCHERGINA_RE.match(line)
        if mk:
            headword, iast, gloss = mk.group(1), mk.group(2), mk.group(3)
            slp1_val = _to_slp1(iast)
            script = _detect_script(headword)
            text = f"{gloss} {headword} {iast}".strip()
            yield {
                "id": record_id,
                "work": slug,
                "passage": passage,
                "seg": "head",
                "group": record_id,
                "lang": "sa",
                "script": script,
                "text": text,
                "html": line,
                "slp1": slp1_val,
                "structure": structure,
                "chapter": "",
                "forms": {"iast": iast},
                "seq": seq,
                "deleted": False,
            }
            continue

        # Try Kossovich: N headword /iast/ /iast_variant/ /cyrillic/ definition
        ms = _DICT_KOSSOVICH_RE.match(line)
        if ms:
            headword, iast, _, cyrillic, gloss = (
                ms.group(1), ms.group(2), ms.group(3), ms.group(4), ms.group(5)
            )
            slp1_val = _to_slp1(iast)
            script = _detect_script(headword)
            text = f"{gloss} {headword} {iast} {cyrillic}".strip()
            yield {
                "id": record_id,
                "work": slug,
                "passage": passage,
                "seg": "head",
                "group": record_id,
                "lang": "sa",
                "script": script,
                "text": text,
                "html": line,
                "slp1": slp1_val,
                "structure": structure,
                "chapter": "",
                "forms": {"iast": iast, "cyrillic": cyrillic},
                "seq": seq,
                "deleted": False,
            }
            continue

        # Generic fallback: extract any /iast/ fields present
        iast_fields = _DICT_GENERIC_IAST_RE.findall(line)
        iast = iast_fields[0] if iast_fields else ""
        slp1_val = _to_slp1(iast) if iast else ""
        plain_text = remove_html_tags(line)
        script = _detect_script(line)
        yield {
            "id": record_id,
            "work": slug,
            "passage": passage,
            "seg": "head",
            "group": record_id,
            "lang": "sa",
            "script": script,
            "text": plain_text,
            "html": line,
            "slp1": slp1_val,
            "structure": structure,
            "chapter": "",
            "forms": {"iast": iast} if iast else {},
            "seq": seq,
            "deleted": False,
        }


_NUMBERED_PARA_RE = re.compile(r"^(\d+)\s+(.+)$", re.DOTALL)


def parse_prose_file(
    slug: str, lines: list[str], structure: str, report_data: dict
) -> Iterator[dict]:
    """Path C: prose / article / commentary-anthology.

    Passage ID scheme (LINE_ID_SCHEME §9):
      - No chapters detected: flat p{global_seq}
      - Chapters detected: c{chapter_num}.p{local_seq}
        Local ordinal resets at each chapter heading — cross-chapter collisions
        are impossible since the c{N} prefix differs.  Note: numbered footnote
        prefixes in prose ("121 Нараяна...") are NOT used as passage IDs because
        note numbers restart within sub-sections, making them non-unique within
        a chapter boundary.
    """
    current_chapter = ""
    chapter_num = 0    # increments at each chapter heading
    chapter_seq = 0    # ordinal within current chapter (reset at each heading)
    global_seq = 0     # global ordinal (never reset)
    has_chapters = False

    def _advance_chapter(new_chapter_text: str) -> None:
        nonlocal chapter_num, chapter_seq, has_chapters, current_chapter
        current_chapter = new_chapter_text
        chapter_num += 1
        chapter_seq = 0
        has_chapters = True

    for raw_line in lines[1:]:  # skip title
        line = raw_line.strip()
        if not line:
            continue
        if _SKIP_RE.match(line):
            continue

        # H1 chapter heading (may have trailing text on same line)
        h1_m = _H1_RE.search(line)
        if h1_m:
            heading_text = remove_html_tags(h1_m.group(1)).strip()
            rest = _H1_RE.sub("", line).strip()
            if not rest or not remove_html_tags(rest).strip():
                # Pure heading — advance chapter, emit nothing
                _advance_chapter(heading_text)
                continue
            # Heading with trailing content — advance, then emit the trailing part
            _advance_chapter(heading_text)
            line = rest

        # Chapter title div (pure heading, no trailing content)
        ct_m = _CHAPTER_TITLE_RE.search(line)
        if ct_m:
            _advance_chapter(remove_html_tags(ct_m.group(2)).strip())
            continue

        global_seq += 1
        if has_chapters:
            chapter_seq += 1
            passage = f"c{chapter_num}.p{chapter_seq}"
        else:
            passage = f"p{global_seq}"

        plain_text = remove_html_tags(line)
        script = _detect_script(line)

        # Detect inline IAST within Russian prose
        if script == "cyrillic" and _IAST_DIACRIT_RE.search(plain_text):
            script = "mixed"

        yield {
            "id": f"{slug}:{passage}",
            "work": slug,
            "passage": passage,
            "seg": None,
            "group": f"{slug}:{passage}",
            "lang": "ru",
            "script": script,
            "text": plain_text,
            "html": line,
            "structure": structure,
            "chapter": current_chapter,
            "seq": global_seq,
            "deleted": False,
        }


# ---------------------------------------------------------------------------
# Per-source dispatcher
# ---------------------------------------------------------------------------

def _sniff_verse_path(lines: list[str]) -> str:
    """Return 'clean' or 'range' based on first citation_block line."""
    for line in lines[1:]:
        if "citation_block" in line:
            if _CB_HAS_ID.search(line):
                return "clean"
            return "range"
    return "range"


def convert_source(
    filename: str,
    meta: dict,
    data_dir: Path,
    output_dir: Path,
    report_data: dict,
) -> dict:
    """Convert one source file → JSONL. Returns per-source report dict."""
    slug = meta["slug"]
    structure = meta.get("structure", "prose")

    filepath = data_dir / filename
    if not filepath.exists():
        return {"slug": slug, "error": "file_not_found", "records": 0}

    try:
        with open(filepath, encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as exc:
        return {"slug": slug, "error": str(exc), "records": 0}

    # Route to parse path
    if structure == "verse":
        path = _sniff_verse_path(lines)
        records_iter = parse_verse_file(slug, lines, path, structure, report_data)
    elif structure == "dictionary":
        path = "dict"
        records_iter = parse_dict_file(slug, lines, structure, report_data)
    else:  # prose or unknown
        path = "prose"
        records_iter = parse_prose_file(slug, lines, structure, report_data)

    jsonl_path = output_dir / f"{slug}.jsonl"
    counts: dict[str, int] = {}
    total = 0
    needs_review_count = 0

    with open(jsonl_path, "w", encoding="utf-8") as out:
        for rec in records_iter:
            seg = rec.get("seg") or "body"
            counts[seg] = counts.get(seg, 0) + 1
            total += 1
            if rec.get("needs_review"):
                needs_review_count += 1
            out.write(json.dumps(rec, ensure_ascii=False))
            out.write("\n")

    return {
        "slug": slug,
        "filename": filename,
        "structure": structure,
        "path": path,
        "records": total,
        "seg_counts": counts,
        "needs_review": needs_review_count,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus-path",
        default="Index/lib/x86_64-win64",
        help="Path to the Index/lib/x86_64-win64 directory",
    )
    parser.add_argument(
        "--output-dir",
        default="web/corpus_builder/jsonl",
        help="Directory to write *.jsonl output files",
    )
    parser.add_argument(
        "--source",
        help="Convert only this slug (for testing)",
    )
    parser.add_argument(
        "--report-path",
        default="web/corpus_builder/conversion_report.json",
        help="Path for conversion report JSON",
    )
    args = parser.parse_args()

    corpus_path = Path(args.corpus_path)
    data_dir = corpus_path / "Data"
    data_txt = corpus_path / "Programdata" / "data.txt"
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not data_txt.exists():
        print(f"ERROR: {data_txt} not found", file=sys.stderr)
        sys.exit(1)

    with open(data_txt, encoding="utf-8") as f:
        filenames = [l.strip() for l in f if l.strip()]

    print(f"Found {len(filenames)} sources in data.txt")

    # Build slug → filename mapping (respects data.txt order for slug uniqueness)
    seen_slugs: set[str] = set()
    source_list: list[tuple[str, dict]] = []
    for fname in filenames:
        fp = data_dir / fname
        meta_fp = Path(str(fp) + ".meta.json")
        if meta_fp.exists():
            with open(meta_fp, encoding="utf-8") as f:
                meta = json.load(f)
        else:
            # Fallback: derive slug from filename
            slug = make_unique_slug(fname, seen_slugs)
            meta = {"slug": slug, "filename": fname, "structure": "prose"}
        slug = meta.get("slug") or make_unique_slug(fname, seen_slugs)
        seen_slugs.add(slug)
        source_list.append((fname, meta))

    report_data: dict = {}  # global mutable accumulator
    source_reports = []
    total_records = 0

    for i, (fname, meta) in enumerate(source_list):
        slug = meta.get("slug", "")
        if args.source and slug != args.source:
            continue

        print(f"[{i+1}/{len(source_list)}] {slug} ({meta.get('structure', '?')})")
        src_report = convert_source(fname, meta, data_dir, output_dir, report_data)
        source_reports.append(src_report)
        total_records += src_report.get("records", 0)
        if src_report.get("error"):
            print(f"  WARNING: {src_report['error']}", file=sys.stderr)
        else:
            print(
                f"  → {src_report['records']} records "
                f"({src_report.get('path', '?')}), "
                f"review={src_report.get('needs_review', 0)}"
            )

    report = {
        "total_sources": len(source_reports),
        "total_records": total_records,
        "sources": source_reports,
        "global_issues": report_data,
    }
    report_path = Path(args.report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(
        f"\nDone. {total_records} records across {len(source_reports)} sources."
    )
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
