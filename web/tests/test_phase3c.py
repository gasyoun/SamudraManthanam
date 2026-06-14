"""Phase 3c hermetic tests: /offline-settings page and COEP scoping."""
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_offline_settings_returns_html():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/offline-settings")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_offline_settings_has_coep():
    """COEP must be set on /offline-settings (enables SharedArrayBuffer)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/offline-settings")
    assert r.headers.get("cross-origin-embedder-policy") == "require-corp", (
        "COEP missing on /offline-settings — SharedArrayBuffer will not be available"
    )


@pytest.mark.asyncio
async def test_offline_settings_has_coop():
    """COOP must also be set (COOP + COEP together unlock SharedArrayBuffer)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/offline-settings")
    assert r.headers.get("cross-origin-opener-policy") == "same-origin"


@pytest.mark.asyncio
async def test_root_still_has_no_coep():
    """COEP must NOT appear on / — regression guard against accidental global COEP."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/")
    assert r.headers.get("cross-origin-embedder-policy", "") == "", (
        "COEP leaked onto / — would break Google Fonts and other CDN resources"
    )


@pytest.mark.asyncio
async def test_offline_settings_contains_pack_sections():
    """Page HTML must include both pack type identifiers."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/offline-settings")
    body = r.text
    assert 'data-pack="base"' in body
    assert 'data-pack="dict"' in body


@pytest.mark.asyncio
async def test_offline_settings_contains_module_imports():
    """Page must import both offline.js and search-offline.js as ES modules."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/offline-settings")
    body = r.text
    assert "/static/scripts/offline.js" in body
    assert "/static/scripts/search-offline.js" in body
    assert 'type="module"' in body


@pytest.mark.asyncio
async def test_offline_settings_navbar_back_link():
    """Page must have a back link to / (no external CDN links)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/offline-settings")
    assert 'href="/"' in r.text


@pytest.mark.asyncio
async def test_api_corpus_version_no_coep():
    """API endpoint must not carry COEP."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/api/corpus-version")
    assert r.headers.get("cross-origin-embedder-policy", "") == ""
