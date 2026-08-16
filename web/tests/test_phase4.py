import os

import aiosqlite
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.services.session_service import SESSION_HEADER
from app.settings import settings
from app.state_db import init_state_db
import httpx
from unittest.mock import AsyncMock, patch

client = TestClient(app)


@pytest_asyncio.fixture(autouse=True)
async def state_db(tmp_path):
    """Every /api/ai/* route now resolves a session against state.db (H2772)."""
    db_path = str(tmp_path / "state_phase4.db")
    old_path = settings.STATE_DB_PATH
    settings.STATE_DB_PATH = db_path
    async with aiosqlite.connect(db_path) as db:
        await init_state_db(db)
    yield db_path
    settings.STATE_DB_PATH = old_path
    if os.path.exists(db_path):
        os.remove(db_path)


def _auth_headers(email="ai-tester@example.com") -> dict:
    """Run the real two-step verification loop and return session headers.

    `verification_token` is only echoed back when APP_ENV != "production"
    (identity.py) — force dev mode for the exchange regardless of what an
    earlier test in the same process left `settings.APP_ENV` as.
    """
    old_env = settings.APP_ENV
    settings.APP_ENV = "development"
    try:
        r = client.post(
            "/api/identity/lead",
            json={"email": email, "consent_data": True, "consent_marketing": False},
        )
        assert r.status_code == 200
        requested = client.post("/api/identity/verify/request", json={"email": email})
        assert requested.status_code == 202
        token = requested.json()["verification_token"]
        confirmed = client.post("/api/identity/verify/confirm", json={"token": token})
        assert confirmed.status_code == 200
        return {SESSION_HEADER: confirmed.json()["session_token"]}
    finally:
        settings.APP_ENV = old_env


def test_ai_explain_requires_auth():
    """Unauthenticated callers are rejected before ever reaching the provider
    (H2772) — the routes must not be reachable with no session at all."""
    response = client.post("/api/ai/explain", json={
        "query": "arjuna",
        "context_lines": ["line 1"]
    })
    assert response.status_code == 401


def test_ai_explain_unconfigured(ai_policy_allowed):
    # Policy allowed (fixture) but no provider endpoint — the "AI_BASE_URL is
    # empty" branch, distinct from an H2866 policy rejection.
    settings.AI_BASE_URL = ""
    # Force dev mode so the test sees the verbose "not configured" message;
    # otherwise an earlier CORS test may have left APP_ENV in production.
    old_env = settings.APP_ENV
    settings.APP_ENV = "development"
    try:
        response = client.post("/api/ai/explain", json={
            "query": "arjuna",
            "context_lines": ["line 1", "line 2"]
        }, headers=_auth_headers())
        assert response.status_code == 503
        assert "not configured" in response.json()["detail"]
    finally:
        settings.APP_ENV = old_env


# ── Input bounds on /api/ai/explain (abuse prevention) ────────────────────────

def test_ai_explain_rejects_excessive_context_lines():
    """Hard cap on context_lines count keeps the AI-provider bill bounded."""
    response = client.post("/api/ai/explain", json={
        "query": "arjuna",
        "context_lines": ["x"] * 1000,  # well above MAX_CONTEXT_LINES=50
    }, headers=_auth_headers())
    assert response.status_code == 422


def test_ai_explain_rejects_oversized_single_line():
    """Per-line length cap prevents megabyte-sized lines from one item."""
    response = client.post("/api/ai/explain", json={
        "query": "arjuna",
        "context_lines": ["x" * 10_000],  # above MAX_CONTEXT_LINE_LEN=2000
    }, headers=_auth_headers())
    assert response.status_code == 422


# ── Input bounds on /api/corrections/propose ──────────────────────────────────

def test_correction_propose_rejects_megabyte_payload():
    """state.db must not be filled with multi-megabyte text fields by anonymous callers."""
    response = client.post("/api/corrections/propose", json={
        "source_id": 1,
        "line_num": 1,
        "old_text": "a" * 100_000,
        "new_text": "b",
    })
    assert response.status_code == 422


def test_correction_propose_rejects_empty_text():
    """Empty old_text/new_text would be valueless noise in the corrections table."""
    response = client.post("/api/corrections/propose", json={
        "source_id": 1,
        "line_num": 1,
        "old_text": "",
        "new_text": "fix",
    })
    assert response.status_code == 422


# ── Input bounds on /api/morph/{word} ─────────────────────────────────────────

def test_morph_rejects_oversized_word():
    """A megabyte-sized word in the path must be rejected before reaching the
    external Sanskrit Heritage API."""
    response = client.get("/api/morph/" + "a" * 5000)
    assert response.status_code == 422


# ── ingest source_count reflects actual rows, not manifest length ─────────────

def test_ingest_source_count_matches_actual_rows(tmp_path):
    """Regression: ingest used to record len(filenames) as source_count, which
    overstated reality when files were skipped. It must now read the actual
    sources table row count."""
    import asyncio
    import sqlite3
    from ingest.ingest import ingest

    # Build a tiny corpus where one file in the manifest is missing on disk
    corpus = tmp_path / "corpus"
    (corpus / "Programdata").mkdir(parents=True)
    (corpus / "Data").mkdir()
    (corpus / "Programdata" / "data.txt").write_text(
        "present.html\nmissing.html\n", encoding="utf-8"
    )
    (corpus / "Data" / "present.html").write_text(
        "<!-- Present -->\n<p>some text</p>\n", encoding="utf-8"
    )
    jsonl_dir = tmp_path / "jsonl"
    jsonl_dir.mkdir()
    (jsonl_dir / "present.jsonl").write_text(
        '{"id":"present:p1","passage":"p1","seq":1,'
        '"text":"some text","html":"<p>some text</p>","chapter":""}\n',
        encoding="utf-8",
    )

    db_path = str(tmp_path / "test_corpus.db")
    asyncio.run(ingest(str(corpus), db_path, str(jsonl_dir)))

    con = sqlite3.connect(db_path)
    try:
        actual_rows = con.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        recorded = con.execute(
            "SELECT value FROM corpus_meta WHERE key = 'source_count'"
        ).fetchone()[0]
    finally:
        con.close()

    assert actual_rows == 1  # manifest had 2 but one was skipped
    assert recorded == "1"   # source_count must reflect reality, not the manifest

@pytest.mark.asyncio
async def test_ai_service_call_mocked(ai_policy_allowed):
    settings.AI_BASE_URL = "https://api.openai.com/v1"
    settings.AI_API_KEY = "sk-test"
    
    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    mock_res = httpx.Response(200, json={
        "choices": [{"message": {"content": "Mocked success"}}],
        "model": "gpt-3.5-turbo"
    }, request=req)
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_res
        
        # Using synchronous client since we are mocking the underlying httpx call
        response = client.post("/api/ai/explain", json={
            "query": "test",
            "context_lines": ["ctx"]
        }, headers=_auth_headers())
    
    assert response.status_code == 200
    assert response.json()["explanation"] == "Mocked success"
