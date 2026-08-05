"""CORS configuration and the security/cache header middleware.

Extracted from `app.main` by H1927 / Lane D2. The header logic is byte-for-byte
the original — Lane D's acceptance criterion D3 is precisely that these headers
survive the extraction, so the long comment explaining *why* each one is set
travels with the code rather than being summarised away.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.settings import settings


def cors_origins() -> list[str]:
    """Resolve the allowed-origin list.

    Wildcard "*" is ONLY used in development with no explicit list — production
    with an unset ALLOWED_ORIGINS results in `[]` (no cross-origin requests
    permitted), which fails closed instead of fails open.
    """
    origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
    if not origins and settings.APP_ENV == "development":
        origins = ["*"]
    return origins


def configure_cors(app: FastAPI) -> None:
    origins = cors_origins()
    allow_credentials = origins != ["*"] and bool(origins)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )


async def security_headers(request: Request, call_next):
    """Add cross-origin headers so the /offline-settings page can spawn the
    sqlite-wasm search worker.

    COOP: same-origin — set on all HTML pages.  Combined with COEP on
    /offline-settings it makes that page cross-origin isolated.  Safe globally:
    it only restricts what other origins can open/reference this window as; it
    does not affect resource loading.  (Note: the durable VFS we use,
    opfs-sahpool, does NOT itself require isolation/SharedArrayBuffer — see
    docs/OFFLINE_SEARCH_DESIGN.md §12.1.  Whether COEP is removable entirely is
    tracked in docs/DECISIONS_NEEDED.md.)

    CORP + COEP (require-corp): set on ALL /static/* responses.  /offline-settings
    is cross-origin isolated, and a cross-origin-isolated document can only spawn
    a dedicated worker whose OWN top-level script response carries COEP
    require-corp (and CORP, so the page may fetch it).  The worker script, the
    wasm glue + binary, and woff2 fonts are all under /static, so both headers go
    there.  All /static assets are first-party (CORP same-origin only blocks
    OTHER origins from embedding them).  COEP on a response is IGNORED for
    ordinary <script>/CSS/font/img loads, so this does not affect index.html
    (which is NOT cross-origin isolated — the middleware sets only COOP on HTML,
    never COEP, so its cross-origin Google Fonts keep loading).
    """
    response = await call_next(request)
    ct = response.headers.get("content-type", "")
    path = request.url.path

    if "text/html" in ct:
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"

    if path.startswith("/static/"):
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        # The /offline-settings page is cross-origin isolated (COEP require-corp).
        # When such a document spawns a dedicated worker, the worker's OWN
        # top-level script response must also carry COEP require-corp to join the
        # isolated agent cluster — without it the worker fails to load with a
        # detail-less error event.  COEP on a response is ignored for ordinary
        # <script>/CSS/font/img loads, so this is harmless for index.html (which
        # is NOT cross-origin isolated and does not enforce COEP on subresources).
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"

        # Cache policy (DECISIONS_NEEDED D4). App code (JS/CSS) is served
        # no-cache so the browser revalidates and a deploy/edit reaches users
        # immediately (a conditional request → 304 when unchanged, fresh on
        # change — cheap). Large vendored binaries (wasm/fonts) change ~never
        # and are cached long. Without this, browsers heuristic-cache app JS and
        # serve stale code (which masqueraded as logic bugs repeatedly). This
        # mirrors the nginx /static caching used in production, which bypasses
        # this middleware. Don't clobber Cache-Control if a route already set one.
        # /static/wasm/* is entirely vendored sqlite-wasm (incl. the large
        # sqlite3.mjs) and fonts change ~never → cache 1 year. Everything else
        # (app JS/CSS under /static/scripts, /static/*.js, etc.) → no-cache.
        if "cache-control" not in response.headers:
            if path.startswith("/static/wasm/") or path.endswith((".woff2", ".woff", ".ttf")):
                response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            elif path.endswith((".js", ".mjs", ".css")):
                response.headers["Cache-Control"] = "no-cache"

    return response
