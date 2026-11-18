"""H7790 — dictionary layer UI tests.

Builds a private fixture corpus.db carrying the five dict sources with
REAL sample lines from the corpus jsonl (the mojibake-repaired shapes),
then exercises the dict routes end-to-end: landing page, per-dict
alphabet index, headword entry page, Devanagari/IAST/SLP1 lookup and the
reverse RU→Sa gloss search with dict badges.
"""
import json
import sqlite3

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402
from app.settings import settings  # noqa: E402

FRISH_LINE = "/देव/\t/deva/\t/deva/\t/дэва/\tdeva m.; бог, божество"
FRISH_MOJI_LINE = "/акампитa/\t/ākampita/\t/Akampita/\t/акампита/\tākampita (pp. < kamp) ; дрожащий"
KOCH_LINE = "°आख्यायिन् /-ākhyāyin/ сообщающий или рассказывающий что-л."
KOSS_LINE = "22 अब्दशत /abdaśata/ /abdazata/ /абдашата/ <i>abda-śata</i>, <i>ср</i>. (-<i>tam</i>), столѣтіе."
KNAUER_LINE = "अंश\t/aṃśa/\t/aMza/\t/анша/\taṅśa m. часть, доля; S. 2, 26 наслѣдственная доля.\tс. 193"
SMIR_LINE = "СВАСТИ\tsvasti\tsvasti\t(Б-г)\t(II-2) XI, 21; ж. р. счастье, удача;"

SOURCES = [
    ("frish", "Фриш", FRISH_LINE),
    ("kochergina", "Кочергина", KOCH_LINE),
    ("kossovich", "Коссович", KOSS_LINE),
    ("knauer", "Кнауэр", KNAUER_LINE),
    ("slovar-smirnova", "Смирнов", SMIR_LINE),
]


@pytest_asyncio.fixture
async def dict_db(tmp_path_factory):
    db_path = str(tmp_path_factory.mktemp("dict") / "dict_corpus.db")
    import aiosqlite
    from app.db import create_schema

    db = await aiosqlite.connect(db_path)
    await create_schema(db)
    for i, (slug, title, line) in enumerate(SOURCES, start=1):
        await db.execute(
            "INSERT INTO sources (id, filename, title, sort_order, slug) "
            "VALUES (?, ?, ?, ?, ?)", (i, f"{slug}.jsonl", title, i, slug))
        await db.execute(
            "INSERT INTO corpus_lines (line_text, line_html, source_id, "
            "line_num, link_id, chapter, canonical_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (line, line, i, i, f"{slug}:e1", "", f"{slug}:e1"),
        )
    await db.commit()
    await db.close()
    yield db_path
    try:
        os.remove(db_path)
    except OSError:
        pass


@pytest_asyncio.fixture
async def client(dict_db, monkeypatch):
    # point the app at the dict fixture db for the duration of each test
    monkeypatch.setattr(settings, "DB_PATH", dict_db)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_dict_landing_lists_all_five(client):
    r = await client.get("/slovari")
    assert r.status_code == 200
    for needle in ("Фриш", "Кочергина", "Коссович", "Кнауэр", "Смирнов"):
        assert needle in r.text, needle
    # every dict card is available with an entry count
    assert "Скоро в корпусе" not in r.text


@pytest.mark.asyncio
async def test_dict_page_alphabet_index(client):
    r = await client.get("/slovari/frish")
    assert r.status_code == 200
    assert "Алфавитный указатель" in r.text
    assert "записей" in r.text


@pytest.mark.asyncio
async def test_frish_letter_page_and_entry_page(client):
    r = await client.get("/slovari/frish/a/d")
    assert r.status_code == 200
    assert "deva" in r.text
    # entry page by SLP1 slug
    r2 = await client.get("/slovari/frish/deva")
    assert r2.status_code == 200
    assert "देव" in r2.text
    assert "бог" in r2.text


@pytest.mark.asyncio
async def test_lookup_accepts_devanagari(client):
    r = await client.get("/slovari/lookup", params={"q": "देव"})
    # exact single match → 303 redirect to the entry page
    assert r.status_code == 303
    assert r.headers["location"].endswith("/slovari/frish/deva")


@pytest.mark.asyncio
async def test_lookup_accepts_iast_and_slp1(client):
    r = await client.get("/slovari/lookup", params={"q": "deva"})
    assert r.status_code in (200, 303)
    if r.status_code == 303:
        assert "/slovari/frish/deva" in r.headers["location"]
    else:
        assert "deva" in r.text


@pytest.mark.asyncio
async def test_reverse_ru_search_returns_badged_cards(client):
    r = await client.get("/slovari/ru/бог")
    assert r.status_code == 200
    assert "deva" in r.text
    assert "Фриш" in r.text  # dict badge on the card


@pytest.mark.asyncio
async def test_reverse_ru_search_no_result(client):
    r = await client.get("/slovari/ru/экзистенциальный")
    assert r.status_code == 200
    assert "не найдено" in r.text


@pytest.mark.asyncio
async def test_slovari_not_swallowed_by_search_catchall(client):
    """/slovari must win over /s/{query:path} (router order pin)."""
    r = await client.get("/slovari/frish")
    assert r.status_code == 200
    assert "Фриш" in r.text


@pytest.mark.asyncio
async def test_entry_404_unknown_headword(client):
    r = await client.get("/slovari/frish/zzzznotaword")
    assert r.status_code == 404
