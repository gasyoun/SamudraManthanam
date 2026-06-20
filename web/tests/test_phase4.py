import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.settings import settings
import httpx
from unittest.mock import AsyncMock, patch

client = TestClient(app)

def test_ai_explain_unconfigured():
    settings.AI_BASE_URL = ""
    # Force dev mode so the test sees the verbose "not configured" message;
    # otherwise an earlier CORS test may have left APP_ENV in production.
    old_env = settings.APP_ENV
    settings.APP_ENV = "development"
    try:
        response = client.post("/api/ai/explain", json={
            "query": "arjuna",
            "context_lines": ["line 1", "line 2"]
        })
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
    })
    assert response.status_code == 422


def test_ai_explain_rejects_oversized_single_line():
    """Per-line length cap prevents megabyte-sized lines from one item."""
    response = client.post("/api/ai/explain", json={
        "query": "arjuna",
        "context_lines": ["x" * 10_000],  # above MAX_CONTEXT_LINE_LEN=2000
    })
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
async def test_ai_service_call_mocked():
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
        })
    
    assert response.status_code == 200
    assert response.json()["explanation"] == "Mocked success"
