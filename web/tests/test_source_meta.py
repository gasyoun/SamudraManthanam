"""Tests for meta.json → DB wiring via ingest and API exposure."""
import asyncio
import json
import os
import pytest
import aiosqlite
from fastapi.testclient import TestClient

from app.main import app
from app.db import create_schema

client = TestClient(app)


# ── /api/sources includes new fields ────────────────────────────────────────

def test_sources_api_includes_meta_fields():
    r = client.get("/api/sources")
    assert r.status_code == 200
    sources = r.json()
    assert len(sources) >= 1
    first = sources[0]
    # All new fields must be present in the response (may be None).
    for field in ("title_en", "subtitle", "credit", "credit_role",
                  "imprint", "publisher", "year"):
        assert field in first, f"missing field: {field}"


# ── Ingest populates meta columns from .meta.json ────────────────────────────

def test_ingest_loads_meta_json(tmp_path):
    """Round-trip: ingest reads a sibling .meta.json and stores bibliographic
    fields on the sources row."""
    from ingest.ingest import ingest

    # Minimal corpus layout.
    data_dir = tmp_path / "Data"
    prog_dir = tmp_path / "Programdata"
    data_dir.mkdir()
    prog_dir.mkdir()

    corpus_file = data_dir / "test_source.html"
    corpus_file.write_text(
        "<!-- Test source -->\n<div>some text</div>\n",
        encoding="utf-8",
    )

    meta = {
        "schema_version": 1,
        "filename": "test_source.html",
        "slug": "test_source",
        "title_ru": "Test source",
        "title_en": "Test Source (EN)",
        "subtitle": "A test",
        "credit": "Ivan Ivanov",
        "credit_role": "Translation",
        "imprint": "Moscow, 2024",
        "publisher": "Nauka",
        "year": 2024,
        "scripts": ["cyrillic"],
        "provenance": "",
        "rights": "",
        "needs_review": False,
    }
    meta_file = data_dir / "test_source.html.meta.json"
    meta_file.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")

    (prog_dir / "data.txt").write_text("test_source.html\n", encoding="utf-8")

    db_path = str(tmp_path / "test.db")
    asyncio.run(ingest(str(tmp_path), db_path))

    async def _check():
        db = await aiosqlite.connect(db_path)
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT title_en, subtitle, credit, credit_role, imprint, publisher, year "
            "FROM sources WHERE filename = 'test_source.html'"
        ) as cur:
            row = await cur.fetchone()
        await db.close()
        return row

    row = asyncio.run(_check())
    assert row is not None
    assert row["title_en"] == "Test Source (EN)"
    assert row["credit"] == "Ivan Ivanov"
    assert row["credit_role"] == "Translation"
    assert row["year"] == 2024
    assert row["publisher"] == "Nauka"


def test_ingest_handles_missing_meta_json(tmp_path):
    """Ingest must succeed even when no sibling .meta.json exists."""
    from ingest.ingest import ingest

    data_dir = tmp_path / "Data"
    prog_dir = tmp_path / "Programdata"
    data_dir.mkdir()
    prog_dir.mkdir()

    corpus_file = data_dir / "no_meta.html"
    corpus_file.write_text("<!-- No meta -->\n<div>text</div>\n", encoding="utf-8")
    (prog_dir / "data.txt").write_text("no_meta.html\n", encoding="utf-8")

    db_path = str(tmp_path / "test.db")
    asyncio.run(ingest(str(tmp_path), db_path))

    async def _check():
        db = await aiosqlite.connect(db_path)
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT credit, year FROM sources WHERE filename = 'no_meta.html'"
        ) as cur:
            row = await cur.fetchone()
        await db.close()
        return row

    row = asyncio.run(_check())
    assert row is not None
    assert row["credit"] is None
    assert row["year"] is None
