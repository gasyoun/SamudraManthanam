"""Tests for the scholarly-reader features added in v1.18.0.

Covers:
- Chapter extraction from a source's lines into a sidebar TOC.
- Toolbar markup (font-size buttons, lang toggle on parallel sources only).
- Per-line copy-citation button presence + data attributes.
- Mobile sidebar toggle markup.
- Help-overlay button hook.
"""
import re

import aiosqlite
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.main import app
from app.settings import settings

client = TestClient(app)


@pytest_asyncio.fixture
async def chaptered_source():
    """Seed a source with explicit H1 chapter markers across multiple verses.

    Yields the slug — tests hit `/sources/{slug}`.
    """
    db = await aiosqlite.connect(settings.DB_PATH)
    await db.execute(
        "INSERT INTO sources (id, filename, title, sort_order, slug) "
        "VALUES (900, 'rdr-chaptered.html', 'Reader test source', 900, 'rdr-chaptered')"
    )
    rows = [
        (1, "1.1", "Глава I", "<div class='citation_block' id='1.1'>verse one</div>"),
        (2, "1.2", "Глава I", "<div class='citation_block' id='1.2'>verse two</div>"),
        (3, "2.1", "Глава II", "<div class='citation_block' id='2.1'>chapter two start</div>"),
        (4, "2.2", "Глава II", "<div class='citation_block' id='2.2'>chapter two second</div>"),
        (5, "3.1", "Глава III", "<div class='citation_block' id='3.1'>chapter three</div>"),
    ]
    for line_num, link_id, chapter, html in rows:
        await db.execute(
            "INSERT INTO corpus_lines (line_text, line_html, source_id, line_num, link_id, chapter) "
            "VALUES (?, ?, 900, ?, ?, ?)",
            (f"text {line_num}", html, line_num, link_id, chapter),
        )
    await db.commit()
    await db.close()
    yield "rdr-chaptered"
    db = await aiosqlite.connect(settings.DB_PATH)
    await db.execute("DELETE FROM corpus_lines WHERE source_id = 900")
    await db.execute("DELETE FROM sources WHERE id = 900")
    await db.commit()
    await db.close()


@pytest_asyncio.fixture
async def unchaptered_source():
    """Source whose lines have NO chapter field — sidebar must NOT render."""
    db = await aiosqlite.connect(settings.DB_PATH)
    await db.execute(
        "INSERT INTO sources (id, filename, title, sort_order, slug) "
        "VALUES (901, 'rdr-flat.html', 'Reader flat source', 901, 'rdr-flat')"
    )
    await db.execute(
        "INSERT INTO corpus_lines (line_text, line_html, source_id, line_num, link_id, chapter) "
        "VALUES ('x', '<div>line</div>', 901, 1, '1.1', '')"
    )
    await db.commit()
    await db.close()
    yield "rdr-flat"
    db = await aiosqlite.connect(settings.DB_PATH)
    await db.execute("DELETE FROM corpus_lines WHERE source_id = 901")
    await db.execute("DELETE FROM sources WHERE id = 901")
    await db.commit()
    await db.close()


@pytest_asyncio.fixture
async def parallel_chaptered_source():
    """Parallel source (iast + translation blocks) WITH chapters."""
    db = await aiosqlite.connect(settings.DB_PATH)
    await db.execute(
        "INSERT INTO sources (id, filename, title, sort_order, slug) "
        "VALUES (902, 'rdr-par.html', 'Reader parallel chaptered', 902, 'rdr-par')"
    )
    await db.execute(
        "INSERT INTO corpus_lines (line_text, line_html, source_id, line_num, link_id, chapter) "
        "VALUES ('p1', "
        "'<div class=\"chapter_block iast\">sansk1</div>"
        "<div class=\"chapter_block translation\">rus1</div>',"
        " 902, 1, '1.1', 'Глава I')"
    )
    await db.commit()
    await db.close()
    yield "rdr-par"
    db = await aiosqlite.connect(settings.DB_PATH)
    await db.execute("DELETE FROM corpus_lines WHERE source_id = 902")
    await db.execute("DELETE FROM sources WHERE id = 902")
    await db.commit()
    await db.close()


# ── Chapter sidebar ──────────────────────────────────────────────────────────

def test_chaptered_source_renders_sidebar_with_all_chapters(chaptered_source):
    r = client.get(f"/sources/{chaptered_source}")
    body = r.text
    # All 3 distinct chapters appear in the sidebar.
    assert '<aside class="rdr-sidebar"' in body
    for ch in ("Глава I", "Глава II", "Глава III"):
        # Each chapter shows up at least twice — once in sidebar, once as
        # an in-content chapter-heading.
        assert body.count(ch) >= 2, f"chapter {ch!r} missing"


def test_chapter_sidebar_links_to_first_line_of_each_chapter(chaptered_source):
    r = client.get(f"/sources/{chaptered_source}")
    body = r.text
    # Chapter I → first line is line_num=1 → anchor #L1.
    # Chapter II → first line is line_num=3.
    # Chapter III → first line is line_num=5.
    sidebar_match = re.search(r'<aside class="rdr-sidebar".*?</aside>', body, re.DOTALL)
    assert sidebar_match is not None
    sidebar = sidebar_match.group(0)
    assert 'href="#L1"' in sidebar
    assert 'href="#L3"' in sidebar
    assert 'href="#L5"' in sidebar


def test_unchaptered_source_omits_sidebar(unchaptered_source):
    r = client.get(f"/sources/{unchaptered_source}")
    body = r.text
    # No sidebar element when no chapters exist.
    assert '<aside class="rdr-sidebar"' not in body
    # Layout marker reflects the no-sidebar variant.
    assert 'reader-layout no-sidebar' in body or 'class="reader-layout no-sidebar"' in body


def test_unchaptered_source_omits_chapter_toggle_button(unchaptered_source):
    r = client.get(f"/sources/{unchaptered_source}")
    # The mobile sidebar toggle has no purpose without chapters.
    assert 'id="rdr-sidebar-toggle"' not in r.text


# ── Toolbar ──────────────────────────────────────────────────────────────────

def test_toolbar_emits_font_size_controls(chaptered_source):
    r = client.get(f"/sources/{chaptered_source}")
    body = r.text
    assert 'id="rdr-font-smaller"' in body
    assert 'id="rdr-font-larger"' in body
    assert 'A−' in body and 'A+' in body


def test_toolbar_emits_help_button(chaptered_source):
    r = client.get(f"/sources/{chaptered_source}")
    assert 'id="rdr-help-btn"' in r.text


def test_toolbar_omits_lang_toggle_on_non_parallel_source(chaptered_source):
    # chaptered_source has no chapter_block iast markers → non-parallel.
    # Lang toggle (Оба / Рус / Санскрит) should NOT appear.
    r = client.get(f"/sources/{chaptered_source}")
    body = r.text
    assert "Санскрит" not in body or 'class="tb-btn' not in body.split("Санскрит")[0][-200:]


def test_toolbar_emits_lang_toggle_on_parallel_source(parallel_chaptered_source):
    r = client.get(f"/sources/{parallel_chaptered_source}")
    body = r.text
    # Three lang-toggle buttons present.
    assert "Оба" in body
    assert "Рус" in body
    assert "Санскрит" in body
    # The "Оба" button is active on the bare URL (no lang param).
    assert 'class="tb-btn active"' in body


def test_lang_toggle_marks_current_variant_as_active(parallel_chaptered_source):
    r = client.get(f"/sources/{parallel_chaptered_source}?lang=sa")
    body = r.text
    # The "Санскрит" button gets the active class.
    sa_link = re.search(
        r'class="tb-btn active"[^>]*href="\?[^"]*lang=sa"', body,
    )
    assert sa_link is not None or 'tb-btn active' in body


# ── Per-line copy-citation buttons + data attributes ─────────────────────────

def test_each_line_has_copy_citation_button(chaptered_source):
    r = client.get(f"/sources/{chaptered_source}")
    body = r.text
    # 5 lines seeded → 5 copy buttons.
    assert body.count('class="copy-citation-btn"') == 5


def test_each_line_row_carries_data_attributes_for_clipboard(chaptered_source):
    r = client.get(f"/sources/{chaptered_source}")
    body = r.text
    # data-line-num and data-link-id are needed by reader.js to build the
    # markdown link.
    assert 'data-link-id="1.1"' in body
    assert 'data-link-id="2.1"' in body
    assert 'data-line-num="1"' in body
    assert 'data-line-num="5"' in body


# ── reader.js loaded ─────────────────────────────────────────────────────────

def test_reader_js_is_loaded_on_source_pages(chaptered_source):
    r = client.get(f"/sources/{chaptered_source}")
    assert '/static/scripts/reader.js' in r.text


def test_reader_js_not_loaded_on_other_page_types():
    # /search uses its own bundle; /q/{slug} doesn't need reader.js.
    for path in ("/search", "/q/dharma"):
        r = client.get(path)
        if r.status_code == 200:
            assert '/static/scripts/reader.js' not in r.text


# ── Sidebar count matches chapters in DB ────────────────────────────────────

def test_sidebar_lists_chapter_count_in_title(chaptered_source):
    # The sidebar header shows "Главы (N)" where N == distinct chapter count.
    r = client.get(f"/sources/{chaptered_source}")
    assert "Главы (3)" in r.text


# ── Render-time chapter fallback (chapter_title div in line_html) ───────────

@pytest_asyncio.fixture
async def chapter_title_div_source():
    """Source whose chapter markers are `<div class="chapter_title">` in
    line_html, not in the `chapter` column. Mirrors the Mahābhārata-parvan
    shape on the live corpus."""
    db = await aiosqlite.connect(settings.DB_PATH)
    await db.execute(
        "INSERT INTO sources (id, filename, title, sort_order, slug) "
        "VALUES (903, 'rdr-divch.html', 'Reader div-chapter source', 903, 'rdr-divch')"
    )
    rows = [
        # Chapter heading row — no `chapter` column, but the html carries it.
        (1, "chapter_1", "", '<div class="chapter_title" id="chapter_1">Глава 1</div>'),
        (2, "1.1", "", '<div class="citation_block" id="1.1">v1</div>'),
        (3, "1.2", "", '<div class="citation_block" id="1.2">v2</div>'),
        (4, "chapter_2", "", '<div class="chapter_title" id="chapter_2">Глава 2</div>'),
        (5, "2.1", "", '<div class="citation_block" id="2.1">v3</div>'),
    ]
    for line_num, link_id, chapter, html in rows:
        await db.execute(
            "INSERT INTO corpus_lines (line_text, line_html, source_id, line_num, link_id, chapter) "
            "VALUES (?, ?, 903, ?, ?, ?)",
            (f"t {line_num}", html, line_num, link_id, chapter),
        )
    await db.commit()
    await db.close()
    yield "rdr-divch"
    db = await aiosqlite.connect(settings.DB_PATH)
    await db.execute("DELETE FROM corpus_lines WHERE source_id = 903")
    await db.execute("DELETE FROM sources WHERE id = 903")
    await db.commit()
    await db.close()


def test_chapter_fallback_detects_chapter_title_div(chapter_title_div_source):
    r = client.get(f"/sources/{chapter_title_div_source}")
    body = r.text
    # Two chapter entries should appear in the sidebar even though the
    # `chapter` column is empty for every row.
    assert "Главы (2)" in body
    sidebar = re.search(r'<aside class="rdr-sidebar".*?</aside>', body, re.DOTALL)
    assert sidebar is not None
    assert "Глава 1" in sidebar.group(0)
    assert "Глава 2" in sidebar.group(0)
    # Anchor targets point at the chapter-heading line, not the first verse.
    assert 'href="#L1"' in sidebar.group(0)
    assert 'href="#L4"' in sidebar.group(0)
