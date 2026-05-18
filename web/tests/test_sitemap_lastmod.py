"""Tests for `<lastmod>` emission on /sitemap.xml entries.

Lastmod is sourced from `corpus_meta.generated_at` (written by ingest.ingest).
Tests cover both populated and missing/malformed states because the lifespan
warning is the only signal an operator gets that corpus_meta is unhealthy —
the sitemap must still serve.
"""
import re
import xml.etree.ElementTree as ET

import aiosqlite
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.main import app, _get_corpus_lastmod
from app.settings import settings

client = TestClient(app)


# ── _get_corpus_lastmod (the parser) ────────────────────────────────────────

@pytest_asyncio.fixture
async def with_generated_at():
    """Insert a populated corpus_meta.generated_at then clean up."""
    db = await aiosqlite.connect(settings.DB_PATH)
    await db.execute(
        "INSERT OR REPLACE INTO corpus_meta (key, value) "
        "VALUES ('generated_at', '2026-05-17T12:34:56.789012')"
    )
    await db.commit()
    await db.close()
    yield "2026-05-17"
    db = await aiosqlite.connect(settings.DB_PATH)
    await db.execute("DELETE FROM corpus_meta WHERE key = 'generated_at'")
    await db.commit()
    await db.close()


@pytest_asyncio.fixture
async def with_malformed_generated_at():
    db = await aiosqlite.connect(settings.DB_PATH)
    await db.execute(
        "INSERT OR REPLACE INTO corpus_meta (key, value) "
        "VALUES ('generated_at', 'not-a-real-date')"
    )
    await db.commit()
    await db.close()
    yield
    db = await aiosqlite.connect(settings.DB_PATH)
    await db.execute("DELETE FROM corpus_meta WHERE key = 'generated_at'")
    await db.commit()
    await db.close()


@pytest.mark.asyncio
async def test_get_corpus_lastmod_extracts_date_from_iso_timestamp(with_generated_at):
    expected = with_generated_at  # "2026-05-17"
    db = await aiosqlite.connect(settings.DB_PATH)
    try:
        result = await _get_corpus_lastmod(db)
    finally:
        await db.close()
    assert result == expected


@pytest.mark.asyncio
async def test_get_corpus_lastmod_returns_empty_when_meta_missing():
    # No fixture — corpus_meta has no generated_at row.
    db = await aiosqlite.connect(settings.DB_PATH)
    try:
        result = await _get_corpus_lastmod(db)
    finally:
        await db.close()
    assert result == ""


@pytest.mark.asyncio
async def test_get_corpus_lastmod_rejects_malformed_value(with_malformed_generated_at):
    # A bad date string in corpus_meta must NOT propagate into <lastmod> —
    # Google rejects the whole sitemap on a single malformed date.
    db = await aiosqlite.connect(settings.DB_PATH)
    try:
        result = await _get_corpus_lastmod(db)
    finally:
        await db.close()
    assert result == ""


# ── HTTP-level: /sitemap.xml output (now a sitemap index) ───────────────────

# After the v1.15.6 split, /sitemap.xml is a sitemapindex referencing three
# child sitemaps. The index itself carries <lastmod> on each <sitemap> entry;
# every child sitemap carries <lastmod> on each <url>.

_CHILD_SITEMAPS = ("/sitemap-core.xml", "/sitemap-sources.xml", "/sitemap-compare.xml")


def test_sitemap_index_is_a_sitemapindex_not_a_urlset():
    r = client.get("/sitemap.xml")
    assert r.status_code == 200
    body = r.text
    assert "<sitemapindex" in body
    assert "<urlset" not in body
    # All three children referenced.
    for child in _CHILD_SITEMAPS:
        assert f"<loc>{child}" in body or f"<loc></loc>".replace("</loc>", child + "</loc>") in body, (
            f"index should reference {child}"
        )


def test_sitemap_index_emits_lastmod_per_child(with_generated_at):
    r = client.get("/sitemap.xml")
    expected = with_generated_at
    body = r.text
    # Three children → three <lastmod> entries on the index.
    assert body.count(f"<lastmod>{expected}</lastmod>") == 3


def test_child_sitemaps_emit_lastmod_when_corpus_meta_populated(with_generated_at):
    expected = with_generated_at
    for child in _CHILD_SITEMAPS:
        r = client.get(child)
        assert r.status_code == 200, f"{child} did not serve"
        body = r.text
        # When the child has no URLs (e.g. /sitemap-compare.xml under the
        # hermetic fixture that seeds no compare-eligible sources), there's
        # nothing to attach lastmod to — that's fine. When the child DOES
        # have URLs, every one of them must carry lastmod.
        url_count = body.count("<url>")
        lastmod_count = body.count(f"<lastmod>{expected}</lastmod>")
        if url_count:
            assert url_count == lastmod_count, (
                f"{child}: {url_count} <url> vs {lastmod_count} <lastmod>"
            )


def test_sitemap_index_omits_lastmod_when_corpus_meta_empty():
    r = client.get("/sitemap.xml")
    assert "<lastmod>" not in r.text


def test_child_sitemaps_omit_lastmod_when_corpus_meta_empty():
    for child in _CHILD_SITEMAPS:
        r = client.get(child)
        assert "<lastmod>" not in r.text, f"{child} unexpectedly emitted lastmod"


def test_all_sitemaps_remain_well_formed_xml(with_generated_at):
    for path in ("/sitemap.xml",) + _CHILD_SITEMAPS:
        r = client.get(path)
        ET.fromstring(r.text)  # would raise on malformed XML


def test_sitemap_lastmod_format_is_yyyy_mm_dd(with_generated_at):
    # Spec-compliant lastmod is W3C-DTF; date-only YYYY-MM-DD is sufficient.
    # Check across all four sitemaps.
    for path in ("/sitemap.xml",) + _CHILD_SITEMAPS:
        r = client.get(path)
        matches = re.findall(r"<lastmod>([^<]+)</lastmod>", r.text)
        for m in matches:
            assert re.match(r"^\d{4}-\d{2}-\d{2}$", m), f"{path}: bad lastmod {m!r}"


def test_sitemap_still_serves_when_corpus_meta_malformed(with_malformed_generated_at):
    # Malformed corpus_meta.generated_at → fall back to no-lastmod across all
    # four sitemaps; everything remains valid and serveable.
    for path in ("/sitemap.xml",) + _CHILD_SITEMAPS:
        r = client.get(path)
        assert r.status_code == 200, f"{path} did not serve"
        assert "<lastmod>" not in r.text, f"{path} leaked lastmod from malformed data"
        ET.fromstring(r.text)
