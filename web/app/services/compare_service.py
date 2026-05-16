"""Comparison service: fetch the same verse across multiple corpus sources.

Caller is `app.routers.compare.view_comparison`. Rendering is the caller's
responsibility — this module returns a pure data structure.

Range-merge handling
--------------------
Some translations group several verses into one `citation_block` (link_id like
"1.3-6" covering verses 3 through 6 of chapter 1). When the user requests verse
1.5, we first try an exact link_id match per source; if that misses, we GLOB
for `1.*-*` link_ids in the same source and accept any whose range covers 5.

Bridges
-------
A "bridge" source uses a different chapter numbering than the canonical work
(e.g. Mahābhārata Bhīṣma-parvan adhyāya 23 = Bhagavadgītā chapter 1). The
config's `chapter_offset` is added to the requested chapter before lookup.
"""

import re
from dataclasses import dataclass, field
from typing import Any

from app.compare_config import WORKS


@dataclass
class VerseHit:
    source_filename: str
    source_id: int          # current numeric source id (unstable across re-ingests)
    source_title: str
    label: str              # human-readable per compare_config (e.g. "Смирнов 1977")
    role: str               # "translation" | "commentary" | "anthology" | "context"
    link_id: str            # link_id we matched on (may be a range like "1.3-6")
    line_html: str          # original HTML
    line_text: str          # plain text (used for og:description / JSON-LD)
    line_num: int
    is_range_match: bool    # True if matched via range-merge fallback
    iast_html: str = ""     # extracted Sanskrit IAST block(s), if present
    translation_html: str = ""  # line_html minus the iast block(s)


_RANGE_LINK_ID = re.compile(r"^(\d+)\.(\d+)-(\d+)$")
_IAST_BLOCK = re.compile(
    r'<div class="chapter_block iast">.*?</div>', re.DOTALL | re.IGNORECASE
)


def _link_id_covers(link_id: str, ch: int, v: int) -> bool:
    """True if link_id is exactly "ch.v" or a range "ch.first-last" covering v."""
    if link_id == f"{ch}.{v}":
        return True
    m = _RANGE_LINK_ID.match(link_id)
    if not m:
        return False
    if int(m.group(1)) != ch:
        return False
    return int(m.group(2)) <= v <= int(m.group(3))


def _split_iast_and_translation(line_html: str) -> tuple[str, str]:
    """Extract Sanskrit IAST blocks from a corpus line.

    Corpus HTML often nests `<div class="chapter_block iast">` (Sanskrit) and
    `<div class="chapter_block translation">` (Russian) inside `citation_block`.
    To avoid showing the same Sanskrit IAST 10 times on a comparison page, we
    extract IAST once and strip it from per-source HTML.

    Returns (iast_concatenated, html_without_iast). If no IAST block exists,
    returns ("", line_html).
    """
    matches = _IAST_BLOCK.findall(line_html)
    if not matches:
        return "", line_html
    stripped = _IAST_BLOCK.sub("", line_html)
    return "".join(matches), stripped


async def _fetch_verse(db, filename: str, ch: int, v: int) -> tuple[dict | None, bool]:
    """Find one row in `filename` matching link_id `ch.v` exactly,
    or a range-merge link_id whose range covers v.

    Returns (row_dict_or_None, is_range_match).
    """
    sql = """
        SELECT cl.source_id, s.title AS source_title, cl.link_id,
               cl.line_html, cl.line_text, cl.line_num
        FROM corpus_lines cl
        JOIN sources s ON cl.source_id = s.id
        WHERE s.filename = ? AND cl.link_id = ?
        LIMIT 1
    """
    async with db.execute(sql, (filename, f"{ch}.{v}")) as cur:
        row = await cur.fetchone()
        if row:
            return dict(row), False

    sql_range = """
        SELECT cl.source_id, s.title AS source_title, cl.link_id,
               cl.line_html, cl.line_text, cl.line_num
        FROM corpus_lines cl
        JOIN sources s ON cl.source_id = s.id
        WHERE s.filename = ? AND cl.link_id GLOB ?
    """
    async with db.execute(sql_range, (filename, f"{ch}.*-*")) as cur:
        async for row in cur:
            if _link_id_covers(row["link_id"], ch, v):
                return dict(row), True
    return None, False


def _make_hit(src_cfg: dict, row: dict, is_range: bool) -> VerseHit:
    iast, translation = _split_iast_and_translation(row["line_html"])
    return VerseHit(
        source_filename=src_cfg["filename"],
        source_id=row["source_id"],
        source_title=row["source_title"],
        label=src_cfg["label"],
        role=src_cfg["role"],
        link_id=row["link_id"],
        line_html=row["line_html"],
        line_text=row["line_text"],
        line_num=row["line_num"],
        is_range_match=is_range,
        iast_html=iast,
        translation_html=translation,
    )


async def get_comparison(db, work_slug: str, ch: int, v: int) -> dict[str, Any] | None:
    """Resolve a verse across all sources configured for `work_slug`.

    Returns None when the work is unknown, the chapter is out of range, or no
    source contained the verse (route should respond 404). Otherwise returns a
    template-ready dict with `hits` populated in config order.
    """
    work = WORKS.get(work_slug)
    if work is None:
        return None
    if ch < 1 or ch > work["chapter_count"]:
        return None

    hits: list[VerseHit] = []
    canonical_iast = ""  # first non-empty IAST wins for the top-of-page display

    for src_cfg in work["sources"]:
        row, is_range = await _fetch_verse(db, src_cfg["filename"], ch, v)
        if row is None:
            continue
        hit = _make_hit(src_cfg, row, is_range)
        if hit.iast_html and not canonical_iast:
            canonical_iast = hit.iast_html
        hits.append(hit)

    for bridge in work.get("bridges", []):
        target_ch = ch + bridge["chapter_offset"]
        row, is_range = await _fetch_verse(db, bridge["filename"], target_ch, v)
        if row is None:
            continue
        hit = _make_hit(bridge, row, is_range)
        if hit.iast_html and not canonical_iast:
            canonical_iast = hit.iast_html
        hits.append(hit)

    if not hits:
        return None

    return {
        "work_slug": work_slug,
        "work_title": work["title"],
        "work_title_iast": work["title_iast"],
        "description": work["description"],
        "chapter_count": work["chapter_count"],
        "chapter": ch,
        "verse": v,
        "hits": hits,
        "canonical_iast": canonical_iast,
        "translation_count": sum(1 for h in hits if h.role in ("translation", "anthology")),
        "commentary_count": sum(1 for h in hits if h.role == "commentary"),
        "context_count": sum(1 for h in hits if h.role == "context"),
    }
