import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.settings import settings
import httpx
from unittest.mock import AsyncMock, patch

client = TestClient(app)

def test_ai_explain_unconfigured():
    settings.AI_BASE_URL = ""
    response = client.post("/api/ai/explain", json={
        "query": "arjuna",
        "context_lines": ["line 1", "line 2"]
    })
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]

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
