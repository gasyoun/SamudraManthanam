"""Tests for the word-of-the-day feature (H4955).

Two layers:
1. `pick_entry` / two-date dry-run — no-repeat guarantee, pure logic + a
   real generate() run against tmp state/pool files (the handoff's required
   "two-date dry-run producing distinct entries" evidence).
2. HTTP routing — the widget page renders all required fields from a
   precomputed static record, with no live DB query.
"""
import json
import random
import sqlite3
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from word_of_day_generate import generate, pick_entry  # noqa: E402

from app.main import app
from app.routers import word_of_day as word_of_day_router

client = TestClient(app)

SAMPLE_POOL = [
    {"entry_id": "koch:a", "slp1": "a", "iast": "a", "devanagari": "अ",
     "gloss": "first letter", "pos": "", "source": "Кочергина"},
    {"entry_id": "koch:b", "slp1": "b", "iast": "b", "devanagari": "ब",
     "gloss": "second", "pos": "m.", "source": "Кочергина"},
    {"entry_id": "koch:c", "slp1": "c", "iast": "c", "devanagari": "च",
     "gloss": "third", "pos": "", "source": "Кочергина"},
]


# ── pick_entry (pure logic) ──────────────────────────────────────────────

def test_pick_entry_excludes_shown():
    rng = random.Random(0)
    picked, reset = pick_entry(SAMPLE_POOL, {"koch:a", "koch:b"}, rng)
    assert picked["entry_id"] == "koch:c"
    assert reset is False


def test_pick_entry_resets_cycle_when_pool_exhausted():
    rng = random.Random(0)
    all_ids = {e["entry_id"] for e in SAMPLE_POOL}
    picked, reset = pick_entry(SAMPLE_POOL, all_ids, rng)
    assert reset is True
    assert picked["entry_id"] in all_ids


# ── generate() two-date dry run (required evidence) ─────────────────────

@pytest.fixture
def wod_env(tmp_path):
    pool_path = tmp_path / "pool.jsonl"
    with pool_path.open("w", encoding="utf-8") as f:
        for e in SAMPLE_POOL:
            f.write(json.dumps(e) + "\n")

    state_db = str(tmp_path / "state.db")
    corpus_db = str(tmp_path / "corpus.db")
    # Empty corpus DB (no corpus_lines table) — exercises the graceful
    # example-lookup fallback the spec requires.
    sqlite3.connect(corpus_db).close()

    out_path = tmp_path / "current.json"
    return pool_path, state_db, corpus_db, out_path


def test_two_consecutive_dates_produce_distinct_entries(wod_env):
    pool_path, state_db, corpus_db, out_path = wod_env

    rec1 = generate("2026-09-16", pool_path, state_db, corpus_db, out_path, rng=random.Random(1))
    rec2 = generate("2026-09-17", pool_path, state_db, corpus_db, out_path, rng=random.Random(1))

    assert rec1["entry_id"] != rec2["entry_id"]
    assert rec1["example"] is None  # no corpus_lines table -> graceful fallback
    assert out_path.exists()


def test_no_repeat_until_pool_cycles(wod_env):
    pool_path, state_db, corpus_db, out_path = wod_env

    seen = []
    for i, date in enumerate(["2026-09-16", "2026-09-17", "2026-09-18"]):
        rec = generate(date, pool_path, state_db, corpus_db, out_path, rng=random.Random(i))
        seen.append(rec["entry_id"])
    assert len(set(seen)) == len(SAMPLE_POOL)  # full pool shown, no repeats

    # 4th draw exhausts the 3-entry pool -> cycle reset, may repeat.
    rec4 = generate("2026-09-19", pool_path, state_db, corpus_db, out_path, rng=random.Random(99))
    assert rec4["cycle_reset"] is True


# ── find_example translation lookup ──────────────────────────────────────

def test_find_example_pairs_adjacent_cyrillic_line_as_translation(tmp_path):
    from word_of_day_generate import find_example

    corpus_db = str(tmp_path / "corpus.db")
    conn = sqlite3.connect(corpus_db)
    conn.execute("CREATE TABLE sources (id INTEGER PRIMARY KEY, filename TEXT, title TEXT)")
    conn.execute("INSERT INTO sources (id, filename, title) VALUES (1, 'f.html', 'Source 1')")
    conn.execute("""
        CREATE VIRTUAL TABLE corpus_lines USING fts5(
            line_text, line_html UNINDEXED, source_id UNINDEXED,
            line_num UNINDEXED, link_id UNINDEXED, chapter UNINDEXED
        )
    """)
    conn.execute(
        "INSERT INTO corpus_lines (line_text, line_html, source_id, line_num) "
        "VALUES ('idam rUpam vihAyASu', '', 1, 1)"
    )
    conn.execute(
        "INSERT INTO corpus_lines (line_text, line_html, source_id, line_num) "
        "VALUES ('Ты лишишься прежнего облика', '', 1, 2)"
    )
    conn.commit()
    conn.close()

    entry = {"iast": "idaṁ-rūpa", "devanagari": "इदंरूप"}
    result = find_example(corpus_db, entry)

    assert result is not None
    assert result["translation"] == "Ты лишишься прежнего облика"


def test_find_example_skips_translation_across_source_boundary(tmp_path):
    from word_of_day_generate import find_example

    corpus_db = str(tmp_path / "corpus.db")
    conn = sqlite3.connect(corpus_db)
    conn.execute("CREATE TABLE sources (id INTEGER PRIMARY KEY, filename TEXT, title TEXT)")
    conn.execute("INSERT INTO sources (id, filename, title) VALUES (1, 'a.html', 'A')")
    conn.execute("INSERT INTO sources (id, filename, title) VALUES (2, 'b.html', 'B')")
    conn.execute("""
        CREATE VIRTUAL TABLE corpus_lines USING fts5(
            line_text, line_html UNINDEXED, source_id UNINDEXED,
            line_num UNINDEXED, link_id UNINDEXED, chapter UNINDEXED
        )
    """)
    conn.execute(
        "INSERT INTO corpus_lines (line_text, line_html, source_id, line_num) "
        "VALUES ('idam rUpam', '', 1, 1)"
    )
    # Next rowid belongs to a DIFFERENT source — must not be paired even
    # though it is Cyrillic text.
    conn.execute(
        "INSERT INTO corpus_lines (line_text, line_html, source_id, line_num) "
        "VALUES ('Привет из другого источника', '', 2, 1)"
    )
    conn.commit()
    conn.close()

    entry = {"iast": "idaṁ-rūpa", "devanagari": "इदंरूप"}
    result = find_example(corpus_db, entry)

    assert result is not None
    assert "translation" not in result


def test_find_example_skips_translation_for_dictionary_self_match(tmp_path):
    """Dictionary sources index one headword per row (already Russian-gloss
    text) — the 'next row' there is the next unrelated headword, not a
    translation. Regression for a real false-positive on prod: 'tripuropaniṣad'
    got 'tri-puruṣa' attached as a bogus 'translation'."""
    from word_of_day_generate import find_example

    corpus_db = str(tmp_path / "corpus.db")
    conn = sqlite3.connect(corpus_db)
    conn.execute("CREATE TABLE sources (id INTEGER PRIMARY KEY, filename TEXT, title TEXT)")
    conn.execute("INSERT INTO sources (id, filename, title) VALUES (1, 'k.html', 'kochergina')")
    conn.execute("""
        CREATE VIRTUAL TABLE corpus_lines USING fts5(
            line_text, line_html UNINDEXED, source_id UNINDEXED,
            line_num UNINDEXED, link_id UNINDEXED, chapter UNINDEXED
        )
    """)
    conn.execute(
        "INSERT INTO corpus_lines (line_text, line_html, source_id, line_num) "
        "VALUES ('tripuropaniSad f. one of the Upanishads назв. одной из Упанишад', '', 1, 1)"
    )
    conn.execute(
        "INSERT INTO corpus_lines (line_text, line_html, source_id, line_num) "
        "VALUES ('tripuruSa n. три поколения', '', 1, 2)"
    )
    conn.commit()
    conn.close()

    entry = {"iast": "tripuropaniṣad", "devanagari": "त्रिपुरोपनिषद्"}
    result = find_example(corpus_db, entry)

    assert result is not None
    assert "translation" not in result


# ── HTTP routing ──────────────────────────────────────────────────────────

@pytest.fixture
def widget_record(tmp_path, monkeypatch):
    record = {
        "date": "2026-09-16",
        "entry_id": "koch:dharma",
        "slp1": "Darma",
        "iast": "dharma",
        "devanagari": "धर्म",
        "gloss": "закон, долг, добродетель",
        "pos": "m.",
        "source": "Кочергина В. А., Санскритско-русский словарь",
        "example": {"text": "dharme sthitaḥ", "source": "Bhagavad Gita"},
        "cycle_reset": False,
    }
    record_path = tmp_path / "current.json"
    record_path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(word_of_day_router, "RECORD_PATH", record_path)
    return record


def test_widget_page_renders_all_required_fields(widget_record):
    resp = client.get("/word-of-day")
    assert resp.status_code == 200
    body = resp.text
    for field in ("धर्म", "dharma", "закон, долг, добродетель", "m.", "dharme sthitaḥ", "Bhagavad Gita"):
        assert field in body, f"missing {field!r} in rendered page"


def test_api_word_of_day_returns_record(widget_record):
    resp = client.get("/api/word-of-day")
    assert resp.status_code == 200
    data = resp.json()
    assert data["iast"] == "dharma"
    assert data["devanagari"] == "धर्म"


def test_widget_page_before_generation_shows_empty_state(tmp_path, monkeypatch):
    monkeypatch.setattr(word_of_day_router, "RECORD_PATH", tmp_path / "missing.json")
    resp = client.get("/word-of-day")
    assert resp.status_code == 200
    assert "ещё не сгенерировано" in resp.text
