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
    source_slug: str        # stable slug (used in template URL building)
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
_EXACT_LINK_ID = re.compile(r"^(\d+)\.(\d+)$")
_IAST_BLOCK = re.compile(
    r'<div class="chapter_block iast">.*?</div>', re.DOTALL | re.IGNORECASE
)


def _build_filename_to_work() -> dict[str, tuple[str, int]]:
    """Reverse-lookup: corpus filename → (work_slug, chapter_offset_to_canonical).

    `chapter_offset_to_canonical` is the amount to ADD to the source's chapter
    number to get the canonical work's chapter. For standalone sources this is
    0; for bridge sources it's `-bridge.chapter_offset` (e.g. Bhīṣma adhyāya 23
    + (-22) = Gītā chapter 1).
    """
    idx: dict[str, tuple[str, int]] = {}
    for slug, work in WORKS.items():
        for src in work["sources"]:
            idx[src["filename"]] = (slug, 0)
        for bridge in work.get("bridges", []):
            idx[bridge["filename"]] = (slug, -bridge["chapter_offset"])
    return idx


_FILENAME_TO_WORK = _build_filename_to_work()


def compare_url_for_hit(source_filename: str, link_id: str) -> str | None:
    """Return ``/compare/{work}/{ch}.{v}`` for a search hit, or None if not eligible.

    Used by ``html_service.render_fragment`` to surface a "Сравнить переводы"
    cross-link next to each search result whose source participates in a
    comparison view.

    Handles:
    - filenames not in any work's source list → None (most of the corpus).
    - link_ids like ``chapter_1`` or empty → None.
    - range-merged link_ids (``1.5-7``) → uses the first verse in the range
      (``/compare/.../1.5``); the comparison page itself handles range fallback.
    - bridge sources (e.g. MBh Bhīṣma-parvan) → applies the inverse chapter
      offset so a hit at ``link_id="23.1"`` maps to ``/compare/bhagavadgita/1.1``,
      and silently returns None when the bridge link_id falls outside the
      canonical work's chapter range (e.g. Bhīṣma chapter 5, before the Gītā).
    """
    if not source_filename or not link_id:
        return None
    entry = _FILENAME_TO_WORK.get(source_filename)
    if entry is None:
        return None
    work_slug, ch_offset = entry

    m = _EXACT_LINK_ID.match(link_id) or _RANGE_LINK_ID.match(link_id)
    if not m:
        return None
    ch_src = int(m.group(1))
    v = int(m.group(2))

    target_ch = ch_src + ch_offset
    if target_ch < 1 or v < 1:
        return None
    if target_ch > WORKS[work_slug]["chapter_count"]:
        return None
    return f"/compare/{work_slug}/{target_ch}.{v}"


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
        SELECT cl.source_id, s.title AS source_title, s.slug AS source_slug,
               cl.link_id, cl.line_html, cl.line_text, cl.line_num
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
        SELECT cl.source_id, s.title AS source_title, s.slug AS source_slug,
               cl.link_id, cl.line_html, cl.line_text, cl.line_num
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
        source_slug=row["source_slug"] or "",
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


def _expand_link_id(link_id: str):
    """Yield every (chapter, verse) pair covered by a single link_id.

    "1.5"   → (1, 5)
    "1.3-6" → (1, 3), (1, 4), (1, 5), (1, 6)
    anything else (chapter anchors, empty, bibliographic refs) → no yield.
    """
    m = _EXACT_LINK_ID.match(link_id)
    if m:
        yield int(m.group(1)), int(m.group(2))
        return
    m = _RANGE_LINK_ID.match(link_id)
    if m:
        ch = int(m.group(1))
        first = int(m.group(2))
        last = int(m.group(3))
        if first <= last:
            for v in range(first, last + 1):
                yield ch, v


async def enumerate_verses(db, work_slug: str) -> list[tuple[int, int]]:
    """Return the sorted set of (chapter, verse) pairs for which
    `/compare/{work_slug}/{ch}.{v}` would render at least one hit.

    Used by the per-work index page and the sitemap. Aggregates across every
    source listed in `compare_config.WORKS[work_slug]`, expanding range-merged
    link_ids and applying the inverse chapter offset for bridge sources.
    Out-of-range chapters (e.g. pre-Gītā or post-Gītā Bhīṣma) are dropped.
    """
    work = WORKS.get(work_slug)
    if work is None:
        return []
    chapter_count = work["chapter_count"]
    seen: set[tuple[int, int]] = set()

    filenames = [s["filename"] for s in work["sources"]]
    if filenames:
        placeholders = ",".join("?" * len(filenames))
        sql = f"""
            SELECT DISTINCT cl.link_id
            FROM corpus_lines cl
            JOIN sources s ON cl.source_id = s.id
            WHERE s.filename IN ({placeholders}) AND cl.link_id != ''
        """
        async with db.execute(sql, filenames) as cur:
            async for row in cur:
                for ch, v in _expand_link_id(row["link_id"]):
                    if 1 <= ch <= chapter_count and v >= 1:
                        seen.add((ch, v))

    for bridge in work.get("bridges", []):
        sql_bridge = """
            SELECT DISTINCT cl.link_id
            FROM corpus_lines cl
            JOIN sources s ON cl.source_id = s.id
            WHERE s.filename = ? AND cl.link_id != ''
        """
        async with db.execute(sql_bridge, (bridge["filename"],)) as cur:
            async for row in cur:
                for ch_src, v in _expand_link_id(row["link_id"]):
                    target_ch = ch_src - bridge["chapter_offset"]
                    if 1 <= target_ch <= chapter_count and v >= 1:
                        seen.add((target_ch, v))

    return sorted(seen)


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
