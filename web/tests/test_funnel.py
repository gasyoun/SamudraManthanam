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


# ── Engaged-user CTA banner ───────────────────────────────────────────────────

def test_engaged_cta_present_when_ss_url_set(test_db):
    """The HTML for the engaged-user CTA must be in the page when SS URL is set.
    JS decides whether to actually display it based on localStorage search count."""
    old = settings.SYSTEMA_SANSCRITICUM_URL
    settings.SYSTEMA_SANSCRITICUM_URL = "https://systema-sanscriticum.ru"
    try:
        response = client.get("/")
        body = response.text
        assert 'id="engagedCta"' in body
        assert "utm_medium=engaged_banner" in body  # distinct attribution surface
        assert "Узнать →" in body
    finally:
        settings.SYSTEMA_SANSCRITICUM_URL = old


def test_engaged_cta_hidden_when_ss_url_unset(test_db):
    old = settings.SYSTEMA_SANSCRITICUM_URL
    settings.SYSTEMA_SANSCRITICUM_URL = ""
    try:
        response = client.get("/")
        # No CTA element should be rendered at all when SS_URL is empty
        assert 'id="engagedCta"' not in response.text
    finally:
        settings.SYSTEMA_SANSCRITICUM_URL = old


# ── Regression: SS_URL with existing query string must not produce ??-URLs ────

def test_ss_url_with_existing_query_string_uses_ampersand(test_db):
    """If operator sets SYSTEMA_SANSCRITICUM_URL=https://x.ru/?ref=y, the resulting
    link must be ...?ref=y&utm_source=..., not ...?ref=y?utm_source=... (broken)."""
    old = settings.SYSTEMA_SANSCRITICUM_URL
    settings.SYSTEMA_SANSCRITICUM_URL = "https://systema-sanscriticum.ru/?ref=launch"
    try:
        body = client.get("/").text
        # The malformed double-? must not appear
        assert "?ref=launch?utm_source" not in body
        # The correctly joined URL must appear (with & separating UTM)
        assert "?ref=launch&amp;utm_source=samudramanthanam" in body or \
               "?ref=launch&utm_source=samudramanthanam" in body
    finally:
        settings.SYSTEMA_SANSCRITICUM_URL = old


def test_ss_url_plain_still_uses_question_mark(test_db):
    """If SYSTEMA_SANSCRITICUM_URL has no query string, the UTM gets a leading ?."""
    old = settings.SYSTEMA_SANSCRITICUM_URL
    settings.SYSTEMA_SANSCRITICUM_URL = "https://systema-sanscriticum.ru"
    try:
        body = client.get("/").text
        assert "https://systema-sanscriticum.ru?utm_source=samudramanthanam" in body
    finally:
        settings.SYSTEMA_SANSCRITICUM_URL = old


# ── Regression: sitemap must produce valid XML when PUBLIC_BASE_URL has & ─────

def test_sitemap_xml_escapes_public_base_url(test_db):
    """A PUBLIC_BASE_URL containing & must be XML-escaped or the document is malformed."""
    import xml.etree.ElementTree as ET
    old = settings.PUBLIC_BASE_URL
    settings.PUBLIC_BASE_URL = "https://example.com/?token=a&b=c"
    try:
        response = client.get("/sitemap.xml")
        assert response.status_code == 200
        # Must parse as valid XML
        ET.fromstring(response.text)
    finally:
        settings.PUBLIC_BASE_URL = old


# ── Regression: error path must not leak internal exception text to client ────

def test_identity_lead_does_not_leak_internals_on_db_failure(test_db):
    """A failure to open state.db (e.g. path is a directory) must yield a clean 503
    with a generic message — not a 500 with the raw aiosqlite traceback."""
    import tempfile, os as _os
    old_state = settings.STATE_DB_PATH
    tmpdir = tempfile.mkdtemp()
    settings.STATE_DB_PATH = tmpdir  # a directory, not a file → aiosqlite.connect fails
    try:
        response = client.post("/api/identity/lead", json={
            "email": "boom@example.com",
            "consent_data": True,
            "consent_marketing": False,
        })
        assert response.status_code == 503
        detail = response.json()["detail"]
        # Must not contain raw exception text (paths, sqlite error names, etc.)
        assert "Identity service unavailable" == detail
    finally:
        settings.STATE_DB_PATH = old_state
        try:
            _os.rmdir(tmpdir)
        except OSError:
            pass
