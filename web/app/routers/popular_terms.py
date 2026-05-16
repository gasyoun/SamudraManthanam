"""`GET /q/{slug}` — SEO landing pages for popular Russian-language
Sanskrit-studies queries.

Each page is a self-contained landing surface for one term:
- short definition (when curated),
- top 20 corpus examples rendered through the same fragment template as the
  main search, so cross-links (⇔ переводы) flow through automatically,
- structured data (`DefinedTerm` inside a `WebPage`),
- related-term cross-links to other `/q/{slug}` pages.

The `total` count and the "Все результаты" link route the user to
`/search?q={term}` for the full result set.

Case-insensitive slug lookup with a canonical lowercased URL — if the user
hits `/q/DHARMA` we serve the page but emit `<link rel="canonical"
href="/q/dharma">` so duplicates collapse for crawlers.
"""
import re
import time
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.db import get_db
from app.models import SearchMode
from app.popular_terms import POPULAR_TERMS, REFERENCE_WORK_FILENAMES, get_term
from app.services.dispatch_service import dispatch_search
from app.services.html_service import render_fragment
from app.settings import settings

router = APIRouter(prefix="/q", tags=["popular-terms"])
templates = Jinja2Templates(directory="templates")

_LANDING_RESULT_LIMIT = 20

# Slug must be ASCII-lowercase letters / digits / hyphens. This is enforced
# both as input validation (reject odd inputs) and as a guard against
# misconfigured registry keys.
_SLUG_PATTERN = re.compile(r"^[a-z0-9-]+$")


async def _fetch_primary_source_ids(db) -> list[int]:
    """Return source IDs that are NOT in `REFERENCE_WORK_FILENAMES`.

    Used by `/q/{slug}` to filter landing-page result sets to primary texts.
    Reference works keep working in the main search — this only affects the
    curated landing pages.
    """
    sql = "SELECT id, filename FROM sources ORDER BY sort_order"
    async with db.execute(sql) as cur:
        rows = await cur.fetchall()
    return [r["id"] for r in rows if r["filename"] not in REFERENCE_WORK_FILENAMES]


@router.get("/{slug}", response_class=HTMLResponse)
async def view_popular_term(request: Request, slug: str):
    if len(slug) > 64:
        raise HTTPException(status_code=400, detail="slug too long")
    canonical_slug = slug.lower()
    if not _SLUG_PATTERN.match(canonical_slug):
        raise HTTPException(status_code=404, detail="Unknown term")
    entry = get_term(canonical_slug)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Unknown term: {slug}")

    search_query = entry.get("search_query") or entry["term"]
    base = settings.PUBLIC_BASE_URL.rstrip("/") if settings.PUBLIC_BASE_URL else ""
    canonical_url = f"{base}/q/{canonical_slug}"

    # Run live search — fast enough for an SEO page at current corpus scale.
    # Future: cache results per (slug, corpus_version) if traffic warrants it.
    # Dictionaries / glossaries occupy top sort_order slots, so we explicitly
    # restrict to the corpus-text source set; an SEO landing page should
    # foreground concept-in-use verses, not lexicon glosses.
    start = time.time()
    db = await get_db(settings.DB_PATH)
    try:
        primary_source_ids = await _fetch_primary_source_ids(db)
        search_data = await dispatch_search(
            db, search_query, SearchMode.plain, False, False,
            source_ids=primary_source_ids, limit=_LANDING_RESULT_LIMIT,
        )
    finally:
        await db.close()
    elapsed_ms = (time.time() - start) * 1000

    results = search_data["results"]
    total = len(results)
    fragment = render_fragment(search_query, results, search_metadata=search_data.get("search_metadata"))

    # Build "Все результаты" deep-link with the proper URL encoding so Cyrillic
    # survives the GET.
    full_search_url = f"/search?q={quote(search_query, safe='')}"

    related = []
    for rel_slug in entry.get("related", []):
        rel_entry = get_term(rel_slug)
        if rel_entry:
            related.append({
                "slug": rel_slug,
                "term": rel_entry["term"],
            })

    from app.main import _ss_link, _template_context

    return templates.TemplateResponse(
        request=request,
        name="popular_term_page.html",
        context=_template_context(
            ss_medium="popular_term",
            slug=canonical_slug,
            term=entry["term"],
            iast=entry["iast"],
            devanagari=entry["devanagari"],
            definition=entry.get("definition", ""),
            related=related,
            results_fragment=fragment,
            total=total,
            elapsed_ms=elapsed_ms,
            full_search_url=full_search_url,
            canonical_url=canonical_url,
            og_title=f"{entry['term']} — что это? стихи из санскрито-русского корпуса",
            og_description=(
                entry.get("definition")
                or f"Примеры использования слова «{entry['term']}» в санскрито-русском параллельном корпусе."
            ),
            og_url=canonical_url,
        ),
    )
