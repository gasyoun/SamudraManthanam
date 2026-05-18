import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.routers import sources, search, morph, corpus_sync, health, reader, identity, corrections, ai, admin, compare, search_page, popular_terms
from app.settings import settings
from app.state_db import get_state_db, init_state_db
from app.db import get_db
import os

logger = logging.getLogger(__name__)


async def _ensure_slug_column_and_backfill(db) -> None:
    """Migrate corpus.db to the slug-routing era.

    Two idempotent steps so an operator can roll back and forward without
    losing data:

    1. Add the `slug` column if missing (ALTER TABLE; no-op when already
       present — PRAGMA table_info gates it).
    2. Backfill `slug` for every row where it's NULL or empty. Slugs are
       derived from filename via `derive_slug` with `make_unique_slug`
       collision resolution against the set of slugs already populated.

    Runs at lifespan startup so any pre-migration corpus.db transparently
    gains slug routing without operator action.
    """
    try:
        async with db.execute("PRAGMA table_info(sources)") as cur:
            columns = {row[1] for row in await cur.fetchall()}
        if "slug" not in columns:
            await db.execute("ALTER TABLE sources ADD COLUMN slug TEXT")
            await db.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_sources_slug "
                "ON sources(slug) WHERE slug IS NOT NULL AND slug != ''"
            )
            await db.commit()
            logger.info("lifespan: added sources.slug column")
    except Exception:
        logger.exception("lifespan: failed to add sources.slug column")
        return

    # Backfill any unset slugs. Idempotent.
    try:
        async with db.execute(
            "SELECT id, filename FROM sources "
            "WHERE slug IS NULL OR slug = '' ORDER BY id"
        ) as cur:
            missing = await cur.fetchall()
        if not missing:
            return

        # Existing slugs (from prior runs or partial migrations).
        async with db.execute(
            "SELECT slug FROM sources WHERE slug IS NOT NULL AND slug != ''"
        ) as cur:
            existing = {row[0] for row in await cur.fetchall()}

        from app.services.slug import make_unique_slug
        for row in missing:
            slug = make_unique_slug(row[1], existing)
            existing.add(slug)
            await db.execute("UPDATE sources SET slug = ? WHERE id = ?", (slug, row[0]))
        await db.commit()
        logger.info("lifespan: backfilled slugs for %d source(s)", len(missing))
    except Exception:
        logger.exception(
            "lifespan: slug backfill failed; /sources/{slug} routes may 404 "
            "for un-migrated rows until next startup or re-ingest"
        )


async def _check_corpus_db() -> None:
    """Log a clear warning at startup if corpus.db is missing or has no sources.

    `aiosqlite.connect` will silently CREATE an empty SQLite file at the path
    if it doesn't exist, so missing-corpus shows up downstream as "no results"
    instead of a startup error. This one-shot probe surfaces the misconfig to
    operators via logs without crashing the app.
    """
    if not os.path.exists(settings.DB_PATH):
        logger.warning(
            "lifespan: corpus DB does not exist at DB_PATH=%s — aiosqlite will "
            "create an empty file on first access; the app will serve zero "
            "search results until the corpus is ingested.", settings.DB_PATH
        )
        return
    try:
        db = await get_db(settings.DB_PATH)
        try:
            async with db.execute("SELECT COUNT(*) FROM sources") as cursor:
                row = await cursor.fetchone()
                count = row[0] if row else 0
            if count == 0:
                logger.warning(
                    "lifespan: corpus DB at %s has zero sources — search will "
                    "return no results until an ingest completes.", settings.DB_PATH
                )
            else:
                logger.info("lifespan: corpus DB OK — %d sources loaded.", count)
            # Slug routing migration. Idempotent; runs every startup so a
            # pre-migration corpus.db gains slug URLs without operator action.
            await _ensure_slug_column_and_backfill(db)
        finally:
            await db.close()
    except Exception:
        logger.exception(
            "lifespan: corpus DB probe failed at DB_PATH=%s — search routes will "
            "return 500 until the corpus is fixed.", settings.DB_PATH
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks. A failed state.db init must NOT crash the whole app —
    the corpus search should keep working in degraded mode while the operator
    fixes the state DB. State-dependent routes will surface clean 503s."""
    await _check_corpus_db()
    if settings.STATE_DB_PATH:
        db = None
        try:
            db = await get_state_db()
            if db is not None:
                await init_state_db(db)
        except Exception:
            logger.exception(
                "lifespan: state DB init failed; identity/corrections/AI cache "
                "endpoints will return 503 until the operator fixes STATE_DB_PATH"
            )
        finally:
            if db is not None:
                try:
                    await db.close()
                except Exception:
                    logger.exception("lifespan: failed to close state DB after init")
    yield

app = FastAPI(title="Samudra Manthanam API", lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

# Configure CORS. Wildcard "*" is ONLY used in development with no explicit list —
# production with an unset ALLOWED_ORIGINS results in `[]` (no cross-origin requests
# permitted), which fails closed instead of fails open.
origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
if not origins and settings.APP_ENV == "development":
    origins = ["*"]

allow_credentials = origins != ["*"] and bool(origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sources.router)
app.include_router(search.router)
app.include_router(morph.router)
app.include_router(corpus_sync.router)
app.include_router(health.router)
app.include_router(reader.router)
app.include_router(identity.router)
app.include_router(corrections.router)
app.include_router(ai.router)
app.include_router(admin.router)
app.include_router(compare.router)
app.include_router(search_page.router)
app.include_router(popular_terms.router)

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

def _ss_link(medium: str) -> str:
    """Build a UTM-tagged link to Systema Sanscriticum.
    Handles the case where SYSTEMA_SANSCRITICUM_URL already contains a query string."""
    from urllib.parse import urlencode, urlparse
    base = settings.SYSTEMA_SANSCRITICUM_URL
    if not base:
        return ""
    qs = urlencode({
        "utm_source": "samudramanthanam",
        "utm_medium": medium,
        "utm_campaign": "cross_link",
    })
    sep = "&" if urlparse(base).query else "?"
    return f"{base}{sep}{qs}"


def _template_context(*, ss_medium: str = "", **extra) -> dict:
    """Common template context — site metadata + cross-link target."""
    base = {
        "site_name": "Пахтанье океана",
        "site_description": settings.SITE_DESCRIPTION,
        "public_base_url": settings.PUBLIC_BASE_URL,
        "ss_url": settings.SYSTEMA_SANSCRITICUM_URL,  # presence-check only
        "ss_link": _ss_link(ss_medium) if ss_medium else "",
    }
    base.update(extra)
    return base


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=_template_context(
            ss_medium="navbar",
            engaged_ss_link=_ss_link("engaged_banner"),
            og_title="Пахтанье океана — поиск по санскрито-русскому корпусу",
            og_description=settings.SITE_DESCRIPTION,
            og_url=settings.PUBLIC_BASE_URL or "/",
        ),
    )

@app.get("/robots.txt")
async def robots():
    sitemap_url = (settings.PUBLIC_BASE_URL.rstrip("/") + "/sitemap.xml") if settings.PUBLIC_BASE_URL else "/sitemap.xml"
    content = f"User-agent: *\nDisallow: /api/\nAllow: /\nSitemap: {sitemap_url}\n"
    from fastapi.responses import Response
    return Response(content=content, media_type="text/plain")

async def _get_corpus_lastmod(db) -> str:
    """Return the corpus-build date in `YYYY-MM-DD` form for `<lastmod>`,
    or an empty string when `corpus_meta.generated_at` is missing/unparseable.

    `generated_at` is written by `ingest.ingest` as a full ISO timestamp
    (`2026-05-17T12:34:56.789012`); the sitemap only needs the date prefix.
    Date-only is W3C-DTF compliant and sufficient for crawl-freshness
    signalling — Google honours daily granularity for `<lastmod>`.
    """
    try:
        async with db.execute(
            "SELECT value FROM corpus_meta WHERE key = 'generated_at'"
        ) as cursor:
            row = await cursor.fetchone()
        if not row or not row[0]:
            return ""
        # The DB stores ISO 8601; sitemaps spec accepts YYYY-MM-DD. Take
        # the first 10 chars — robust to either '2026-05-17' or full
        # `2026-05-17T12:34:56.789012`.
        candidate = str(row[0])[:10]
        # Sanity-check the shape so a malformed value doesn't make every
        # `<lastmod>` invalid; Google will reject the whole sitemap on
        # malformed dates.
        if len(candidate) == 10 and candidate[4] == "-" and candidate[7] == "-":
            return candidate
        return ""
    except Exception:
        return ""


def _xml_response(content: str):
    """Wrap an XML string in a Response with the correct media type."""
    from fastapi.responses import Response
    return Response(content=content, media_type="application/xml")


def _render_urlset(url_entries: list[str], *, include_xhtml: bool = False) -> str:
    """Wrap a list of `<url>…</url>` strings in a sitemap urlset envelope.

    `include_xhtml=True` declares the xhtml namespace on the urlset element,
    which is required when any `<url>` entry inside contains `<xhtml:link>`
    hreflang alternates (Google's preferred sitemap-level multilingual signal).
    """
    xhtml_attr = ' xmlns:xhtml="http://www.w3.org/1999/xhtml"' if include_xhtml else ""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"{xhtml_attr}>\n'
        + "\n".join(url_entries)
        + "\n</urlset>\n"
    )


def _render_sitemapindex(sitemap_entries: list[str]) -> str:
    """Wrap a list of `<sitemap>…</sitemap>` strings in a sitemapindex envelope."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(sitemap_entries)
        + "\n</sitemapindex>\n"
    )


def _sitemap_base() -> str:
    """XML-escaped `PUBLIC_BASE_URL` (operator-controlled; & must become &amp;)."""
    from xml.sax.saxutils import escape as xml_escape
    raw_base = settings.PUBLIC_BASE_URL.rstrip("/") if settings.PUBLIC_BASE_URL else ""
    return xml_escape(raw_base)


async def _fetch_source_ids(db) -> list[int]:
    """Legacy: returns numeric IDs. Retained for tests; new code should use
    `_fetch_source_slugs` so the sitemap emits stable URLs."""
    async with db.execute("SELECT id FROM sources ORDER BY sort_order") as cursor:
        return [row[0] for row in await cursor.fetchall()]


async def _fetch_source_slugs(db) -> list[str]:
    """Return slugs of every source in `sort_order`. Skips rows where the
    slug is NULL or empty (shouldn't happen post-migration, but defensive)."""
    async with db.execute(
        "SELECT slug FROM sources WHERE slug IS NOT NULL AND slug != '' "
        "ORDER BY sort_order"
    ) as cursor:
        return [row[0] for row in await cursor.fetchall()]


async def _fetch_parallel_source_slugs(db) -> set[str]:
    """Return slugs of sources whose corpus_lines carry the `chapter_block
    iast` marker — i.e. parallel-content sources that earn hreflang
    alternates in the sitemap.
    """
    try:
        sql = """
            SELECT s.slug FROM sources s
            WHERE s.slug IS NOT NULL AND s.slug != ''
              AND EXISTS (
                SELECT 1 FROM corpus_lines cl
                WHERE cl.source_id = s.id
                  AND cl.line_html LIKE '%chapter_block iast%'
                LIMIT 1
              )
        """
        async with db.execute(sql) as cursor:
            return {row[0] for row in await cursor.fetchall()}
    except Exception:
        return set()


async def _fetch_parallel_source_ids(db) -> set[int]:
    """Return the set of source IDs whose corpus_lines contain at least one
    `chapter_block iast` marker — i.e. sources that have parallel Sanskrit +
    Russian content and therefore deserve hreflang alternates in the sitemap.

    Single SQL pass with EXISTS + LIMIT 1 short-circuit, so per-source work
    stops at the first qualifying line. On the live ~120k-line corpus this
    runs in well under a second; not worth pre-computing a column for now.
    Fails soft to an empty set so the sitemap still serves on errors.
    """
    try:
        sql = """
            SELECT s.id FROM sources s
            WHERE EXISTS (
                SELECT 1 FROM corpus_lines cl
                WHERE cl.source_id = s.id
                  AND cl.line_html LIKE '%chapter_block iast%'
                LIMIT 1
            )
        """
        async with db.execute(sql) as cursor:
            return {row[0] for row in await cursor.fetchall()}
    except Exception:
        return set()


# ──────────────────────────────────────────────────────────────────────────────
# Sitemap index + three child sitemaps.
#
# Why split: the previous flat sitemap reached 1,420 URLs and ~145 KB. Splitting
# into core (~34) / sources (~148) / compare-leaves (~1,238) gives crawlers
# clearer prioritisation signals and keeps the high-value hub pages off the same
# document as the long-tail verse URLs. The robots.txt `Sitemap: /sitemap.xml`
# directive still points at the index — Google transparently follows children.
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/sitemap.xml")
async def sitemap_index():
    """Sitemap index pointing to the three child sitemaps."""
    base = _sitemap_base()
    lastmod = ""
    try:
        db = await get_db(settings.DB_PATH)
        try:
            lastmod = await _get_corpus_lastmod(db)
        finally:
            await db.close()
    except Exception:
        lastmod = ""

    lm = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
    entries = [
        f"  <sitemap><loc>{base}/sitemap-core.xml</loc>{lm}</sitemap>",
        f"  <sitemap><loc>{base}/sitemap-sources.xml</loc>{lm}</sitemap>",
        f"  <sitemap><loc>{base}/sitemap-compare.xml</loc>{lm}</sitemap>",
    ]
    return _xml_response(_render_sitemapindex(entries))


@app.get("/sitemap-core.xml")
async def sitemap_core():
    """High-value hub pages: root + 3 work hubs + 30 popular-query landings."""
    from app.compare_config import WORKS
    from app.popular_terms import POPULAR_TERMS

    base = _sitemap_base()
    lastmod = ""
    try:
        db = await get_db(settings.DB_PATH)
        try:
            lastmod = await _get_corpus_lastmod(db)
        finally:
            await db.close()
    except Exception:
        lastmod = ""

    lm = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
    urls = [f"  <url><loc>{base}/</loc>{lm}<priority>1.0</priority></url>"]
    for work_slug in WORKS:
        urls.append(f"  <url><loc>{base}/compare/{work_slug}</loc>{lm}<priority>0.9</priority></url>")
    for slug in POPULAR_TERMS:
        urls.append(f"  <url><loc>{base}/q/{slug}</loc>{lm}<priority>0.9</priority></url>")
    return _xml_response(_render_urlset(urls))


@app.get("/sitemap-sources.xml")
async def sitemap_sources():
    """One entry per `/sources/{slug}` for non-parallel sources, three entries
    (bare + `?lang=ru` + `?lang=sa`) for parallel sources. Each parallel
    entry carries the full `<xhtml:link>` hreflang alternate set, which is
    Google's preferred sitemap-level signal for multilingual content.
    Slug URLs (not numeric IDs) so the sitemap survives re-ingest renumbering.
    """
    from urllib.parse import quote

    base = _sitemap_base()
    slugs: list[str] = []
    parallel_slugs: set[str] = set()
    lastmod = ""
    try:
        db = await get_db(settings.DB_PATH)
        try:
            slugs = await _fetch_source_slugs(db)
            parallel_slugs = await _fetch_parallel_source_slugs(db)
            lastmod = await _get_corpus_lastmod(db)
        finally:
            await db.close()
    except Exception:
        slugs = []

    lm = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
    urls: list[str] = []
    for slug in slugs:
        # Cyrillic-derived slugs are already ASCII via transliteration, but
        # underscores etc. are URL-safe so `quote` is mostly a no-op here.
        encoded = quote(slug, safe="-_")
        source_url = f"{base}/sources/{encoded}"
        if slug in parallel_slugs:
            # Per Google: each language variant gets its own <url> entry,
            # and each entry repeats the full alternate set (including a
            # self-reference). The bare URL is the x-default.
            alternates = (
                f'<xhtml:link rel="alternate" hreflang="x-default" href="{source_url}"/>'
                f'<xhtml:link rel="alternate" hreflang="ru" href="{source_url}?lang=ru"/>'
                f'<xhtml:link rel="alternate" hreflang="sa" href="{source_url}?lang=sa"/>'
            )
            for variant_url in (source_url, f"{source_url}?lang=ru", f"{source_url}?lang=sa"):
                urls.append(
                    f"  <url><loc>{variant_url}</loc>{lm}<priority>0.8</priority>{alternates}</url>"
                )
        else:
            urls.append(
                f"  <url><loc>{source_url}</loc>{lm}<priority>0.8</priority></url>"
            )

    return _xml_response(_render_urlset(urls, include_xhtml=bool(parallel_slugs)))


@app.get("/sitemap-compare.xml")
async def sitemap_compare():
    """Leaf comparison URLs (~1,238 on the live corpus). Each verse where a
    `/compare/{work}/{ch}.{v}` page would surface at least one hit."""
    from app.compare_config import WORKS
    from app.services.compare_service import enumerate_verses

    base = _sitemap_base()
    work_verses: dict[str, list[tuple[int, int]]] = {}
    lastmod = ""
    try:
        db = await get_db(settings.DB_PATH)
        try:
            for work_slug in WORKS:
                try:
                    work_verses[work_slug] = await enumerate_verses(db, work_slug)
                except Exception:
                    work_verses[work_slug] = []
            lastmod = await _get_corpus_lastmod(db)
        finally:
            await db.close()
    except Exception:
        pass

    lm = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
    urls = [
        f"  <url><loc>{base}/compare/{work_slug}/{ch}.{v}</loc>{lm}<priority>0.7</priority></url>"
        for work_slug, verses in work_verses.items()
        for ch, v in verses
    ]
    return _xml_response(_render_urlset(urls))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
