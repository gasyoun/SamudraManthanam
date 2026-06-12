"""Server-rendered `/search?q=…` page.

This is the SEO surface for content queries — distinct from:
- `/`              live JS-driven search app (brand/home landing)
- `/api/search`    POST JSON API consumed by the live app
- `/api/search/export`  downloadable HTML export

The page server-renders results into the initial HTML payload so search
engines see content without executing JavaScript. Form submission is plain
GET, so the page works without JS.

Canonical URL discipline
------------------------
Multiple URLs can produce the same result set (different param order,
mixed-case query, default-valued booleans). To prevent duplicate-content
penalties we emit `<link rel="canonical">` pointing at a deterministically
normalised URL: lowercase query, sorted source ids, dropped defaults.

Indexability rules
------------------
Pages with no useful indexable content get `<meta name="robots" content="noindex,follow">`:
- single-character queries (junk)
- regex queries (don't make good landing pages, and patterns are search-noise)
- zero-result queries (crawl budget waste)
"""
import logging
import re
import time
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.db import get_db
from app.models import SearchMode
from app.services.dispatch_service import dispatch_search
from app.services.html_service import render_fragment
from app.settings import settings

router = APIRouter(tags=["search-page"])
templates = Jinja2Templates(directory="templates")
from app import corpus_info
templates.env.globals["corpus_info"] = corpus_info
logger = logging.getLogger(__name__)


_SOURCE_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


async def _resolve_source_filter(
    db, raw: Optional[str],
) -> tuple[Optional[list[int]], Optional[list[str]]]:
    """Resolve a `src=` filter of comma-separated tokens to source ids.

    Tokens are slugs (stable across re-ingests). Purely numeric tokens that
    don't match any slug are accepted as legacy source ids so pre-slug
    bookmarks keep working. Returns `(ids, slugs)` — ids feed the search,
    slugs feed the canonical URL — or `(None, None)` when the filter is
    absent or nothing resolves (treated as "all sources", matching the old
    silent-drop semantics).
    """
    if not raw:
        return None, None
    tokens = [t for t in raw.split(",") if t and _SOURCE_TOKEN_PATTERN.match(t)]
    if not tokens:
        return None, None
    resolved: dict[int, str] = {}
    placeholders = ",".join("?" * len(tokens))
    async with db.execute(
        f"SELECT id, slug FROM sources WHERE slug IN ({placeholders})", tokens
    ) as cur:
        matched_slugs = set()
        for row in await cur.fetchall():
            resolved[row[0]] = row[1]
            matched_slugs.add(row[1])
    legacy_ids = [int(t) for t in tokens if t.isdigit() and t not in matched_slugs]
    if legacy_ids:
        placeholders = ",".join("?" * len(legacy_ids))
        async with db.execute(
            f"SELECT id, slug FROM sources WHERE id IN ({placeholders})", legacy_ids
        ) as cur:
            for row in await cur.fetchall():
                resolved[row[0]] = row[1] or str(row[0])
    if not resolved:
        return None, None
    return sorted(resolved.keys()), sorted(resolved.values())


def _canonical_search_url(
    *, base: str, query: str, mode: str, case_sensitive: bool,
    whole_word: bool, source_slugs: Optional[list[str]],
) -> str:
    """Build a normalised canonical URL.

    Normalisation: lowercase + strip query, drop default-valued flags, sort
    source slugs. Empty params are omitted so equivalent searches converge
    on one URL. Slugs (not ids) keep the canonical stable across re-ingests.
    """
    parts: list[tuple[str, str]] = [("q", query.strip().lower())]
    if mode != "plain":
        parts.append(("mode", mode))
    if case_sensitive:
        parts.append(("cs", "1"))
    if whole_word:
        parts.append(("ww", "1"))
    if source_slugs:
        parts.append(("src", ",".join(sorted(source_slugs))))
    return f"{base}/search?{urlencode(parts)}"


def _should_noindex(*, query: str, mode: str, total: int) -> bool:
    """Return True when this result page should not be indexed.

    These pages are still served and useful to humans following links from
    elsewhere — they just don't earn a place in Google's index.
    """
    if mode != "plain":
        return True
    if len(query.strip()) < 2:
        return True
    if total == 0:
        return True
    return False


@router.get("/search", response_class=HTMLResponse)
async def search_page(
    request: Request,
    q: str = Query("", max_length=1000, description="Search query"),
    mode: SearchMode = Query(SearchMode.plain),
    cs: bool = Query(False, description="Case sensitive"),
    ww: bool = Query(False, description="Whole word"),
    src: Optional[str] = Query(None, description="Comma-separated source slugs (legacy: numeric IDs)"),
):
    from app.main import _ss_link, _template_context

    base = settings.PUBLIC_BASE_URL.rstrip("/") if settings.PUBLIC_BASE_URL else ""

    # Empty-query landing: show the form, no search executed, noindex.
    if not q.strip():
        return templates.TemplateResponse(
            request=request,
            name="search_page.html",
            context=_template_context(
                ss_medium="search_page",
                query="",
                mode=mode.value,
                case_sensitive=cs,
                whole_word=ww,
                source_ids_raw=src or "",
                results_fragment="",
                total=0,
                elapsed_ms=0.0,
                noindex=True,
                canonical_url=f"{base}/search",
                og_title="Поиск по санскрито-русскому корпусу — Пахтанье океана",
                og_description=settings.SITE_DESCRIPTION,
                og_url=f"{base}/search",
            ),
        )

    # Run the search through the same dispatcher used by /api/search.
    start = time.time()
    db = await get_db(settings.DB_PATH)
    try:
        source_ids, source_slugs = await _resolve_source_filter(db, src)
        search_data = await dispatch_search(
            db, q, mode, cs, ww, source_ids, limit=5000
        )
    finally:
        await db.close()
    elapsed_ms = (time.time() - start) * 1000

    results = search_data["results"]
    search_metadata = search_data["search_metadata"]
    total = len(results)
    fragment = render_fragment(q, results, search_metadata=search_metadata)

    canonical_url = _canonical_search_url(
        base=base, query=q, mode=mode.value,
        case_sensitive=cs, whole_word=ww, source_slugs=source_slugs,
    )
    noindex = _should_noindex(query=q, mode=mode.value, total=total)

    # SEO description: include the query and result count so SERP snippets are
    # actionable. The full description tail is the site default.
    if total:
        og_description = f"Найдено {total} стихов по запросу «{q.strip()}» в санскрито-русском параллельном корпусе."
    else:
        og_description = f"По запросу «{q.strip()}» ничего не найдено. {settings.SITE_DESCRIPTION}"

    return templates.TemplateResponse(
        request=request,
        name="search_page.html",
        context=_template_context(
            ss_medium="search_page",
            query=q,
            mode=mode.value,
            case_sensitive=cs,
            whole_word=ww,
            source_ids_raw=src or "",
            results_fragment=fragment,
            total=total,
            elapsed_ms=elapsed_ms,
            noindex=noindex,
            canonical_url=canonical_url,
            og_title=f"«{q.strip()}» — {total} результатов | Пахтанье океана",
            og_description=og_description,
            og_url=canonical_url,
        ),
    )
