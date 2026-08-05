"""The durable-reference inventory, as executable assertions (H1925, B1/B2).

``docs/DURABLE_REFERENCE_INVENTORY.md`` is the prose census; this file is the
half that fails when the code drifts from it. Criterion B1 is explicit that
*no retained reference may be omitted because it is currently unused by the
UI*, so every site in the inventory gets a test here — including the ones whose
verdict is "carries no corpus reference", which is asserted rather than assumed.
"""
import csv
import io
import sqlite3

import aiosqlite
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.canonical_refs import CANONICAL_TUPLE_FIELDS
from app.canonical_state_migrations import apply_migrations
from app.db import create_schema
from app.main import app
from app.models import SearchResult, SearchResultItem
from app.services.source_metadata import build_line_quotation
from app.settings import settings
from app.state_db import init_state_db
from canonical_fixtures import make_state

CORPUS_VERSION = "v2026.test"


@pytest_asyncio.fixture
async def canonical_corpus(tmp_path, monkeypatch):
    """A corpus DB whose lines carry canonical ids, wired into settings."""
    db_path = str(tmp_path / "canonical_corpus.db")
    db = await aiosqlite.connect(db_path)
    await create_schema(db)
    await db.execute(
        "INSERT INTO sources (id, filename, title, sort_order, slug) "
        # Filename must agree with the slug: the lifespan backfill re-derives
        # slugs from filenames, so a mismatched fixture would be overwritten.
        "VALUES (1, 'bhagavadgita-1909.html', 'Бхагавадгита', 1, 'bhagavadgita-1909')"
    )
    await db.execute(
        "INSERT INTO corpus_lines "
        "(line_text, line_html, source_id, line_num, link_id, chapter, canonical_id) "
        "VALUES ('dharmaksetre kuruksetre', '<p>dharmaksetre kuruksetre</p>', 1, 1, "
        "'1.1', 'Глава 1', 'bhagavadgita-1909:1.1')"
    )
    await db.execute(
        "INSERT INTO corpus_meta (key, value) VALUES ('corpus_version', ?)",
        (CORPUS_VERSION,),
    )
    await db.commit()
    await db.close()

    previous = settings.DB_PATH
    settings.DB_PATH = db_path
    yield db_path
    settings.DB_PATH = previous


async def _make_state_db(path: str) -> str:
    """Build a state DB through the real migration path.

    Not hand-rolled CREATE TABLEs: the correction route needs Lane C's
    rate-limit and audit tables plus Lane B's canonical columns, and a
    hand-written snapshot of that schema silently rots the moment either lane
    adds a table.
    """
    previous = settings.STATE_DB_PATH
    settings.STATE_DB_PATH = path
    try:
        db = await aiosqlite.connect(path)
        await init_state_db(db)
        await db.close()
    finally:
        settings.STATE_DB_PATH = previous
    return path


async def _client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ── 1. Search API ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_results_expose_the_canonical_tuple(canonical_corpus):
    async with await _client() as ac:
        r = await ac.post("/api/search", json={"query": "dharmaksetre", "mode": "plain"})
    assert r.status_code == 200
    data = r.json()
    assert data["corpus_version"] == CORPUS_VERSION
    hit = data["results"][0]
    assert hit["source_slug"] == "bhagavadgita-1909"
    assert hit["canonical_id"] == "bhagavadgita-1909:1.1"
    # Ordinals survive as compatibility fields (B6), they are just no longer alone.
    assert hit["source_id"] == 1 and hit["line_num"] == 1


@pytest.mark.asyncio
async def test_regex_and_morphological_share_the_search_projection(canonical_corpus):
    """Both alternative modes read through the same SELECT, so neither can
    silently serve results without canonical identity."""
    async with await _client() as ac:
        r = await ac.post("/api/search", json={"query": "dharma.*etre", "mode": "regex"})
    assert r.status_code == 200
    hit = r.json()["results"][0]
    assert hit["canonical_id"] == "bhagavadgita-1909:1.1"


def test_search_models_declare_every_tuple_member():
    assert {"source_slug", "canonical_id"} <= set(SearchResultItem.model_fields)
    assert "corpus_version" in SearchResult.model_fields
    assert set(CANONICAL_TUPLE_FIELDS) <= (
        set(SearchResultItem.model_fields) | set(SearchResult.model_fields)
    )


# ── 2. Context endpoint ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_context_endpoint_carries_identity(canonical_corpus):
    async with await _client() as ac:
        r = await ac.get("/api/search/context", params={"source_id": 1, "line_num": 1})
    assert r.status_code == 200
    data = r.json()
    assert data["corpus_version"] == CORPUS_VERSION
    assert data["current"]["canonical_id"] == "bhagavadgita-1909:1.1"
    assert data["current"]["source_slug"] == "bhagavadgita-1909"


# ── 3/4. Exports ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_json_export_rows_are_citable(canonical_corpus):
    async with await _client() as ac:
        r = await ac.get("/api/search/export", params={"query": "dharmaksetre", "format": "json"})
    assert r.status_code == 200
    payload = r.json()
    assert payload["metadata"]["corpus_version"] == CORPUS_VERSION
    row = payload["results"][0]
    assert row["source_slug"] == "bhagavadgita-1909"
    assert row["canonical_id"] == "bhagavadgita-1909:1.1"


@pytest.mark.asyncio
async def test_csv_export_rows_are_citable(canonical_corpus):
    async with await _client() as ac:
        r = await ac.get("/api/search/export", params={"query": "dharmaksetre", "format": "csv"})
    assert r.status_code == 200
    rows = list(csv.reader(io.StringIO(r.text)))
    header = next(row for row in rows if row and row[0] == "source_id")
    assert "source_slug" in header and "canonical_id" in header
    body = rows[rows.index(header) + 1]
    record = dict(zip(header, body))
    assert record["canonical_id"] == "bhagavadgita-1909:1.1"


# ── 5. Reader / citation path ───────────────────────────────────────────────


def test_citation_jsonld_carries_the_canonical_identifier():
    quotation = build_line_quotation(
        line={
            "line_num": 1,
            "link_id": "1.1",
            "line_text": "dharmaksetre kuruksetre",
            "canonical_id": "bhagavadgita-1909:1.1",
            "chapter": "Глава 1",
        },
        slug="bhagavadgita-1909",
        source_url="https://example.test/sources/bhagavadgita-1909",
        base_url="https://example.test",
    )
    assert quotation["identifier"] == "bhagavadgita-1909:1.1"


def test_reader_merge_preserves_the_passage_canonical_id():
    from app.routers.reader import _merge_jsonl_lines

    merged = _merge_jsonl_lines(
        [
            {
                "line_num": 1,
                "link_id": "1.1",
                "chapter": "Глава 1",
                "line_html": "<p>sa</p>",
                "line_text": "dharmaksetre",
                "canonical_id": "bhagavadgita-1909:1.1#sa",
            },
            {
                "line_num": 2,
                "link_id": "1.1",
                "chapter": "Глава 1",
                "line_html": "<p>ru</p>",
                "line_text": "На поле дхармы",
                "canonical_id": "bhagavadgita-1909:1.1#ru",
            },
        ]
    )
    assert len(merged) == 1
    # Segment suffix dropped: the citable unit is the passage, not the segment.
    assert merged[0]["canonical_id"] == "bhagavadgita-1909:1.1"


# ── 6. Corrections (state.db) ───────────────────────────────────────────────


def test_corrections_table_stores_the_canonical_tuple(tmp_path):
    path = make_state(tmp_path / "state.db")
    apply_migrations(path)
    conn = sqlite3.connect(path)
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(corrections)")}
    finally:
        conn.close()
    assert set(CANONICAL_TUPLE_FIELDS) <= cols
    assert "ref_status" in cols


@pytest.mark.asyncio
async def test_correction_written_via_the_api_is_stored_canonically(
    canonical_corpus, tmp_path
):
    state_path = str(tmp_path / "state_api.db")
    await _make_state_db(state_path)

    previous = settings.STATE_DB_PATH
    settings.STATE_DB_PATH = state_path
    try:
        async with await _client() as ac:
            r = await ac.post(
                "/api/corrections/propose",
                json={
                    "source_slug": "bhagavadgita-1909",
                    "canonical_id": "bhagavadgita-1909:1.1",
                    "old_text": "kuruksetre",
                    "new_text": "kurukṣetre",
                },
            )
        assert r.status_code == 200, r.text
        assert r.json()["reference"]["resolved_via"] == "canonical"

        conn = sqlite3.connect(state_path)
        conn.row_factory = sqlite3.Row
        row = dict(conn.execute("SELECT * FROM corrections").fetchone())
        conn.close()
        assert row["canonical_id"] == "bhagavadgita-1909:1.1"
        assert row["source_slug"] == "bhagavadgita-1909"
        assert row["corpus_version"] == CORPUS_VERSION
        # Ordinals are RESOLVED, not echoed from the request.
        assert (row["source_id"], row["line_num"]) == (1, 1)
    finally:
        settings.STATE_DB_PATH = previous


@pytest.mark.asyncio
async def test_legacy_correction_client_still_works(canonical_corpus, tmp_path):
    """B6: legacy records/clients remain usable during the compatibility span."""
    state_path = str(tmp_path / "state_legacy.db")
    await _make_state_db(state_path)

    previous = settings.STATE_DB_PATH
    settings.STATE_DB_PATH = state_path
    try:
        async with await _client() as ac:
            r = await ac.post(
                "/api/corrections/propose",
                json={
                    "source_id": 1,
                    "line_num": 1,
                    "old_text": "kuruksetre",
                    "new_text": "kurukṣetre",
                },
            )
        assert r.status_code == 200, r.text
        # Accepted through the legacy address, but STORED canonically.
        assert r.json()["reference"]["canonical_id"] == "bhagavadgita-1909:1.1"
    finally:
        settings.STATE_DB_PATH = previous


@pytest.mark.asyncio
async def test_correction_against_an_unknown_reference_is_refused(
    canonical_corpus, tmp_path
):
    state_path = str(tmp_path / "state_bad.db")
    await _make_state_db(state_path)

    previous = settings.STATE_DB_PATH
    settings.STATE_DB_PATH = state_path
    try:
        async with await _client() as ac:
            r = await ac.post(
                "/api/corrections/propose",
                json={
                    "source_slug": "bhagavadgita-1909",
                    "canonical_id": "bhagavadgita-1909:99.99",
                    "old_text": "x",
                    "new_text": "y",
                },
            )
        assert r.status_code == 409
        assert r.json()["detail"]["status"] == "orphan"

        # And an address-less proposal never reaches the resolver at all.
        async with await _client() as ac:
            r = await ac.post(
                "/api/corrections/propose", json={"old_text": "x", "new_text": "y"}
            )
        assert r.status_code == 422
    finally:
        settings.STATE_DB_PATH = previous


# ── 7. Offline payloads ─────────────────────────────────────────────────────


def test_offline_pack_schema_carries_canonical_identity():
    """Offline packs are a durable payload a user keeps on disk across rebuilds."""
    from pathlib import Path

    src = Path(__file__).resolve().parents[1] / "scripts" / "build_offline_pack.py"
    text = src.read_text(encoding="utf-8")
    assert "canonical_id" in text
    assert "source_slug" in text


# ── 8. Retained AI/cache data — asserted N/A, not assumed ───────────────────


@pytest.mark.asyncio
async def test_ai_cache_rows_hold_no_corpus_coordinates(tmp_path):
    """The inventory's one "carries no reference" verdict, made falsifiable.

    ``ai_cache`` is keyed by a hash of (system prompt, user prompt, model) and
    stores an opaque response payload — no source id, line number, slug or
    canonical id. If a future change adds corpus coordinates to this table, this
    test fails and the row must join the migration/zero-orphan path.
    """
    from app.state_db import init_state_db

    path = str(tmp_path / "state_ai.db")
    previous = settings.STATE_DB_PATH
    settings.STATE_DB_PATH = path
    try:
        db = await aiosqlite.connect(path)
        await init_state_db(db)
        async with db.execute("PRAGMA table_info(ai_cache)") as cur:
            cols = {r[1] for r in await cur.fetchall()}
        await db.close()
    finally:
        settings.STATE_DB_PATH = previous

    assert cols == {"request_hash", "task", "response", "model", "created_at", "latency_ms"}
    assert not ({"source_id", "line_num", "canonical_id", "source_slug"} & cols)
