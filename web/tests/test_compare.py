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
    _link_id_covers,
    _split_iast_and_translation,
    get_comparison,
)

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
