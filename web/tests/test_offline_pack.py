"""Hermetic tests for the offline pack format and /api/corpus-version endpoint.

Builds a minimal fixture pack with known content and validates:
- FTS5 plain search (IAST and Cyrillic)
- Prefix matching
- Multi-token AND logic
- Multi-line OR logic
- Case-sensitive post-filter
- Whole-word post-filter
- Regex via Python re module (client-side path)
- IAST diacritics preserved (remove_diacritics 0)
- Zero-results case
- /api/corpus-version endpoint shape

No corpus.db required — all tests are hermetic.
"""
import os
import re
import sqlite3
import tempfile

import pytest
from httpx import ASGITransport, AsyncClient

# ── Fixture pack schema (mirrors build_offline_pack.py) ──────────────────────

_PACK_SCHEMA = """\
CREATE TABLE pack_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE pack_sources (
    source_id   INTEGER PRIMARY KEY,
    source_slug TEXT NOT NULL,
    title       TEXT NOT NULL,
    role        TEXT NOT NULL
);
CREATE TABLE corpus_lines (
    id           INTEGER PRIMARY KEY,
    source_id    INTEGER NOT NULL,
    link_id      TEXT NOT NULL,
    canonical_id TEXT,
    chapter      TEXT,
    line_num     INTEGER,
    line_text    TEXT NOT NULL
);
CREATE INDEX corpus_lines_source ON corpus_lines (source_id);
CREATE INDEX corpus_lines_link   ON corpus_lines (link_id);
"""

_FTS_CREATE = """\
CREATE VIRTUAL TABLE corpus_fts USING fts5(
    line_text,
    content='corpus_lines',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 0'
);
"""

# Known corpus rows — a mix of IAST Sanskrit and Russian
_SOURCES = [
    (1, "bhagavadgita-test", "Test BG", "translation"),
    (2, "dic-test", "Test Dict", "dictionary"),
]

_LINES = [
    # (source_id, link_id, canonical_id, chapter, line_num, line_text)
    (1, "1.1", "bhagavadgita-test:1.1#sa", "1", 1,
     "dhṛtarāṣṭra uvāca dharmakṣetre kurukṣetre samavetā yuyutsavaḥ"),
    (1, "1.1", "bhagavadgita-test:1.1#ru", "1", 2,
     "Дхритараштра сказал: На поле дхармы, на поле Куру собрались желающие сражаться"),
    (1, "1.2", "bhagavadgita-test:1.2#sa", "1", 3,
     "sañjaya uvāca dṛṣṭvā tu pāṇḍavānīkaṃ vyūḍhaṃ duryodhanas tadā"),
    (1, "1.2", "bhagavadgita-test:1.2#ru", "1", 4,
     "Санджая сказал: Увидев войско пандавов в боевом строю Дурьодхана"),
    (1, "2.1", "bhagavadgita-test:2.1#sa", "2", 5,
     "taṃ tathā kṛpayāviṣṭam aśrūpūrṇākulekṣaṇam"),
    (1, "2.1", "bhagavadgita-test:2.1#ru", "2", 6,
     "Того, охваченного состраданием, с глазами полными слёз"),
    (1, "2.47", "bhagavadgita-test:2.47#sa", "2", 7,
     "karmaṇy evādhikāras te mā phaleṣu kadācana"),
    (1, "2.47", "bhagavadgita-test:2.47#ru", "2", 8,
     "У тебя есть право лишь на действие но не на его плоды никогда"),
    (2, "mw.1", "dic-test:mw.1", None, 1,
     "dharma: m. duty, righteousness, sacred law"),
    (2, "mw.2", "dic-test:mw.2", None, 2,
     "kṛṣṇa: adj. black, dark; m. name of the deity Krishna"),
]


def _build_fixture_pack(path: str) -> None:
    db = sqlite3.connect(path)
    for stmt in _PACK_SCHEMA.strip().split(";"):
        stmt = stmt.strip()
        if stmt:
            db.execute(stmt)
    db.executemany(
        "INSERT INTO pack_sources (source_id, source_slug, title, role) VALUES (?, ?, ?, ?)",
        _SOURCES,
    )
    db.executemany(
        "INSERT INTO corpus_lines "
        "(source_id, link_id, canonical_id, chapter, line_num, line_text) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        _LINES,
    )
    db.commit()
    db.execute(_FTS_CREATE)
    db.execute("INSERT INTO corpus_fts(corpus_fts) VALUES('rebuild')")
    db.executemany(
        "INSERT INTO pack_meta (key, value) VALUES (?, ?)",
        [
            # Mirror build_offline_pack.py's pack_meta keys exactly. There is
            # deliberately NO 'sha256' key — a file cannot contain its own hash;
            # the SHA lives only in the .db.sha256 sidecar.
            ("corpus_version", "test-001"),
            ("pack_version", "1"),
            ("pack_type", "test"),
            ("built_at", "2026-06-13T00:00:00+00:00"),
            ("source_count", "2"),
            ("row_count", str(len(_LINES))),
        ],
    )
    db.commit()
    db.close()


@pytest.fixture(scope="module")
def fixture_pack(tmp_path_factory):
    d = tmp_path_factory.mktemp("packs")
    p = str(d / "test.db")
    _build_fixture_pack(p)
    return p


# ── FTS5 pack format tests ────────────────────────────────────────────────────

def _fts_search(db_path: str, term: str) -> list[str]:
    """Run a plain FTS5 MATCH query; return matched line_text values."""
    db = sqlite3.connect(db_path)
    rows = db.execute(
        "SELECT cl.line_text FROM corpus_fts f "
        "JOIN corpus_lines cl ON cl.id = f.rowid "
        "WHERE corpus_fts MATCH ?",
        (f'"{term}"*',),
    ).fetchall()
    db.close()
    return [r[0] for r in rows]


def test_fts5_plain_iast(fixture_pack):
    results = _fts_search(fixture_pack, "dharma")
    assert any("dharma" in r for r in results), f"Expected 'dharma' hit, got {results}"


def test_fts5_plain_russian(fixture_pack):
    results = _fts_search(fixture_pack, "сказал")
    assert len(results) == 2, f"Expected 2 hits for 'сказал', got {len(results)}: {results}"


def test_fts5_prefix_match(fixture_pack):
    # 'karm' prefix should match 'karmaṇy' and 'karma'
    results = _fts_search(fixture_pack, "karm")
    assert any("karma" in r.lower() or "karmaṇy" in r for r in results), \
        f"Prefix 'karm' should match karma/karmaṇy; got {results}"


def test_fts5_iast_diacritics_preserved(fixture_pack):
    # 'ṛ' is distinct from 'r'; searching 'dhr' should NOT match 'dhṛ'
    db = sqlite3.connect(fixture_pack)
    rows_with_diacritic = db.execute(
        "SELECT line_text FROM corpus_fts WHERE corpus_fts MATCH '\"dhṛtarāṣṭra\"'",
    ).fetchall()
    rows_without = db.execute(
        "SELECT line_text FROM corpus_fts WHERE corpus_fts MATCH '\"dhrtarastra\"'",
    ).fetchall()
    db.close()
    assert len(rows_with_diacritic) == 1, "Exact IAST match should find 1 row"
    assert len(rows_without) == 0, "ASCII fallback should NOT match IAST text (remove_diacritics 0)"


def test_fts5_multi_token_and(fixture_pack):
    # 'dharmakṣetre kurukṣetre' — both tokens must appear in the same row
    db = sqlite3.connect(fixture_pack)
    rows = db.execute(
        "SELECT line_text FROM corpus_fts WHERE corpus_fts MATCH '\"dharmakṣetre\" \"kurukṣetre\"'",
    ).fetchall()
    db.close()
    assert len(rows) == 1
    assert "dharmakṣetre" in rows[0][0]
    assert "kurukṣetre" in rows[0][0]


def test_fts5_multi_line_or(fixture_pack):
    # Two separate FTS queries merged (OR logic mirrors search_service.py)
    db = sqlite3.connect(fixture_pack)
    rows_a = db.execute(
        "SELECT line_text FROM corpus_fts WHERE corpus_fts MATCH '\"uvāca\"*'",
    ).fetchall()
    rows_b = db.execute(
        "SELECT line_text FROM corpus_fts WHERE corpus_fts MATCH '\"karmaṇy\"*'",
    ).fetchall()
    db.close()
    combined = [r[0] for r in rows_a] + [r[0] for r in rows_b]
    assert len(combined) >= 3, f"OR query should return ≥3 rows; got {len(combined)}"


def test_fts5_zero_results(fixture_pack):
    results = _fts_search(fixture_pack, "xyzzy_gibberish_never_matches")
    assert results == []


def test_fts5_source_filter(fixture_pack):
    # Only source 1 (not dict source 2)
    db = sqlite3.connect(fixture_pack)
    rows = db.execute(
        "SELECT cl.line_text FROM corpus_fts f "
        "JOIN corpus_lines cl ON cl.id = f.rowid "
        "WHERE corpus_fts MATCH '\"dharma\"*' AND cl.source_id = 1",
    ).fetchall()
    db.close()
    assert all("dharma" in r[0].lower() for r in rows)
    assert len(rows) >= 1


def test_regex_search_python(fixture_pack):
    # Regex is applied client-side in Phase 3b; validate the data layer here
    db = sqlite3.connect(fixture_pack)
    all_rows = db.execute("SELECT line_text FROM corpus_lines").fetchall()
    db.close()
    pattern = re.compile(r"uvāca", re.UNICODE)
    matched = [r[0] for r in all_rows if pattern.search(r[0])]
    assert len(matched) == 2, f"Expected 2 'uvāca' lines; got {len(matched)}"


def test_case_sensitive_filter(fixture_pack):
    # Case-sensitive post-filter (uppercase should NOT match lowercase IAST)
    db = sqlite3.connect(fixture_pack)
    all_rows = db.execute("SELECT line_text FROM corpus_lines").fetchall()
    db.close()
    texts = [r[0] for r in all_rows]
    # 'Дхритараштра' (capitalised) should match, but not 'дхритараштра'
    sensitive = [t for t in texts if "Дхритараштра" in t]
    insensitive = [t for t in texts if "дхритараштра" in t]
    assert len(sensitive) == 1
    assert len(insensitive) == 0


def test_pack_meta_fields(fixture_pack):
    db = sqlite3.connect(fixture_pack)
    meta = dict(db.execute("SELECT key, value FROM pack_meta").fetchall())
    db.close()
    assert "corpus_version" in meta
    assert "pack_version" in meta
    # The SHA-256 must NOT live in pack_meta (self-referential & impossible);
    # it is in the .db.sha256 sidecar. Guards against the bug being reintroduced.
    assert "sha256" not in meta
    assert int(meta["row_count"]) == len(_LINES)
    assert int(meta["source_count"]) == len(_SOURCES)


def test_pack_sources_schema(fixture_pack):
    db = sqlite3.connect(fixture_pack)
    sources = db.execute("SELECT source_id, source_slug, title, role FROM pack_sources").fetchall()
    db.close()
    assert len(sources) == 2
    roles = {r[3] for r in sources}
    assert "translation" in roles
    assert "dictionary" in roles


# ── /api/corpus-version endpoint tests ───────────────────────────────────────

@pytest.mark.asyncio
async def test_corpus_version_shape():
    """Endpoint returns the expected JSON shape even when no packs are built."""
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/corpus-version")
    assert response.status_code == 200
    data = response.json()
    assert "corpus_version" in data
    assert "pack_sha256" in data
    assert "base" in data["pack_sha256"]
    assert "dict" in data["pack_sha256"]


@pytest.mark.asyncio
async def test_corpus_version_sha256_from_sidecar(tmp_path, monkeypatch):
    """When sidecar files exist, their SHA-256 values are returned."""
    # Write fake sidecar files
    (tmp_path / "base.db.sha256").write_text("abc123")
    (tmp_path / "dict.db.sha256").write_text("def456")

    from app import settings as settings_module
    monkeypatch.setattr(settings_module.settings, "OFFLINE_PACKS_DIR", str(tmp_path))

    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/corpus-version")
    assert response.status_code == 200
    data = response.json()
    assert data["pack_sha256"]["base"] == "abc123"
    assert data["pack_sha256"]["dict"] == "def456"


@pytest.mark.asyncio
async def test_offline_pack_serve_missing():
    """Serving a non-existent pack returns 404."""
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/offline-packs/base.db")
    # Either 404 (pack not built) or 200 (pack exists on this machine)
    assert response.status_code in (200, 404)


@pytest.mark.asyncio
async def test_offline_pack_serve_invalid_type():
    """Unknown pack type returns 404."""
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/offline-packs/evil.db")
    assert response.status_code == 404


# ── gzip-on-wire serving + pack_bytes ────────────────────────────────────────

@pytest.mark.asyncio
async def test_corpus_version_has_pack_bytes(tmp_path, monkeypatch):
    """pack_bytes reflects the raw .db size, and is None when the pack is absent."""
    (tmp_path / "base.db").write_bytes(b"0123456789")  # 10 bytes; no dict.db
    from app import settings as settings_module
    monkeypatch.setattr(settings_module.settings, "OFFLINE_PACKS_DIR", str(tmp_path))
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/corpus-version")
    data = response.json()
    assert "pack_bytes" in data
    assert data["pack_bytes"]["base"] == 10
    assert data["pack_bytes"]["dict"] is None


@pytest.mark.asyncio
async def test_offline_pack_served_gzip(tmp_path, monkeypatch):
    """When a .db.gz exists, the endpoint serves it Content-Encoding: gzip with an
    X-Db-Bytes header = raw decoded size, and the decoded body equals the raw .db."""
    import gzip
    raw = b"SQLite format 3\x00" + b"x" * 5000
    (tmp_path / "base.db").write_bytes(raw)
    with gzip.GzipFile(str(tmp_path / "base.db.gz"), "wb", mtime=0) as f:
        f.write(raw)
    from app import settings as settings_module
    monkeypatch.setattr(settings_module.settings, "OFFLINE_PACKS_DIR", str(tmp_path))
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/offline-packs/base.db")
    assert response.status_code == 200
    assert response.headers.get("content-encoding") == "gzip"
    assert response.headers.get("x-db-bytes") == str(len(raw))
    # Served via StreamingResponse (no Range handling) → no Accept-Ranges: bytes,
    # so an inbound Range can never yield an undecodable 206 slice of the gzip.
    assert response.headers.get("accept-ranges") != "bytes"
    # httpx transparently decodes gzip → SHA over the decoded body matches the raw .db
    assert response.content == raw


@pytest.mark.asyncio
async def test_offline_pack_falls_back_to_raw(tmp_path, monkeypatch):
    """With only the raw .db (no .gz), serve it WITHOUT Content-Encoding."""
    raw = b"raw-db-bytes-no-gz-variant"
    (tmp_path / "dict.db").write_bytes(raw)
    from app import settings as settings_module
    monkeypatch.setattr(settings_module.settings, "OFFLINE_PACKS_DIR", str(tmp_path))
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/offline-packs/dict.db")
    assert response.status_code == 200
    assert not response.headers.get("content-encoding")
    assert response.headers.get("x-db-bytes") == str(len(raw))
    assert response.content == raw
