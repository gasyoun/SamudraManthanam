import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.routers import sources, search, morph, corpus_sync, health, reader, identity, corrections, ai, admin, compare
from app.settings import settings
from app.state_db import get_state_db, init_state_db
from app.db import get_db
import os

logger = logging.getLogger(__name__)


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

@app.get("/sitemap.xml")
async def sitemap():
    from fastapi.responses import Response
    from xml.sax.saxutils import escape as xml_escape
    from app.compare_config import WORKS
    from app.services.compare_service import enumerate_verses

    raw_base = settings.PUBLIC_BASE_URL.rstrip("/") if settings.PUBLIC_BASE_URL else ""
    base = xml_escape(raw_base)  # PUBLIC_BASE_URL is operator-controlled; & must become &amp;

    # Collect source IDs and per-work verse coordinates. Both depend on the
    # corpus DB; if it's briefly unavailable the sitemap still serves the
    # root + any successfully-fetched lists, fail-soft.
    source_ids: list[int] = []
    work_verses: dict[str, list[tuple[int, int]]] = {}
    try:
        db = await get_db(settings.DB_PATH)
        try:
            async with db.execute("SELECT id FROM sources ORDER BY sort_order") as cursor:
                source_ids = [row[0] for row in await cursor.fetchall()]
            for work_slug in WORKS:
                try:
                    work_verses[work_slug] = await enumerate_verses(db, work_slug)
                except Exception:
                    work_verses[work_slug] = []
        finally:
            await db.close()
    except Exception:
        source_ids = []

    urls = [f"  <url><loc>{base}/</loc><priority>1.0</priority></url>"]
    for sid in source_ids:
        urls.append(f"  <url><loc>{base}/sources/{sid}</loc><priority>0.8</priority></url>")
    # Per-work index hub pages (priority 0.9 — high-value SEO landing pages)
    for work_slug in WORKS:
        urls.append(f"  <url><loc>{base}/compare/{work_slug}</loc><priority>0.9</priority></url>")
    # Leaf comparison URLs (priority 0.7 — many of them, each unique on RuNet)
    for work_slug, verses in work_verses.items():
        for ch, v in verses:
            urls.append(f"  <url><loc>{base}/compare/{work_slug}/{ch}.{v}</loc><priority>0.7</priority></url>")

    content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )
    return Response(content=content, media_type="application/xml")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
