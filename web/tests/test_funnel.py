"""Tests for the funnel features: sitemap, OG meta, cross-link banner.

These guard the marketing surface — broken OG tags or missing sitemap entries
silently kill organic discovery and social-link previews.
"""
from fastapi.testclient import TestClient
from app.main import app
from app.settings import settings

client = TestClient(app)


# ── Sitemap ───────────────────────────────────────────────────────────────────

def test_sitemap_includes_all_sources(test_db):
    """Every source must appear in the sitemap for SEO indexing."""
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    body = response.text
    # Conftest seeds 2 sources
    assert "/sources/1" in body
    assert "/sources/2" in body
    assert "<priority>1.0</priority>" in body  # root entry preserved


def test_sitemap_uses_public_base_url_when_set(test_db):
    old = settings.PUBLIC_BASE_URL
    settings.PUBLIC_BASE_URL = "https://example.com"
    try:
        response = client.get("/sitemap.xml")
        assert "https://example.com/sources/1" in response.text
        assert "https://example.com/</loc>" in response.text
    finally:
        settings.PUBLIC_BASE_URL = old


def test_robots_points_at_sitemap(test_db):
    old = settings.PUBLIC_BASE_URL
    settings.PUBLIC_BASE_URL = "https://example.com"
    try:
        response = client.get("/robots.txt")
        assert response.status_code == 200
        assert "Sitemap: https://example.com/sitemap.xml" in response.text
    finally:
        settings.PUBLIC_BASE_URL = old


# ── OG meta tags ──────────────────────────────────────────────────────────────

def test_index_has_og_tags(test_db):
    response = client.get("/")
    assert response.status_code == 200
    body = response.text
    assert 'property="og:title"' in body
    assert 'property="og:description"' in body
    assert 'property="og:url"' in body
    assert 'property="og:type"' in body
    assert 'name="twitter:card"' in body
    assert 'og:locale" content="ru_RU"' in body


def test_source_view_has_og_tags(test_db):
    response = client.get("/sources/1")
    assert response.status_code == 200
    body = response.text
    assert 'property="og:title"' in body
    assert 'property="og:type" content="article"' in body
    assert "Source 1" in body  # source title flows into og:title


# ── Cross-link banner ─────────────────────────────────────────────────────────

def test_cross_link_banner_hidden_when_ss_url_unset(test_db):
    old = settings.SYSTEMA_SANSCRITICUM_URL
    settings.SYSTEMA_SANSCRITICUM_URL = ""
    try:
        response = client.get("/")
        # No banner should be rendered when SS_URL is empty
        assert "Курс грамматики →" not in response.text
    finally:
        settings.SYSTEMA_SANSCRITICUM_URL = old


def test_cross_link_banner_shown_with_utm_when_ss_url_set(test_db):
    old = settings.SYSTEMA_SANSCRITICUM_URL
    settings.SYSTEMA_SANSCRITICUM_URL = "https://systema-sanscriticum.ru"
    try:
        response = client.get("/")
        body = response.text
        assert "Курс грамматики →" in body
        # UTM attribution should be baked into the link
        assert "utm_source=samudramanthanam" in body
        assert "utm_medium=navbar" in body
    finally:
        settings.SYSTEMA_SANSCRITICUM_URL = old


def test_source_view_cross_link_uses_distinct_utm_medium(test_db):
    old = settings.SYSTEMA_SANSCRITICUM_URL
    settings.SYSTEMA_SANSCRITICUM_URL = "https://systema-sanscriticum.ru"
    try:
        response = client.get("/sources/1")
        body = response.text
        # Different placement → different utm_medium so analytics can tell them apart
        assert "utm_medium=source_view" in body
    finally:
        settings.SYSTEMA_SANSCRITICUM_URL = old
