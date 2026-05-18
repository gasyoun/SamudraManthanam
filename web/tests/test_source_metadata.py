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
    KNOWN_SANSKRIT_AUTHORS,
    _AUTHOR_IAST,
    build_breadcrumb_jsonld,
    build_line_quotation,
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
        "author": "",
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
    assert out == {"name": "", "translator": "", "year": "", "author": ""}


def test_parse_title_18th_century_year():
    # Verify the year regex doesn't fail on early publications.
    out = parse_source_title("БАГУАТ-ГЕТА (1788); А.А. Петров")
    assert out["year"] == "1788"


# ── Author detection ────────────────────────────────────────────────────────

def test_parse_title_detects_single_word_author():
    out = parse_source_title("Бхартрихари. Шатакатраям (2020); М. В. Леонов")
    assert out["author"] == "Бхартрихари"
    assert out["translator"] == "М. В. Леонов"
    assert out["year"] == "2020"


def test_parse_title_detects_multi_word_author():
    # The longer-prefix-wins rule: "Ватсьяянга Маланга" must beat any partial match.
    out = parse_source_title("Ватсьяянга Маланга. Камасутра (2000); А. Я. Сыркин")
    assert out["author"] == "Ватсьяянга Маланга"


def test_parse_title_detects_kalidasa():
    out = parse_source_title("Калидаса. Облако-вестник (1914); П. Риттер")
    assert out["author"] == "Калидаса"


def test_parse_title_detects_jayadeva():
    out = parse_source_title("Джаядева. Гитаговинда (2020); А.Я. Сыркин")
    assert out["author"] == "Джаядева"


def test_parse_title_detects_author_as_suffix_segment():
    # Serebryakov's edition reverses the convention to "Work. Author (Year)".
    out = parse_source_title("Шатакатраям. Бхартрихари (1979); И.Д. Серебряков")
    assert out["author"] == "Бхартрихари"
    assert out["translator"] == "И.Д. Серебряков"
    assert out["year"] == "1979"


def test_parse_title_detects_author_after_subpart_segment():
    # Erman's Raghuvaṃśa has author as the third segment.
    out = parse_source_title("Рагхуванша. Род Рагху. Калидаса (1996); В.Г. Эрман")
    assert out["author"] == "Калидаса"


def test_parse_title_does_not_misdetect_work_name_prefix():
    # "Ригведа." is part of the work name, not an author. The detector
    # must return "" here (false-positive guard).
    out = parse_source_title("Ригведа. Мандала I (1989); Т.Я. Елизаренкова")
    assert out["author"] == ""
    out = parse_source_title("Атхарваведа. Книга 1 (2005); Т.Я. Елизаренкова")
    assert out["author"] == ""
    out = parse_source_title("Махабхарата VI (2009); В.Г. Эрман")
    assert out["author"] == ""


def test_parse_title_anonymous_works_have_empty_author():
    # Major works that are anonymous in this corpus's titling convention.
    for title in (
        "Бхагавад-Гита (1977); Б. Л. Смирнов",
        "Иша упанишада (1992); А.Я. Сыркин",
        "Рамаяна I (2006); П.А. Гринцер",
        "Хатха Йога Прадипика; Шайлендра Шарма",
    ):
        assert parse_source_title(title)["author"] == "", f"misdetected author in {title!r}"


def test_known_authors_registry_is_non_empty():
    # Safety net: if a refactor accidentally empties this, every author-
    # bearing title would silently lose its structured author field.
    assert len(KNOWN_SANSKRIT_AUTHORS) >= 10


def test_jsonld_emits_author_when_detected():
    source = {"id": 1, "title": "Бхартрихари. Шатакатраям (2020); М. В. Леонов"}
    jsonld = build_source_jsonld(
        source=source, canonical_url="/sources/1", site_name="Site",
    )
    assert jsonld["author"]["@type"] == "Person"
    assert jsonld["author"]["name"] == "Бхартрихари"
    # Translator is a separate field — both should coexist.
    assert jsonld["translator"]["name"] == "М. В. Леонов"


def test_jsonld_omits_author_when_anonymous_work():
    source = {"id": 1, "title": "Махабхарата VI (2009); В.Г. Эрман"}
    jsonld = build_source_jsonld(
        source=source, canonical_url="/sources/1", site_name="Site",
    )
    assert "author" not in jsonld
    # Translator + year still emitted.
    assert jsonld["translator"]["name"] == "В.Г. Эрман"
    assert jsonld["datePublished"] == "2009"


# ── IAST alternateName on author Person ─────────────────────────────────────

def test_iast_mapping_covers_every_known_author():
    # If a name is in the detector set but missing from the IAST mapping,
    # we'd emit a `Person` without `alternateName` for it. Single-source-of-
    # truth: the public set is derived from the mapping's keys, so this is
    # tautological — but the test still guards against accidental divergence
    # if someone splits the two declarations.
    for author in KNOWN_SANSKRIT_AUTHORS:
        assert author in _AUTHOR_IAST, f"{author!r} missing IAST entry"
        assert _AUTHOR_IAST[author], f"{author!r} has empty IAST value"


def test_iast_values_are_ascii_or_combining_diacritics_only():
    # IAST is Latin-with-diacritics — no Cyrillic should leak in. Catches
    # a copy-paste mistake where a Russian form ends up as the IAST value.
    for ru, iast in _AUTHOR_IAST.items():
        for ch in iast:
            # Reject Cyrillic block (U+0400–U+04FF).
            assert not (0x0400 <= ord(ch) <= 0x04FF), (
                f"{ru!r}: IAST value {iast!r} contains Cyrillic char {ch!r}"
            )


def test_jsonld_author_includes_iast_alternate_name():
    source = {"id": 1, "title": "Бхартрихари. Шатакатраям (2020); М. В. Леонов"}
    jsonld = build_source_jsonld(
        source=source, canonical_url="/sources/1", site_name="Site",
    )
    assert jsonld["author"]["name"] == "Бхартрихари"
    assert jsonld["author"]["alternateName"] == "Bhartṛhari"


def test_jsonld_iast_for_kalidasa():
    source = {"id": 1, "title": "Калидаса. Облако-вестник (1914); П. Риттер"}
    jsonld = build_source_jsonld(
        source=source, canonical_url="/sources/1", site_name="Site",
    )
    assert jsonld["author"]["alternateName"] == "Kālidāsa"


def test_jsonld_iast_for_multi_word_author():
    source = {"id": 1, "title": "Ватсьяянга Маланга. Камасутра (2000); А. Я. Сыркин"}
    jsonld = build_source_jsonld(
        source=source, canonical_url="/sources/1", site_name="Site",
    )
    assert jsonld["author"]["name"] == "Ватсьяянга Маланга"
    assert jsonld["author"]["alternateName"] == "Vātsyāyana Mallanāga"


def test_jsonld_iast_for_suffix_form_author():
    # Serebryakov edition uses suffix form: "Work. Author (Year)".
    # IAST should still attach.
    source = {"id": 1, "title": "Шатакатраям. Бхартрихари (1979); И.Д. Серебряков"}
    jsonld = build_source_jsonld(
        source=source, canonical_url="/sources/1", site_name="Site",
    )
    assert jsonld["author"]["alternateName"] == "Bhartṛhari"


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
    """Insert a high-id source that won't collide with conftest fixtures.
    Yields (numeric_id, slug) so tests can hit either URL form."""
    db = await aiosqlite.connect(settings.DB_PATH)
    await db.execute(
        "INSERT INTO sources (id, filename, title, sort_order, slug) "
        "VALUES (500, 'test-src.html', 'Бхагавад-Гита (1977); Б. Л. Смирнов', 500, 'test-src')"
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
    r = client.get("/sources/test-src")
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
    # Hit the slug URL directly; the numeric form 301-redirects to slug.
    r = client.get("/sources/test-src")
    assert 'rel="canonical"' in r.text
    assert '/sources/test-src' in r.text


# ── hasPart sample on Book ──────────────────────────────────────────────────

def test_jsonld_haspart_includes_sample_lines_when_provided():
    source = {"id": 5, "slug": "test-src", "title": "Test (2020); Тест"}
    lines = [
        {"line_num": 1, "link_id": "1.1", "line_text": "first verse", "chapter": "Глава I"},
        {"line_num": 2, "link_id": "1.2", "line_text": "second verse", "chapter": "Глава I"},
    ]
    jsonld = build_source_jsonld(
        source=source, canonical_url="/sources/5", site_name="Site",
        sample_lines=lines,
    )
    assert jsonld["numberOfItems"] == 2
    assert "hasPart" in jsonld
    assert len(jsonld["hasPart"]) == 2
    assert jsonld["hasPart"][0]["@type"] == "Quotation"
    assert jsonld["hasPart"][0]["text"] == "first verse"


def test_jsonld_haspart_caps_at_sample_size():
    # 30 lines → with default cap of 20, only 20 appear in hasPart but the
    # numberOfItems count reflects the FULL filtered set.
    source = {"id": 5, "slug": "test-src", "title": "Test"}
    lines = [
        {"line_num": i, "link_id": f"1.{i}", "line_text": f"verse {i}", "chapter": ""}
        for i in range(1, 31)
    ]
    jsonld = build_source_jsonld(
        source=source, canonical_url="/sources/5", site_name="Site",
        sample_lines=lines,
    )
    assert jsonld["numberOfItems"] == 30
    assert len(jsonld["hasPart"]) == 20


def test_jsonld_haspart_skips_empty_text_lines():
    # Chapter-header rows have line_text=="" and should NOT count or appear.
    source = {"id": 5, "slug": "test-src", "title": "Test"}
    lines = [
        {"line_num": 1, "link_id": "chapter_1", "line_text": "", "chapter": ""},
        {"line_num": 2, "link_id": "1.1", "line_text": "real verse", "chapter": ""},
        {"line_num": 3, "link_id": "1.2", "line_text": "another", "chapter": ""},
    ]
    jsonld = build_source_jsonld(
        source=source, canonical_url="/sources/5", site_name="Site",
        sample_lines=lines,
    )
    assert jsonld["numberOfItems"] == 2
    assert all(p["text"] for p in jsonld["hasPart"])


def test_jsonld_haspart_omitted_when_no_sample_lines():
    source = {"id": 5, "slug": "test-src", "title": "Test"}
    jsonld = build_source_jsonld(
        source=source, canonical_url="/sources/5", site_name="Site",
    )
    assert "hasPart" not in jsonld
    assert "numberOfItems" not in jsonld


def test_jsonld_haspart_links_use_base_url_when_provided():
    source = {"id": 5, "slug": "test-src", "title": "Test"}
    lines = [{"line_num": 1, "link_id": "1.1", "line_text": "v", "chapter": ""}]
    jsonld = build_source_jsonld(
        source=source, canonical_url="https://samskrtam.ru/sources/5",
        site_name="Site", sample_lines=lines, base_url="https://samskrtam.ru",
    )
    assert jsonld["hasPart"][0]["@id"].startswith("https://samskrtam.ru/sources/test-src?highlight=1.1")


# ── Per-line Quotation builder ──────────────────────────────────────────────

def test_line_quotation_minimal_shape():
    line = {"line_num": 10, "link_id": "1.1", "line_text": "dharma quote",
            "chapter": "Глава I"}
    q = build_line_quotation(
        line=line, slug="test-source", source_url="/sources/test-source",
    )
    assert q["@type"] == "Quotation"
    assert q["@id"].endswith("/sources/test-source?highlight=1.1")
    assert q["text"] == "dharma quote"
    assert q["inLanguage"] == "ru"
    assert q["isPartOf"] == {"@id": "/sources/test-source"}
    assert q["citation"] == "Глава I, 1.1"


def test_line_quotation_falls_back_to_line_num_when_no_link_id():
    line = {"line_num": 42, "link_id": "", "line_text": "verse text", "chapter": ""}
    q = build_line_quotation(
        line=line, slug="test-source", source_url="/sources/test-source",
    )
    assert q["@id"].endswith("highlight=42")
    assert "citation" not in q  # no chapter, no citation field


def test_line_quotation_url_encodes_link_id():
    # link_ids like "1.3-6" must be URL-safe.
    line = {"line_num": 10, "link_id": "1.3-6", "line_text": "x", "chapter": ""}
    q = build_line_quotation(
        line=line, slug="test-source", source_url="/sources/test-source",
    )
    assert "highlight=1.3-6" in q["@id"]


def test_line_quotation_truncates_pathological_long_text():
    # Some Smirnov-edition lines pack ~6 KB of footnote prose; cap at 1500 chars.
    line = {"line_num": 1, "link_id": "1.1", "line_text": "x" * 5000, "chapter": ""}
    q = build_line_quotation(
        line=line, slug="test-source", source_url="/sources/test-source",
    )
    assert len(q["text"]) <= 1500 + 1  # +1 for the ellipsis character
    assert q["text"].endswith("…")


# ── HTTP integration for the new blocks ─────────────────────────────────────

def test_source_view_emits_haspart_in_book_jsonld(source_with_translator):
    r = client.get("/sources/test-src")
    body = r.text
    blocks = re.findall(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
        body, re.DOTALL,
    )
    book = json.loads(blocks[0])
    assert book["@type"] == "Book"
    assert book.get("numberOfItems", 0) >= 1
    assert "hasPart" in book


def test_source_view_without_highlight_emits_two_jsonld_blocks(source_with_translator):
    r = client.get("/sources/test-src")
    blocks = re.findall(
        r'<script type="application/ld\+json">',
        r.text,
    )
    # Book + BreadcrumbList. No highlight → no third block.
    assert len(blocks) == 2


def test_source_view_with_highlight_emits_third_quotation_block(source_with_translator):
    r = client.get("/sources/test-src?highlight=1.1")
    blocks = re.findall(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
        r.text, re.DOTALL,
    )
    assert len(blocks) == 3
    quotation = json.loads(blocks[2])
    assert quotation["@type"] == "Quotation"
    assert "highlight=1.1" in quotation["@id"]


def test_source_view_with_unmatched_highlight_does_not_emit_quotation(source_with_translator):
    # Highlight that doesn't resolve to any line → no third block emitted,
    # don't fabricate a Quotation with empty text.
    r = client.get("/sources/test-src?highlight=nope")
    blocks = re.findall(
        r'<script type="application/ld\+json">',
        r.text,
    )
    assert len(blocks) == 2
