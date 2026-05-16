"""Tests for /compare/{work}/{ch}.{v} multi-translation comparison route.

Covers the data path (compare_service.get_comparison) and the HTTP layer
(routers.compare.view_comparison). Uses the session test DB and seeds it with
minimal Bhagavadgītā-style sources matching the filenames in compare_config.

Each test inserts the rows it needs and cleans up afterwards so test order
remains independent.
"""
import aiosqlite
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.main import app
from app.settings import settings
from app.services.compare_service import (
    _expand_link_id,
    _link_id_covers,
    _split_iast_and_translation,
    compare_url_for_hit,
    enumerate_verses,
    get_comparison,
)
from app.services.html_service import render_fragment

client = TestClient(app)


# ── Pure helper tests (no DB) ────────────────────────────────────────────────

def test_link_id_covers_exact_match():
    assert _link_id_covers("1.5", 1, 5)
    assert not _link_id_covers("1.5", 1, 6)
    assert not _link_id_covers("1.5", 2, 5)


def test_link_id_covers_range_match():
    assert _link_id_covers("1.3-6", 1, 3)
    assert _link_id_covers("1.3-6", 1, 5)
    assert _link_id_covers("1.3-6", 1, 6)
    assert not _link_id_covers("1.3-6", 1, 2)
    assert not _link_id_covers("1.3-6", 1, 7)
    assert not _link_id_covers("1.3-6", 2, 4)


def test_link_id_covers_rejects_malformed():
    assert not _link_id_covers("", 1, 1)
    assert not _link_id_covers("chapter_1", 1, 1)
    assert not _link_id_covers("Махабхарата (VI): 9", 1, 1)


def test_split_iast_separates_sanskrit_from_translation():
    line = (
        '<div class="citation_block" id="1.1">'
        '<div class="chapter_block iast">dharmakṣetre kurukṣetre</div>'
        '<div class="chapter_block translation">На поле дхармы</div>'
        '</div>'
    )
    iast, rest = _split_iast_and_translation(line)
    assert "dharmakṣetre" in iast
    assert "dharmakṣetre" not in rest
    assert "На поле дхармы" in rest


def test_split_iast_no_iast_returns_original():
    line = "<p>plain translation only</p>"
    iast, rest = _split_iast_and_translation(line)
    assert iast == ""
    assert rest == line


# ── compare_url_for_hit (reverse-routing for search-result cross-links) ──────

def test_compare_url_for_standalone_bhg_source():
    assert compare_url_for_hit("bhagavadgita-smirnov.html", "1.1") == "/compare/bhagavadgita/1.1"
    assert compare_url_for_hit("bhagavadgita-erman.html", "18.78") == "/compare/bhagavadgita/18.78"


def test_compare_url_for_yogasutra_and_shatakatraya():
    assert compare_url_for_hit("yoga-sutry_sharma.html", "2.46") == "/compare/yogasutra/2.46"
    assert compare_url_for_hit("shatakatrayam.html", "1.1") == "/compare/shatakatrayam/1.1"


def test_compare_url_for_mbh_bridge_applies_inverse_chapter_offset():
    # BhG 1.1 lives at Bhīṣma-parvan adhyāya 23.1 (config offset = 22).
    assert compare_url_for_hit("06_mahabharata-bhishmaparva.html", "23.1") == "/compare/bhagavadgita/1.1"
    # BhG 18.78 = Bhīṣma 40.78.
    assert compare_url_for_hit("06_mahabharata-bhishmaparva.html", "40.78") == "/compare/bhagavadgita/18.78"


def test_compare_url_for_mbh_outside_gita_chapters_returns_none():
    # Bhīṣma chapter 1 (book intro, before Gītā) → target chapter = -21.
    assert compare_url_for_hit("06_mahabharata-bhishmaparva.html", "1.1") is None
    # Bhīṣma chapter 22 (just before Gītā) → target chapter = 0.
    assert compare_url_for_hit("06_mahabharata-bhishmaparva.html", "22.1") is None
    # Bhīṣma chapter 50 (after Gītā 40) → target 28 > 18.
    assert compare_url_for_hit("06_mahabharata-bhishmaparva.html", "50.1") is None


def test_compare_url_uses_first_verse_of_range_merged_block():
    # A search hit landing on a merged "1.5-7" block links to the first verse.
    assert compare_url_for_hit("bhagavadgita-radha.html", "1.5-7") == "/compare/bhagavadgita/1.5"


def test_compare_url_returns_none_for_non_comparison_source():
    assert compare_url_for_hit("01_rigveda.html", "1.1") is None
    assert compare_url_for_hit("kama-sutra.html", "1.1") is None


def test_compare_url_returns_none_for_chapter_anchor_or_empty():
    assert compare_url_for_hit("bhagavadgita-smirnov.html", "chapter_1") is None
    assert compare_url_for_hit("bhagavadgita-smirnov.html", "") is None
    assert compare_url_for_hit("", "1.1") is None


# ── Search-result rendering integration: cross-link appears for eligible hits ─

def test_search_results_render_compare_link_for_eligible_source():
    # Mimic the dict shape that search_service.search_plain emits AFTER the
    # source_filename SQL addition. render_fragment enriches with compare_url
    # and renders the ⇔ button.
    results = [
        {
            "source_id": 101,
            "source_title": "Бхагавад-Гита (1977); Б. Л. Смирнов",
            "source_filename": "bhagavadgita-smirnov.html",
            "line_num": 5,
            "link_id": "1.1",
            "chapter": "Глава I",
            "line_html": "<div class='citation_block' id='1.1'>На поле дхармы</div>",
            "line_text": "На поле дхармы",
        }
    ]
    html = render_fragment("дхарма", results)
    assert 'href="/compare/bhagavadgita/1.1"' in html
    assert "⇔ переводы" in html


def test_search_results_render_compare_link_for_mbh_bridge_hit():
    # A hit in MBh Bhīṣma-parvan at link_id="23.1" should cross-link to
    # /compare/bhagavadgita/1.1 — letting users pivot from Erman's prose
    # rendering to the 14-way BhG comparison.
    results = [
        {
            "source_id": 204,
            "source_title": "Махабхарата VI (2009); В.Г. Эрман",
            "source_filename": "06_mahabharata-bhishmaparva.html",
            "line_num": 158,
            "link_id": "23.1",
            "chapter": "",
            "line_html": "<div class='citation_block'>Дхритараштра сказал</div>",
            "line_text": "Дхритараштра сказал",
        }
    ]
    html = render_fragment("дхритараштра", results)
    assert 'href="/compare/bhagavadgita/1.1"' in html


def test_search_results_omit_compare_link_for_non_eligible_source():
    # Ṛgveda is not in compare_config → no compare link rendered.
    results = [
        {
            "source_id": 1,
            "source_title": "Ригведа. Мандала I",
            "source_filename": "01_rigveda.html",
            "line_num": 1,
            "link_id": "1.1.1",
            "chapter": "",
            "line_html": "<div>agnimīḷe purohitaṃ</div>",
            "line_text": "agnimīḷe purohitaṃ",
        }
    ]
    html = render_fragment("agni", results)
    assert "/compare/" not in html
    assert "⇔ переводы" not in html


def test_search_results_omit_compare_link_when_source_filename_missing():
    # Defensive: results lacking source_filename (e.g. from legacy code paths)
    # must not crash and must not surface a misrouted link.
    results = [
        {
            "source_id": 1,
            "source_title": "Some source",
            # source_filename intentionally absent
            "line_num": 1,
            "link_id": "1.1",
            "chapter": "",
            "line_html": "<div>text</div>",
            "line_text": "text",
        }
    ]
    html = render_fragment("text", results)
    assert "/compare/" not in html


# ── Fixture: seed BhG-style sources ───────────────────────────────────────────

@pytest_asyncio.fixture
async def bhg_db():
    """Insert BhG-style sources matching compare_config filenames, then clean up.

    The session test_db only has source1/source2 — comparison config requires
    specific filenames. This fixture adds them just for compare tests.
    """
    db = await aiosqlite.connect(settings.DB_PATH)
    db.row_factory = aiosqlite.Row
    # Source ids chosen high to avoid collision with conftest seed (1, 2).
    fixtures = [
        (101, "bhagavadgita-smirnov.html", "Бхагавад-Гита (1977); Б. Л. Смирнов"),
        (102, "bhagavadgita-erman.html",   "Бхагавад-Гита (2009); В. Г. Эрман"),
        (103, "bhagavadgita-radha.html",   "Бхагавадгита (2016); Р.Т. Блиндерман"),
        (104, "06_mahabharata-bhishmaparva.html", "Махабхарата VI (2009); В.Г. Эрман"),
    ]
    for sid, fname, title in fixtures:
        await db.execute(
            "INSERT INTO sources (id, filename, title, sort_order) VALUES (?, ?, ?, ?)",
            (sid, fname, title, sid),
        )

    # Smirnov has Gītā 1.1 with both Sanskrit IAST and Russian translation.
    await db.execute("""
        INSERT INTO corpus_lines (line_text, line_html, source_id, line_num, link_id, chapter)
        VALUES (
            'dharmakshetre Дхритараштра сказал На поле дхармы',
            '<div class="citation_block" id="1.1"><div class="chapter_block iast">dharmakṣetre kurukṣetre</div><div class="chapter_block translation">Дхритараштра сказал: На поле дхармы.</div></div>',
            101, 5, '1.1', 'Глава I'
        )
    """)
    # Erman BhG 1.1
    await db.execute("""
        INSERT INTO corpus_lines (line_text, line_html, source_id, line_num, link_id, chapter)
        VALUES (
            'Что сделали мои и Пандавы',
            '<div class="citation_block" id="1.1">На поле дхармы, на поле Куру что сделали мои и Пандавы.</div>',
            102, 3, '1.1', 'Глава I'
        )
    """)
    # Radha (Blinderman) merges verses 1.5-1.7 into a single block keyed 1.5.
    await db.execute("""
        INSERT INTO corpus_lines (line_text, line_html, source_id, line_num, link_id, chapter)
        VALUES (
            'merged 5 6 7',
            '<div class="citation_block" id="1.5-7">objединённый блок стихов 5-7</div>',
            103, 8, '1.5-7', 'Глава I'
        )
    """)
    # MBh Bhīṣma-parvan 23.1 = Gītā 1.1 (chapter_offset=22 in config).
    await db.execute("""
        INSERT INTO corpus_lines (line_text, line_html, source_id, line_num, link_id, chapter)
        VALUES (
            'Дхритараштра сказал в Махабхарате',
            '<div class="citation_block">Дхритараштра сказал (Махабхарата VI.23.1).</div>',
            104, 158, '23.1', 'Глава 23'
        )
    """)
    await db.commit()
    await db.close()

    yield

    # Cleanup so other tests don't see these rows.
    db = await aiosqlite.connect(settings.DB_PATH)
    await db.execute("DELETE FROM corpus_lines WHERE source_id IN (101, 102, 103, 104)")
    await db.execute("DELETE FROM sources WHERE id IN (101, 102, 103, 104)")
    await db.commit()
    await db.close()


# ── Service-level tests ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_comparison_returns_hits_for_bhg_1_1(bhg_db):
    db = await aiosqlite.connect(settings.DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        result = await get_comparison(db, "bhagavadgita", 1, 1)
    finally:
        await db.close()

    assert result is not None
    assert result["chapter"] == 1
    assert result["verse"] == 1
    # Smirnov + Erman + MBh bridge (Radha doesn't have 1.1 — only 1.5-7).
    labels = [h.label for h in result["hits"]]
    assert "Смирнов 1977" in labels
    assert "Эрман 2009" in labels
    assert any("Махабхарата" in l for l in labels), "MBh bridge should surface"
    assert "Блиндерман 2016" not in labels
    # Canonical IAST extracted from Smirnov's iast block.
    assert "dharmakṣetre" in result["canonical_iast"]


@pytest.mark.asyncio
async def test_get_comparison_range_fallback_finds_radha_for_1_6(bhg_db):
    # Radha has only "1.5-7"; the lookup for 1.6 must find it via range fallback.
    db = await aiosqlite.connect(settings.DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        result = await get_comparison(db, "bhagavadgita", 1, 6)
    finally:
        await db.close()
    assert result is not None
    radha = [h for h in result["hits"] if h.label == "Блиндерман 2016"]
    assert len(radha) == 1
    assert radha[0].is_range_match is True
    assert radha[0].link_id == "1.5-7"


@pytest.mark.asyncio
async def test_get_comparison_unknown_work_returns_none(bhg_db):
    db = await aiosqlite.connect(settings.DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        result = await get_comparison(db, "ramayana", 1, 1)
    finally:
        await db.close()
    assert result is None


@pytest.mark.asyncio
async def test_get_comparison_chapter_out_of_range_returns_none(bhg_db):
    db = await aiosqlite.connect(settings.DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        result = await get_comparison(db, "bhagavadgita", 19, 1)  # BhG only has 18 chapters
    finally:
        await db.close()
    assert result is None


@pytest.mark.asyncio
async def test_get_comparison_unknown_verse_returns_none(bhg_db):
    # Chapter 1 exists in fixtures but verse 999 doesn't.
    db = await aiosqlite.connect(settings.DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        result = await get_comparison(db, "bhagavadgita", 1, 999)
    finally:
        await db.close()
    assert result is None


# ── HTTP-level tests ─────────────────────────────────────────────────────────

def test_route_renders_html_for_known_verse(bhg_db):
    r = client.get("/compare/bhagavadgita/1.1")
    assert r.status_code == 200
    assert "Бхагавадгита 1.1" in r.text
    assert "Смирнов" in r.text
    # JSON-LD present
    assert "application/ld+json" in r.text
    assert "WebPage" in r.text
    # Canonical link
    assert 'rel="canonical"' in r.text


def test_route_rejects_bad_verse_id_format():
    r = client.get("/compare/bhagavadgita/abc")
    assert r.status_code == 400


def test_route_rejects_range_in_url():
    # Canonical URLs are single verses; ranges are an internal concept only.
    r = client.get("/compare/bhagavadgita/1.3-6")
    assert r.status_code == 400


def test_route_rejects_unknown_work():
    r = client.get("/compare/ramayana/1.1")
    assert r.status_code == 404


def test_route_404_for_chapter_out_of_range():
    r = client.get("/compare/bhagavadgita/99.1")
    assert r.status_code == 404


def test_route_404_for_unknown_verse_with_no_data(bhg_db):
    r = client.get("/compare/bhagavadgita/2.500")
    assert r.status_code == 404


def test_route_rejects_oversized_verse_id():
    r = client.get("/compare/bhagavadgita/" + "1" * 20)
    assert r.status_code == 400


# ── _expand_link_id helper ───────────────────────────────────────────────────

def test_expand_link_id_exact():
    assert list(_expand_link_id("1.5")) == [(1, 5)]


def test_expand_link_id_range_inclusive():
    assert list(_expand_link_id("1.3-6")) == [(1, 3), (1, 4), (1, 5), (1, 6)]


def test_expand_link_id_single_verse_range():
    assert list(_expand_link_id("2.10-10")) == [(2, 10)]


def test_expand_link_id_inverted_range_yields_nothing():
    # Defensive: malformed "1.7-3" must not yield negative-range pairs.
    assert list(_expand_link_id("1.7-3")) == []


def test_expand_link_id_non_verse_anchors_yield_nothing():
    assert list(_expand_link_id("chapter_1")) == []
    assert list(_expand_link_id("")) == []
    assert list(_expand_link_id("Махабхарата (VI): 9")) == []


# ── enumerate_verses (per-work verse aggregation) ────────────────────────────

@pytest.mark.asyncio
async def test_enumerate_verses_aggregates_across_sources_and_expands_ranges(bhg_db):
    db = await aiosqlite.connect(settings.DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        verses = await enumerate_verses(db, "bhagavadgita")
    finally:
        await db.close()
    # Fixtures inserted: Smirnov 1.1, Erman 1.1, Radha 1.5-7 (→ 1.5/1.6/1.7),
    # MBh Bhīṣma 23.1 (→ Gītā 1.1).
    assert (1, 1) in verses
    assert (1, 5) in verses
    assert (1, 6) in verses
    assert (1, 7) in verses
    # No verse from fixtures lands outside chapter 1.
    assert all(ch == 1 for ch, _ in verses)


@pytest.mark.asyncio
async def test_enumerate_verses_drops_out_of_range_bridge_chapters(bhg_db):
    # Insert a Bhīṣma row at link_id="1.1" (book intro, BEFORE the Gītā).
    db = await aiosqlite.connect(settings.DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        await db.execute(
            "INSERT INTO corpus_lines (line_text, line_html, source_id, line_num, link_id, chapter) "
            "VALUES ('intro', '<div>intro</div>', 104, 10, '1.1', '')"
        )
        await db.commit()
        verses = await enumerate_verses(db, "bhagavadgita")
        # 1.1 + (-22) = -21, must be dropped.
        # No way to assert "absent" precisely, but the MBh's own 23.1 hit
        # already adds (1,1); the pre-Gītā 1.1 must not have created (-21,1).
        assert all(ch >= 1 for ch, _ in verses)
        assert (-21, 1) not in verses
    finally:
        # Clean up the extra row
        await db.execute("DELETE FROM corpus_lines WHERE source_id = 104 AND link_id = '1.1' AND line_num = 10")
        await db.commit()
        await db.close()


@pytest.mark.asyncio
async def test_enumerate_verses_unknown_work_returns_empty():
    db = await aiosqlite.connect(settings.DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        verses = await enumerate_verses(db, "ramayana")
    finally:
        await db.close()
    assert verses == []


# ── /compare/{work_slug} index route ─────────────────────────────────────────

def test_index_route_renders_work_hub(bhg_db):
    r = client.get("/compare/bhagavadgita")
    assert r.status_code == 200
    assert "Бхагавадгита" in r.text
    # All 18 chapter sections rendered, even empty ones.
    assert "Глава 1" in r.text
    assert "Глава 18" in r.text
    # Chapter 1 has the four fixture verses; verify their links are emitted.
    assert "/compare/bhagavadgita/1.1" in r.text
    assert "/compare/bhagavadgita/1.5" in r.text
    assert "/compare/bhagavadgita/1.6" in r.text
    assert "/compare/bhagavadgita/1.7" in r.text
    # JSON-LD ItemList present
    assert "ItemList" in r.text
    # Canonical link
    assert 'rel="canonical"' in r.text


def test_index_route_unknown_work_returns_404():
    r = client.get("/compare/ramayana")
    assert r.status_code == 404


def test_index_route_for_yogasutra_renders_without_fixture_data():
    # No fixtures for yogasutra, but route should still serve the hub with all
    # 4 chapters and empty verse grids.
    r = client.get("/compare/yogasutra")
    assert r.status_code == 200
    assert "Йога-сутры" in r.text
    assert "Глава 4" in r.text
    # Empty-chapter messaging surfaces somewhere on the page.
    assert "пока не доступны" in r.text


# ── /sitemap.xml includes compare hub + leaf URLs ────────────────────────────

def test_sitemap_includes_compare_hub_pages_for_each_work(bhg_db):
    r = client.get("/sitemap.xml")
    assert r.status_code == 200
    body = r.text
    for slug in ("bhagavadgita", "yogasutra", "shatakatrayam"):
        assert f"/compare/{slug}<" in body, f"hub for {slug} missing"


def test_sitemap_includes_leaf_compare_urls_from_fixtures(bhg_db):
    r = client.get("/sitemap.xml")
    body = r.text
    # bhg_db seeded BhG 1.1 plus the 1.5-7 range — all four should appear.
    for path in ("/compare/bhagavadgita/1.1<", "/compare/bhagavadgita/1.5<",
                 "/compare/bhagavadgita/1.6<", "/compare/bhagavadgita/1.7<"):
        assert path in body, f"missing leaf URL {path}"
