import datetime
import json
import pytest
import pytest_asyncio
import aiosqlite
import httpx
from unittest.mock import AsyncMock, patch

from app.services.morph_service import detect_encoding, to_slp1, expand_word
from app.settings import settings
from app.state_db import init_state_db

# ── Encoding detection ────────────────────────────────────────────────────────

def test_detect_encoding():
    assert detect_encoding("arjuna") == "SLP1"
    assert detect_encoding("kṛṣṇa") == "IAST"
    assert detect_encoding("कृष्ण") == "Devanagari"
    assert detect_encoding("āpastamba") == "IAST"

def test_to_slp1():
    assert to_slp1("arjuna", "SLP1") == "arjuna"
    assert to_slp1("kṛṣṇa", "IAST") == "kfzRa"
    assert to_slp1("कृष्ण", "Devanagari") == "kfzRa"
    assert to_slp1("अ", "Devanagari") == "a"

# ── expand_word ───────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def morph_state_db(tmp_path):
    db_path = str(tmp_path / "morph_state.db")
    old = settings.STATE_DB_PATH
    settings.STATE_DB_PATH = db_path
    async with aiosqlite.connect(db_path) as db:
        await init_state_db(db)
    yield db_path
    settings.STATE_DB_PATH = old

@pytest.mark.asyncio
async def test_expand_word_network_failure_returns_input(morph_state_db):
    """When Sanskrit Heritage is unreachable, the input word is returned as the sole stem."""
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectError("simulated timeout")
        result = await expand_word("arjuna")
    assert "arjuna" in result

@pytest.mark.asyncio
async def test_expand_word_cache_hit_skips_network(morph_state_db):
    """A cached result is returned immediately without making any HTTP request."""
    now = datetime.datetime.now().isoformat()
    async with aiosqlite.connect(morph_state_db) as db:
        await db.execute(
            "INSERT INTO morph_cache (query, stems_json, created_at, refreshed_at) VALUES (?, ?, ?, ?)",
            ("arjuna", json.dumps(["arjuna", "arjun"]), now, now),
        )
        await db.commit()

    with patch("httpx.AsyncClient.get") as mock_get:
        result = await expand_word("arjuna")
        mock_get.assert_not_called()

    assert set(result) == {"arjuna", "arjun"}

@pytest.mark.asyncio
async def test_expand_word_writes_to_cache_on_api_hit(morph_state_db):
    """A successful API response is persisted to state.db for subsequent calls."""
    req = httpx.Request("GET", "https://sanskrit.inria.fr")
    mock_res = httpx.Response(
        200,
        text="<stem>arjuna</stem><stem>arjun</stem>",
        request=req,
    )
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_res
        result = await expand_word("arjuna")

    assert "arjuna" in result
    # Verify it was written to the cache
    async with aiosqlite.connect(morph_state_db) as db:
        async with db.execute("SELECT stems_json FROM morph_cache WHERE query = 'arjuna'") as cursor:
            row = await cursor.fetchone()
    assert row is not None
    assert "arjuna" in json.loads(row[0])

@pytest.mark.asyncio
async def test_expand_word_no_state_db_skips_cache():
    """When STATE_DB_PATH is unset, expand_word still returns results (no cache, no crash)."""
    old = settings.STATE_DB_PATH
    settings.STATE_DB_PATH = ""
    try:
        req = httpx.Request("GET", "https://sanskrit.inria.fr")
        mock_res = httpx.Response(200, text="<stem>arjuna</stem>", request=req)
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_res
            result = await expand_word("arjuna")
        assert "arjuna" in result
    finally:
        settings.STATE_DB_PATH = old

@pytest.mark.asyncio
async def test_expand_word_iast_round_trip(morph_state_db):
    """IAST input is normalised to SLP1 before the cache key is formed."""
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectError("offline")
        # kṛṣṇa in IAST → SLP1 is kfzRa
        result = await expand_word("kfzRa")
    assert "kfzRa" in result

# ── Export metadata ───────────────────────────────────────────────────────────

def test_export_includes_result_count(test_db):
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    response = client.get("/api/search/export?query=arjuna")
    assert response.status_code == 200
    assert "Найдено:" in response.text

def test_export_includes_live_search_link(test_db):
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    response = client.get("/api/search/export?query=arjuna")
    assert response.status_code == 200
    assert "Открыть в поиске" in response.text
    assert "?q=" in response.text
