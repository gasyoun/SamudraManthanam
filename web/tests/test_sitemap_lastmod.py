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


# ── HTTP-level: /sitemap.xml output ─────────────────────────────────────────

def test_sitemap_emits_lastmod_when_corpus_meta_populated(with_generated_at):
    expected = with_generated_at
    r = client.get("/sitemap.xml")
    assert r.status_code == 200
    body = r.text
    # At least one <lastmod> with the date.
    assert f"<lastmod>{expected}</lastmod>" in body
    # Should appear on EVERY url entry, not just one — count parity.
    url_count = body.count("<url>")
    lastmod_count = body.count(f"<lastmod>{expected}</lastmod>")
    assert url_count == lastmod_count, (
        f"every <url> should carry <lastmod>: got {url_count} urls vs {lastmod_count} lastmods"
    )


def test_sitemap_omits_lastmod_when_corpus_meta_empty():
    r = client.get("/sitemap.xml")
    body = r.text
    # No populated fixture → no lastmod tags at all.
    assert "<lastmod>" not in body


def test_sitemap_remains_well_formed_xml_with_lastmod(with_generated_at):
    r = client.get("/sitemap.xml")
    # Must still parse — a stray malformed `<lastmod>` would crash XML parsing.
    ET.fromstring(r.text)


def test_sitemap_lastmod_format_is_yyyy_mm_dd(with_generated_at):
    r = client.get("/sitemap.xml")
    # Spec-compliant lastmod is W3C-DTF; date-only YYYY-MM-DD is the
    # simplest valid form.
    matches = re.findall(r"<lastmod>([^<]+)</lastmod>", r.text)
    assert matches, "no <lastmod> tags found"
    for m in matches:
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", m), f"bad lastmod format: {m}"


def test_sitemap_still_serves_when_corpus_meta_malformed(with_malformed_generated_at):
    # Malformed corpus_meta.generated_at → fall back to no-lastmod; the
    # sitemap remains valid and serveable.
    r = client.get("/sitemap.xml")
    assert r.status_code == 200
    assert "<lastmod>" not in r.text
    ET.fromstring(r.text)  # still well-formed
