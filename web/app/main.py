"""Application composition root.

What lives here and nowhere else: creating the app, wiring middleware, and
registering routers. Everything that used to make this file 611 lines was moved
out by H1927 / Lane D2, into modules named for the one job each does:

* `app.lifespan`       — startup probes, corpus checks, state-DB migrations
* `app.http_headers`   — CORS setup + the security/cache header middleware
* `app.static_assets`  — static directory resolution and the `/static` mount
* `app.routers.home`   — the site root page
* `app.routers.pwa`    — root-scoped `/sw.js`
* `app.routers.seo`    — `robots.txt` and the sitemap index + children
* `app.site_context`   — shared template context and the cross-link builder
* `app.corpus_compat`  — the one grandfathered in-place corpus.db shim

No new framework, no repository-wide layering scheme: routers register the same
way they always did, and the extracted route handlers are byte-for-byte the
originals so headers and XML output cannot drift. `test_composition_root.py`
pins that.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Imported for its side effect of registering the .mjs mimetype before any
# static file is served, as well as for STATIC_DIR / mount_static.
from app.security import install_credential_log_redaction
from app.services.regex_executor import ERROR_ENGINE_UNAVAILABLE, RegexContractError
from app.static_assets import STATIC_DIR, mount_static
from app.http_headers import configure_cors, security_headers
from app.lifespan import lifespan
from app.routers import (
    admin,
    ai,
    chronology,
    compare,
    corpus_sync,
    corrections,
    health,
    home,
    identity,
    morph,
    offline,
    offline_page,
    popular_terms,
    pwa,
    reader,
    search,
    search_page,
    seo,
    sources,
)

logger = logging.getLogger(__name__)

# H1926 C5: attach the credential-scrubbing log filter at import time, before
# the first request can be access-logged. Admin routes already refuse a
# query-string credential, but the refused request's own log line would
# otherwise preserve the very value the refusal exists to protect.
install_credential_log_redaction()

app = FastAPI(title="Samudra Manthanam API", lifespan=lifespan)


@app.exception_handler(RegexContractError)
async def regex_contract_error_handler(request: Request, exc: RegexContractError):
    """One stable payload for every refused user regex (H1926 C1/C3).

    Registered app-wide so /api/search, /api/search/stream and
    /api/search/export cannot drift into three different error shapes. 503 when
    the timeout-capable engine is missing — that is an operational fault, not
    the user's pattern; 400 for a pattern the published contract refuses.
    Neither carries engine text, offsets, or paths.
    """
    status = 503 if exc.code == ERROR_ENGINE_UNAVAILABLE else 400
    return JSONResponse(status_code=status, content=exc.as_payload())


configure_cors(app)
app.middleware("http")(security_headers)

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
app.include_router(offline.router)
app.include_router(offline_page.router)
app.include_router(chronology.router)
app.include_router(home.router)
app.include_router(pwa.router)
app.include_router(seo.router)

# Mount static files
mount_static(app)


# ──────────────────────────────────────────────────────────────────────────────
# Backwards-compatible re-exports.
#
# Several test modules and scripts import these names from `app.main` directly
# (`from app.main import app, _fetch_parallel_source_slugs`). Lane D's rule is
# that the extraction must not change behaviour, and an import path is
# behaviour, so the old names keep resolving to the moved implementations.
# ──────────────────────────────────────────────────────────────────────────────

from app.corpus_compat import (  # noqa: E402
    ensure_slug_column_and_backfill as _ensure_slug_column_and_backfill,
)
from app.lifespan import check_corpus_db as _check_corpus_db  # noqa: E402
from app.routers.home import templates  # noqa: E402
from app.routers.seo import (  # noqa: E402
    _fetch_parallel_source_ids,
    _fetch_parallel_source_slugs,
    _fetch_source_ids,
    _fetch_source_slugs,
    _get_corpus_lastmod,
    _render_sitemapindex,
    _render_urlset,
    _sitemap_base,
    _xml_response,
)
from app.site_context import ss_link as _ss_link  # noqa: E402
from app.site_context import template_context as _template_context  # noqa: E402

static_dir = STATIC_DIR

__all__ = ["app", "templates", "static_dir", "lifespan", "security_headers"]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
