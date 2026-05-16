"""Tests for source-page JSON-LD and title parsing.

Two layers:
1. Pure parser/builder tests (no DB, no HTTP) — fast and exhaustive over the
   weird shapes seen in real corpus titles.
2. HTTP-level smoke against the conftest source fixtures — confirms the JSON
   actually lands in the rendered `<script type="application/ld+json">` and
   parses as valid JSON.
"""
import json
import re

import aiosqlite
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.main import app
from app.services.source_metadata import (
    build_breadcrumb_jsonld,
    build_source_jsonld,
    parse_source_title,
)
from app.settings import settings

client = TestClient(app)


# ── parse_source_title — handles every shape seen in the live corpus ─────────

def test_parse_title_with_year_and_translator():
    out = parse_source_title("Махабхарата VI (2009); В.Г. Эрман")
    assert out == {
        "name": "Махабхарата VI (2009); В.Г. Эрман",
        "translator": "В.Г. Эрман",
        "year": "2009",
    }


def test_parse_title_with_author_prefix():
    out = parse_source_title("Бхартрихари. Шатакатраям (2020); М. В. Леонов")
    assert out["year"] == "2020"
    assert out["translator"] == "М. В. Леонов"
    # Full title stays as-is — we don't strip the author prefix.
    assert out["name"] == "Бхартрихари. Шатакатраям (2020); М. В. Леонов"


def test_parse_title_without_year():
    out = parse_source_title("Ашвагхоша. Буддхачарита; М.В. Леонов")
    assert out["year"] == ""
    assert out["translator"] == "М.В. Леонов"


def test_parse_title_without_translator():
    out = parse_source_title("Махабхарата XIII")
    assert out["year"] == ""
    assert out["translator"] == ""
    assert out["name"] == "Махабхарата XIII"


def test_parse_title_handles_extra_whitespace():
    out = parse_source_title("  Бхагавад-Гита (1977);   Б. Л. Смирнов  ")
    assert out["year"] == "1977"
    assert out["translator"] == "Б. Л. Смирнов"


def test_parse_title_empty_string():
    out = parse_source_title("")
    assert out == {"name": "", "translator": "", "year": ""}


def test_parse_title_18th_century_year():
    # Verify the year regex doesn't fail on early publications.
    out = parse_source_title("БАГУАТ-ГЕТА (1788); А.А. Петров")
    assert out["year"] == "1788"


# ── build_source_jsonld — only emits fields that exist ───────────────────────

def test_jsonld_minimum_fields_when_translator_and_year_present():
    source = {"id": 1, "title": "Бхагавад-Гита (1977); Б. Л. Смирнов"}
    jsonld = build_source_jsonld(
        source=source,
        canonical_url="https://samskrtam.ru/sources/1",
        site_name="Пахтанье океана",
    )
    assert jsonld["@type"] == "Book"
    assert jsonld["@id"] == "https://samskrtam.ru/sources/1"
    assert jsonld["url"] == "https://samskrtam.ru/sources/1"
    assert jsonld["inLanguage"] == "ru"
    assert jsonld["datePublished"] == "1977"
    assert jsonld["translator"]["@type"] == "Person"
    assert jsonld["translator"]["name"] == "Б. Л. Смирнов"
    assert jsonld["isPartOf"]["@type"] == "WebSite"
    assert jsonld["isPartOf"]["name"] == "Пахтанье океана"


def test_jsonld_omits_translator_when_unparseable():
    # No semicolon → no translator. Field should be absent rather than empty.
    source = {"id": 1, "title": "Махабхарата XIII"}
    jsonld = build_source_jsonld(
        source=source, canonical_url="/sources/1", site_name="Test",
    )
    assert "translator" not in jsonld
    assert "datePublished" not in jsonld


def test_jsonld_omits_year_when_absent():
    source = {"id": 1, "title": "Ашвагхоша. Буддхачарита; М.В. Леонов"}
    jsonld = build_source_jsonld(
        source=source, canonical_url="/sources/1", site_name="Test",
    )
    assert "datePublished" not in jsonld
    assert jsonld["translator"]["name"] == "М.В. Леонов"


def test_jsonld_includes_full_title_as_name():
    # The name field carries the full unparsed string so search engines show
    # the same heading users see on the page.
    source = {"id": 1, "title": "Махабхарата VI (2009); В.Г. Эрман"}
    jsonld = build_source_jsonld(
        source=source, canonical_url="/sources/1", site_name="Test",
    )
    assert jsonld["name"] == "Махабхарата VI (2009); В.Г. Эрман"


def test_jsonld_serializes_to_valid_json():
    source = {"id": 1, "title": "Бхагавад-Гита (1977); Б. Л. Смирнов"}
    jsonld = build_source_jsonld(
        source=source, canonical_url="/sources/1", site_name="Test",
    )
    # Round-trip through JSON to confirm no non-serialisable values leaked in.
    encoded = json.dumps(jsonld, ensure_ascii=False)
    decoded = json.loads(encoded)
    assert decoded["@type"] == "Book"


# ── build_breadcrumb_jsonld ──────────────────────────────────────────────────

def test_breadcrumb_has_site_then_source_position_order():
    crumb = build_breadcrumb_jsonld(
        source_title="Махабхарата VI",
        source_url="/sources/204",
        site_name="Пахтанье океана",
        site_url="https://samskrtam.ru",
    )
    items = crumb["itemListElement"]
    assert len(items) == 2
    assert items[0]["position"] == 1
    assert items[0]["name"] == "Пахтанье океана"
    assert items[1]["position"] == 2
    assert items[1]["name"] == "Махабхарата VI"


def test_breadcrumb_falls_back_to_root_when_site_url_empty():
    crumb = build_breadcrumb_jsonld(
        source_title="Test", source_url="/sources/1",
        site_name="Site", site_url="",
    )
    assert crumb["itemListElement"][0]["item"] == "/"


# ── HTTP integration — JSON-LD appears in source_view.html ───────────────────

@pytest_asyncio.fixture
async def source_with_translator():
    """Insert a high-id source that won't collide with conftest fixtures."""
    db = await aiosqlite.connect(settings.DB_PATH)
    await db.execute(
        "INSERT INTO sources (id, filename, title, sort_order) "
        "VALUES (500, 'test-src.html', 'Бхагавад-Гита (1977); Б. Л. Смирнов', 500)"
    )
    await db.execute(
        "INSERT INTO corpus_lines (line_text, line_html, source_id, line_num, link_id, chapter) "
        "VALUES ('test', '<p>test</p>', 500, 1, '1.1', 'Глава I')"
    )
    await db.commit()
    await db.close()
    yield 500
    db = await aiosqlite.connect(settings.DB_PATH)
    await db.execute("DELETE FROM corpus_lines WHERE source_id = 500")
    await db.execute("DELETE FROM sources WHERE id = 500")
    await db.commit()
    await db.close()


def test_source_view_emits_book_jsonld(source_with_translator):
    r = client.get(f"/sources/{source_with_translator}")
    assert r.status_code == 200
    body = r.text

    # Two <script type="application/ld+json"> blocks: Book + BreadcrumbList.
    blocks = re.findall(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
        body, re.DOTALL,
    )
    assert len(blocks) == 2

    book = json.loads(blocks[0])
    crumb = json.loads(blocks[1])

    assert book["@type"] == "Book"
    assert book["name"] == "Бхагавад-Гита (1977); Б. Л. Смирнов"
    assert book["translator"]["name"] == "Б. Л. Смирнов"
    assert book["datePublished"] == "1977"
    assert book["inLanguage"] == "ru"

    assert crumb["@type"] == "BreadcrumbList"
    assert crumb["itemListElement"][1]["name"].startswith("Бхагавад-Гита")


def test_source_view_emits_canonical_link(source_with_translator):
    r = client.get(f"/sources/{source_with_translator}")
    assert 'rel="canonical"' in r.text
    assert f'/sources/{source_with_translator}' in r.text
