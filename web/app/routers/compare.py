"""HTTP route for /compare/{work_slug}/{ch}.{v}.

Server-rendered multi-translation comparison view. Each request resolves the
verse across every source configured in `compare_config.WORKS[work_slug]`,
including any chapter-offset bridge sources (e.g. MBh Bhīṣma-parvan for Gītā).

Validation rules:
- `work_slug` must be a configured key.
- `verse_id` must match `chapter.verse` with positive integers (no ranges in URL).
- Out-of-range chapter or missing verse → 404.
"""
import re

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.compare_config import WORKS
from app.db import get_db
from app.services.compare_service import enumerate_verses, get_comparison
from app.settings import settings

router = APIRouter(prefix="/compare", tags=["compare"])
templates = Jinja2Templates(directory="templates")

# Verse id format: `chapter.verse`, both positive integers. Ranges and decimals
# are intentionally rejected — canonical URLs are always single verses.
_VERSE_PATTERN = re.compile(r"^(\d+)\.(\d+)$")
_VERSE_ID_MAX_LEN = 16


@router.get("/{work_slug}", response_class=HTMLResponse)
async def view_work_index(request: Request, work_slug: str):
    """Per-work hub page — lists every chapter with all verse links.

    Acts as the navigation root for `/compare/{work_slug}/{ch}.{v}` leaf pages
    and as a crawlable hub for search engines. Verse counts come from the
    actual corpus (aggregated across all configured sources, with range-merged
    blocks expanded), so the index reflects what the comparison view will
    actually render.
    """
    if work_slug not in WORKS:
        raise HTTPException(status_code=404, detail=f"Unknown work: {work_slug}")
    work = WORKS[work_slug]

    db = await get_db(settings.DB_PATH)
    try:
        verses = await enumerate_verses(db, work_slug)
    finally:
        await db.close()

    # Group verses by chapter for the template
    chapters: dict[int, list[int]] = {ch: [] for ch in range(1, work["chapter_count"] + 1)}
    for ch, v in verses:
        chapters.setdefault(ch, []).append(v)

    base = settings.PUBLIC_BASE_URL.rstrip("/") if settings.PUBLIC_BASE_URL else ""
    canonical_url = f"{base}/compare/{work_slug}"

    from app.main import _ss_link

    return templates.TemplateResponse(
        request=request,
        name="compare_index.html",
        context={
            "work_slug": work_slug,
            "work_title": work["title"],
            "work_title_iast": work["title_iast"],
            "description": work["description"],
            "chapter_count": work["chapter_count"],
            "source_count": len(work["sources"]) + len(work.get("bridges", [])),
            "total_verses": len(verses),
            "chapters": chapters,
            "canonical_url": canonical_url,
            "og_title": f"{work['title']} — переводы и комментарии",
            "og_description": work["description"],
            "og_url": canonical_url,
            "site_name": "Пахтанье океана",
            "ss_link": _ss_link("compare_index"),
        },
    )


@router.get("/{work_slug}/{verse_id}", response_class=HTMLResponse)
async def view_comparison(request: Request, work_slug: str, verse_id: str):
    if len(verse_id) > _VERSE_ID_MAX_LEN:
        raise HTTPException(status_code=400, detail="verse_id too long")
    m = _VERSE_PATTERN.match(verse_id)
    if not m:
        raise HTTPException(
            status_code=400,
            detail="verse_id must be 'chapter.verse' with positive integers",
        )
    ch, v = int(m.group(1)), int(m.group(2))
    if ch < 1 or v < 1:
        raise HTTPException(status_code=400, detail="chapter and verse must be ≥ 1")

    if work_slug not in WORKS:
        raise HTTPException(status_code=404, detail=f"Unknown work: {work_slug}")

    db = await get_db(settings.DB_PATH)
    try:
        result = await get_comparison(db, work_slug, ch, v)
    finally:
        await db.close()

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No comparison data for {work_slug} {ch}.{v}",
        )

    base = settings.PUBLIC_BASE_URL.rstrip("/") if settings.PUBLIC_BASE_URL else ""
    canonical_url = f"{base}/compare/{work_slug}/{ch}.{v}"

    # Adjacent-verse links — best-effort, no DB check. The page itself 404s
    # cleanly for unknown verses, so a stale prev/next is harmless.
    prev_url = f"/compare/{work_slug}/{ch}.{v - 1}" if v > 1 else None
    next_url = f"/compare/{work_slug}/{ch}.{v + 1}"

    # Truncate plain text for og:description (search snippet preview).
    og_description_full = (result["hits"][0].line_text or "").strip()
    og_description = (og_description_full[:160] + "…") if len(og_description_full) > 160 else og_description_full
    if not og_description:
        og_description = result["description"]

    from app.main import _ss_link

    return templates.TemplateResponse(
        request=request,
        name="compare_view.html",
        context={
            **result,
            "canonical_url": canonical_url,
            "og_title": f"{result['work_title']} {ch}.{v} — переводы",
            "og_description": og_description,
            "og_url": canonical_url,
            "site_name": "Пахтанье океана",
            "ss_link": _ss_link("compare_view"),
            "prev_url": prev_url,
            "next_url": next_url,
        },
    )
