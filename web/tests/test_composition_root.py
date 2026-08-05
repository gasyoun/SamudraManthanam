"""D3 acceptance — routes and headers survive the main.py extraction (H1927).

VERIFICATION D3: "Existing routes and key response headers survive the bounded
`main.py` extraction."

The probe list below is a *snapshot of the pre-extraction app's public paths*,
committed deliberately. Its job is not to describe what the app should ideally
expose — it is to fail loudly if an extraction, a router reshuffle, or a future
refactor silently drops a public path. Adding a route is expected and allowed;
the assertion is one-directional (no path may disappear).
"""

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


# Probed by request rather than by scanning `app.routes`, deliberately.
#
# An earlier draft asserted against the route table and failed only in CI, while
# tests *in this same module* fetched `/sw.js` and `/robots.txt` successfully —
# the introspected object is mutated by other modules in the session (notably
# `test_cors.py`'s `importlib.reload(app.main)`), so what it lists depends on
# execution order. The response is not order-dependent, and D3's criterion is
# that the routes *survive* the extraction: a path that answers is stronger
# evidence of that than a path that appears in a list.
PRE_EXTRACTION_PROBES = [
    ("/", (200,)),
    ("/robots.txt", (200,)),
    ("/sitemap.xml", (200,)),
    ("/sitemap-core.xml", (200,)),
    ("/sitemap-sources.xml", (200,)),
    ("/sitemap-compare.xml", (200,)),
    ("/api/health", (200,)),
    # Registered by the app; 404 only when static/sw.js is absent from a
    # checkout, which is a packaging question, not a routing one.
    ("/sw.js", (200, 404)),
]


def test_no_pre_extraction_route_disappeared(client):
    lost = []
    for path, acceptable in PRE_EXTRACTION_PROBES:
        status = client.get(path).status_code
        if status == 404 and 404 not in acceptable:
            lost.append(f"{path} -> 404")
        elif status >= 500:
            lost.append(f"{path} -> {status}")
    assert not lost, f"routes lost or broken by the extraction: {lost}"


def test_admin_route_still_registered(client):
    """The one non-GET pre-extraction route, and the smoke suite's probe target.

    Probed with a header since H1926: `?key=` is now refused as a *transport*
    (400) before the value is ever compared, so it can no longer stand in for
    "a bogus key is rejected".
    """
    status = client.post(
        "/api/admin/vacuum", headers={"X-Admin-Key": "not-a-real-key"}
    ).status_code
    assert status != 404, "/api/admin/vacuum disappeared from the app"
    assert status in (401, 403), f"a bogus admin key was not refused (got {status})"


def test_admin_route_refuses_query_string_credentials(client):
    """The transport half of the same surface (H1926 C3)."""
    status = client.post("/api/admin/vacuum?key=not-a-real-key").status_code
    assert status == 400, f"query-string credential was not refused (got {status})"


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
