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
