"""D3 acceptance — routes and headers survive the main.py extraction (H1927).

VERIFICATION D3: "Existing routes and key response headers survive the bounded
`main.py` extraction."

The route inventory below is a *snapshot taken from the pre-extraction app* and
committed deliberately. Its job is not to describe what the app should ideally
expose — it is to fail loudly if an extraction, a router reshuffle, or a future
refactor silently drops or renames a public path. Adding a route is expected and
allowed; the assertion is one-directional (no path may disappear).
"""

import importlib

import pytest
from fastapi.testclient import TestClient


def current_app():
    """Read `app.main.app` at call time, never as a module-level snapshot.

    `tests/test_cors.py` calls `importlib.reload(app.main)`, which rebinds
    `app.main.app` to a brand-new FastAPI instance. Anything holding the object
    captured at import time is then asserting about an app the process no longer
    serves — and whether that matters depends on test execution order, which is
    exactly the kind of dependency that passes locally and fails in CI.
    """
    import app.main

    return app.main.app


# Captured from origin/main @ be9a303 before the Lane D2 extraction.
PRE_EXTRACTION_PATHS = {
    "/",
    "/robots.txt",
    "/sw.js",
    "/sitemap.xml",
    "/sitemap-core.xml",
    "/sitemap-sources.xml",
    "/sitemap-compare.xml",
    "/api/health",
    "/static",
}


def _paths() -> set[str]:
    return {getattr(r, "path", "") for r in current_app().routes}


def test_no_pre_extraction_route_disappeared():
    present = _paths()
    missing = PRE_EXTRACTION_PATHS - present
    assert not missing, (
        f"routes lost in extraction: {sorted(missing)}. "
        f"App currently registers: {sorted(present)}"
    )


def test_route_names_are_stable():
    """Route *names* are part of the contract too — url_for() uses them."""
    by_name = {getattr(r, "name", None) for r in current_app().routes}
    for name in (
        "root",
        "robots",
        "service_worker",
        "sitemap_index",
        "sitemap_core",
        "sitemap_sources",
        "sitemap_compare",
        "static",
    ):
        assert name in by_name, f"route name '{name}' lost in extraction"


def test_main_still_exports_the_names_tests_import():
    """Import paths are behaviour. These are imported from app.main elsewhere."""
    import app.main as main

    for attr in (
        "app",
        "templates",
        "static_dir",
        "lifespan",
        "security_headers",
        "_ss_link",
        "_template_context",
        "_get_corpus_lastmod",
        "_fetch_source_ids",
        "_fetch_source_slugs",
        "_fetch_parallel_source_ids",
        "_fetch_parallel_source_slugs",
        "_render_urlset",
        "_render_sitemapindex",
        "_sitemap_base",
        "_xml_response",
        "_check_corpus_db",
        "_ensure_slug_column_and_backfill",
    ):
        assert hasattr(main, attr), f"app.main no longer exports {attr}"


def test_main_stays_bounded():
    """The point of D2 was a composition root, not a 611-line module.

    A generous ceiling — this is a regression guard against re-accretion, not a
    style rule. If a genuinely new router needs registering, that costs a line.
    """
    from pathlib import Path

    main_py = Path(__file__).resolve().parents[1] / "app" / "main.py"
    lines = main_py.read_text(encoding="utf-8").splitlines()
    code = [ln for ln in lines if ln.strip() and not ln.strip().startswith("#")]
    assert len(code) < 160, f"app/main.py is re-accreting logic ({len(code)} code lines)"


# ---------------------------------------------------------------------------
# Header contract — these are the headers the offline sqlite-wasm page needs.
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    return TestClient(current_app())


def test_html_pages_carry_coop(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.headers.get("Cross-Origin-Opener-Policy") == "same-origin"


def test_html_pages_do_not_carry_coep(client):
    """index.html must NOT be cross-origin isolated — its Google Fonts would break."""
    resp = client.get("/")
    assert "Cross-Origin-Embedder-Policy" not in resp.headers


def test_service_worker_is_root_scoped(client):
    resp = client.get("/sw.js")
    if resp.status_code == 404:
        pytest.skip("static/sw.js not present in this checkout")
    assert resp.headers.get("Service-Worker-Allowed") == "/"
    assert resp.headers.get("Cache-Control") == "no-cache"


def test_robots_points_at_the_sitemap(client):
    resp = client.get("/robots.txt")
    assert resp.status_code == 200
    assert "Sitemap:" in resp.text
    assert "Disallow: /api/" in resp.text
