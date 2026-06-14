"""Phase 3b hermetic tests: COOP/CORP security headers + static asset presence.

Validates that:
- COOP: same-origin is set on HTML responses (required for SharedArrayBuffer)
- CORP: same-origin is set on /static/wasm/* responses (required for COEP pages)
- COEP is NOT set globally (would block Google Fonts on index.html)
- search.worker.js, search-offline.js, and wasm files exist as static assets
"""
import os
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

STATIC_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "static",
)


# ── Security header tests ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_coop_header_on_root():
    """Root page (/) must carry COOP: same-origin."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.headers.get("cross-origin-opener-policy") == "same-origin", (
        "COOP header missing on /; SharedArrayBuffer will not be available in the browser"
    )


@pytest.mark.asyncio
async def test_coop_absent_on_json_responses():
    """JSON API responses must not carry COOP (middleware scoped to HTML only)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/health")
    ct = response.headers.get("content-type", "")
    assert "text/html" not in ct
    # COOP on JSON is harmless but the middleware must not blindly add it
    # to non-HTML responses; verify the content-type gate works correctly.
    if response.headers.get("cross-origin-opener-policy"):
        # Only acceptable if response is actually HTML
        assert "text/html" in ct, "COOP set on a non-HTML response"


@pytest.mark.asyncio
async def test_corp_header_on_wasm_file():
    """WASM binary at /static/wasm/sqlite3.wasm must carry CORP: same-origin."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/static/wasm/sqlite3.wasm")
    # 200 means file is present and served; 404 means file not copied yet
    if response.status_code == 404:
        pytest.skip("sqlite3.wasm not present in static/wasm/ — run scripts/fetch_wasm.sh")
    assert response.status_code == 200
    assert response.headers.get("cross-origin-resource-policy") == "same-origin", (
        "CORP header missing on sqlite3.wasm; the file will be blocked by COEP pages"
    )


@pytest.mark.asyncio
async def test_corp_header_on_wasm_mjs():
    """ES module at /static/wasm/sqlite3.mjs must carry CORP: same-origin."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/static/wasm/sqlite3.mjs")
    if response.status_code == 404:
        pytest.skip("sqlite3.mjs not present in static/wasm/")
    assert response.status_code == 200
    assert response.headers.get("cross-origin-resource-policy") == "same-origin"


@pytest.mark.asyncio
async def test_worker_script_has_corp_and_coep():
    """The search worker script must carry BOTH CORP and COEP require-corp.

    Regression guard for the Phase 3d worker-load bug: /offline-settings is
    cross-origin isolated (COEP require-corp), and a cross-origin-isolated
    document can only spawn a dedicated worker whose top-level script response
    asserts COEP require-corp (and CORP, so the isolated page may fetch it).
    Without these the worker fails to load with a detail-less error event.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/static/scripts/search.worker.js")
    if response.status_code == 404:
        pytest.skip("search.worker.js not present")
    assert response.status_code == 200
    assert response.headers.get("cross-origin-resource-policy") == "same-origin", (
        "CORP missing on the worker script — a COEP page cannot fetch it"
    )
    assert response.headers.get("cross-origin-embedder-policy") == "require-corp", (
        "COEP missing on the worker script — a cross-origin-isolated page "
        "cannot spawn it as a dedicated worker (detail-less load failure)"
    )


@pytest.mark.asyncio
async def test_no_coep_on_root():
    """COEP must NOT be set globally — it would break Google Fonts on index.html."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/")
    coep = response.headers.get("cross-origin-embedder-policy", "")
    assert coep == "", (
        f"COEP is set globally ('{coep}'); this breaks cross-origin resources. "
        "COEP must be scoped to /offline-settings only (Phase 3c)."
    )


@pytest.mark.asyncio
async def test_no_coep_on_api_endpoints():
    """API JSON responses must not carry COOP or COEP."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/corpus-version")
    assert response.status_code == 200
    # COOP/COEP on JSON responses are harmless but undesirable clutter
    assert response.headers.get("cross-origin-embedder-policy", "") == ""
    # COOP on non-HTML is allowed (middleware checks content-type) but let's confirm
    ct = response.headers.get("content-type", "")
    assert "text/html" not in ct


# ── Static asset presence ─────────────────────────────────────────────────────

def test_search_worker_js_exists():
    path = os.path.join(STATIC_DIR, "scripts", "search.worker.js")
    assert os.path.isfile(path), f"search.worker.js not found at {path}"


def test_search_offline_js_exists():
    path = os.path.join(STATIC_DIR, "scripts", "search-offline.js")
    assert os.path.isfile(path), f"search-offline.js not found at {path}"


def test_sqlite3_wasm_exists():
    path = os.path.join(STATIC_DIR, "wasm", "sqlite3.wasm")
    assert os.path.isfile(path), (
        f"sqlite3.wasm not found at {path} — run: "
        "npm pack @sqlite.org/sqlite-wasm and copy dist/sqlite3.wasm"
    )


def test_sqlite3_mjs_exists():
    path = os.path.join(STATIC_DIR, "wasm", "sqlite3.mjs")
    assert os.path.isfile(path), f"sqlite3.mjs not found at {path}"


def test_sqlite3_opfs_proxy_exists():
    path = os.path.join(STATIC_DIR, "wasm", "sqlite3-opfs-async-proxy.js")
    assert os.path.isfile(path), f"sqlite3-opfs-async-proxy.js not found at {path}"


def test_wasm_binary_minimum_size():
    """WASM binary must be at least 500 KB — a smaller file indicates a truncated copy."""
    path = os.path.join(STATIC_DIR, "wasm", "sqlite3.wasm")
    if not os.path.isfile(path):
        pytest.skip("sqlite3.wasm not present")
    size = os.path.getsize(path)
    assert size >= 500_000, f"sqlite3.wasm is only {size} bytes — expected ≥500 KB"


# ── Worker JS smoke-check (static analysis) ───────────────────────────────────

def test_worker_uses_dynamic_import():
    """search.worker.js must DYNAMICALLY import sqlite3.mjs, not statically.

    A top-level `import sqlite3InitModule from '/static/wasm/sqlite3.mjs'` makes
    the glue a load-time dependency of the worker module, which fails worker
    instantiation in this build (detail-less error). The import must be deferred
    to runtime via `await import('/static/wasm/sqlite3.mjs')` inside _init().
    """
    path = os.path.join(STATIC_DIR, "scripts", "search.worker.js")
    if not os.path.isfile(path):
        pytest.skip("search.worker.js not present")
    src = open(path, encoding="utf-8").read()
    assert "import('/static/wasm/sqlite3.mjs')" in src, (
        "search.worker.js must use a dynamic import() of sqlite3.mjs"
    )
    # Guard against a top-level static import slipping back in. Strip comment
    # lines first so the explanatory header (which quotes the bad pattern) does
    # not trip the check.
    code = "\n".join(
        ln for ln in src.splitlines()
        if not ln.lstrip().startswith("*") and not ln.lstrip().startswith("//")
    )
    assert "import sqlite3InitModule from" not in code, (
        "search.worker.js has a static top-level import — it must be dynamic"
    )


def test_worker_uses_sahpool_vfs():
    """search.worker.js must use the opfs-sahpool VFS (durable, no SAB needed),
    not the regular OpfsDb VFS which does not initialise in this build."""
    path = os.path.join(STATIC_DIR, "scripts", "search.worker.js")
    if not os.path.isfile(path):
        pytest.skip("search.worker.js not present")
    src = open(path, encoding="utf-8").read()
    assert "installOpfsSAHPoolVfs" in src
    assert "OpfsSAHPoolDb" in src


def test_worker_exports_expected_message_types():
    """search.worker.js must handle every message type the main thread sends."""
    path = os.path.join(STATIC_DIR, "scripts", "search.worker.js")
    if not os.path.isfile(path):
        pytest.skip("search.worker.js not present")
    src = open(path, encoding="utf-8").read()
    for msg_type in ("init", "importPack", "removePack", "hasPack", "openPack",
                     "closePack", "getMeta", "listSources", "query", "status"):
        assert f"'{msg_type}'" in src or f'"{msg_type}"' in src, (
            f"search.worker.js missing handler for message type '{msg_type}'"
        )


def test_offline_module_exports_public_api():
    """search-offline.js must export the required public functions."""
    path = os.path.join(STATIC_DIR, "scripts", "search-offline.js")
    if not os.path.isfile(path):
        pytest.skip("search-offline.js not present")
    src = open(path, encoding="utf-8").read()
    for fn in ("init", "isSearchAvailable", "hasPack", "openPack", "closePack",
               "packMeta", "checkVersion", "searchOffline", "installPack",
               "removePack", "status"):
        assert f"export async function {fn}" in src or f"export function {fn}" in src, (
            f"search-offline.js missing export: {fn}"
        )


@pytest.mark.asyncio
async def test_sqlite3_mjs_served_with_javascript_mime():
    """sqlite3.mjs must be served as text/javascript for ES module import in workers.

    On Windows, Python's mimetypes has no registry entry for .mjs and would
    return application/octet-stream, which Chrome rejects for module imports.
    main.py must call mimetypes.add_type('text/javascript', '.mjs') at import time.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/static/wasm/sqlite3.mjs")
    if r.status_code == 404:
        pytest.skip("sqlite3.mjs not present in static/wasm/")
    ct = r.headers.get("content-type", "")
    assert "javascript" in ct, (
        f"sqlite3.mjs served with Content-Type={ct!r}; "
        "Chrome rejects non-javascript MIME for ES module imports in workers"
    )
