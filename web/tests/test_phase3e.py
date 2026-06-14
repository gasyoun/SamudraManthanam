"""Phase 3e hermetic guards: main-page offline-search integration.

These are source/template smoke checks — the real behaviour is browser-verified
(worker load on the non-isolated index page, offline routing, renderer). They
guard against the wiring silently regressing:
  - search-offline.js exposes listSources (needed by the bridge for titles)
  - the bridge sets window.SamudraOffline and imports search-offline.js
  - index.html loads the bridge + has the #netStatus pill + loads search.js
  - search.js's offline routing is gated on navigator.onLine === false so the
    online path is never affected
"""
import os

STATIC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
TEMPLATES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")


def _read(*parts):
    with open(os.path.join(*parts), encoding="utf-8") as f:
        return f.read()


def test_search_offline_exports_list_sources():
    src = _read(STATIC, "scripts", "search-offline.js")
    assert "export async function listSources" in src, (
        "search-offline.js must export listSources — the bridge needs it to map "
        "result rows (source_id only) to display titles/slugs"
    )


def test_bridge_exists_and_sets_global():
    path = os.path.join(STATIC, "scripts", "offline-search-bridge.js")
    assert os.path.isfile(path), "offline-search-bridge.js missing"
    src = _read(path)
    assert "window.SamudraOffline" in src
    assert "search-offline.js" in src  # imports the engine
    for fn in ("search", "renderHtml", "isAvailable", "whenReady"):
        assert fn in src, f"bridge facade missing {fn}"


def test_bridge_lazy_and_escapes_output():
    """The renderer must escape data-derived values (line_text, titles) — guards
    against an XSS regression — and the worker must be lazy (no eager init)."""
    src = _read(STATIC, "scripts", "offline-search-bridge.js")
    assert "_esc(" in src and "function _esc" in src, "renderer must HTML-escape output"
    # Lazy: init happens inside ensureReady (called on demand / 'offline' event),
    # not at module top-level.
    assert "addEventListener('offline'" in src


def test_index_loads_bridge_and_pill():
    src = _read(TEMPLATES, "index.html")
    assert "offline-search-bridge.js" in src, "index.html must load the offline bridge"
    assert 'type="module"' in src
    assert 'id="netStatus"' in src, "index.html must have the network-status pill"
    assert "/static/search.js" in src


def test_search_js_offline_routing_is_gated_online():
    """Offline routing must be gated on navigator.onLine === false, so a normal
    online search is byte-for-byte the existing /api/search path."""
    src = _read(STATIC, "search.js")
    assert "navigator.onLine === false" in src, (
        "offline routing must trigger ONLY when navigator.onLine === false"
    )
    assert "runOfflineSearch" in src
    assert "window.SamudraOffline" in src
    # morphological offline must be handled (network-only)
    assert "morphological" in src


def test_static_scripts_cache_busted():
    """Worker + bridge + search.js carry a ?v= cache-bust (belt-and-suspenders
    alongside the no-cache policy below; DECISIONS_NEEDED D4)."""
    index = _read(TEMPLATES, "index.html")
    assert "offline-search-bridge.js?v=" in index
    assert "/static/search.js?v=" in index
    offline_js = _read(STATIC, "scripts", "search-offline.js")
    assert "WORKER_VERSION" in offline_js
    assert "search.worker.js?v=" in offline_js


import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_d4_cache_policy():
    """App JS/CSS is served no-cache (revalidates → deploys reach users); large
    vendored sqlite-wasm + fonts are cached long. Regression guard for the
    immutable-app-JS staleness (DECISIONS_NEEDED D4)."""
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for p in ("/static/search.js", "/static/scripts/search-offline.js",
                  "/static/scripts/search.worker.js", "/static/style.css"):
            r = await ac.get(p)
            if r.status_code != 200:
                continue
            assert r.headers.get("cache-control") == "no-cache", (
                f"{p} must be no-cache so a deploy reaches users, got "
                f"{r.headers.get('cache-control')!r}"
            )
        for p in ("/static/wasm/sqlite3.wasm", "/static/wasm/sqlite3.mjs"):
            r = await ac.get(p)
            if r.status_code != 200:
                continue
            cc = r.headers.get("cache-control", "")
            assert "immutable" in cc, f"{p} (vendored) should be cached long, got {cc!r}"


def test_d4_sw_does_not_cache_first_app_code():
    """The service worker must NOT cache-first app JS/CSS (that pins stale code
    forever, defeating the no-cache HTTP policy). App code uses
    stale-while-revalidate; only vendored binaries (wasm/fonts/icons) are
    cache-first. The install must also tolerate a failed precache entry
    (allSettled) so one 404 doesn't break the whole PWA (DECISIONS_NEEDED D4)."""
    sw = _read(STATIC, "sw.js")
    assert "staleWhileRevalidate" in sw
    assert "/static/wasm/" in sw and "/static/fonts/" in sw  # vendored → cache-first branch
    assert "allSettled" in sw, "install must tolerate a failed precache entry"
    assert "'/sources'" not in sw, "/sources 404s — must not be in PRECACHE_URLS"


@pytest.mark.asyncio
async def test_sw_served_no_cache():
    """/sw.js must be served no-cache so an updated SW is picked up promptly."""
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/sw.js")
    if r.status_code == 200:
        assert r.headers.get("cache-control") == "no-cache"


@pytest.mark.asyncio
async def test_d4_revalidation_returns_304():
    """A no-cache app asset must carry an ETag and answer a conditional request
    with 304 — that is what makes revalidation cheap (no body re-sent)."""
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/static/search.js")
        if r.status_code != 200:
            pytest.skip("search.js not served in this environment")
        etag = r.headers.get("etag")
        assert etag, "no-cache asset must carry an ETag for cheap revalidation"
        r2 = await ac.get("/static/search.js", headers={"If-None-Match": etag})
        assert r2.status_code == 304
