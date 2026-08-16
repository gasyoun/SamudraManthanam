import pytest
import httpx
from unittest.mock import AsyncMock, patch
from app.services.ai_service import explain_with_ai
from app.settings import settings

@pytest.mark.asyncio
async def test_explain_with_ai_service_mocked(ai_policy_allowed):
    settings.AI_BASE_URL = "http://local-ai"
    settings.AI_API_KEY = "test-key"
    
    # We use a dummy request to satisfy raise_for_status()
    req = httpx.Request("POST", "http://local-ai")
    mock_res = httpx.Response(200, json={
        "choices": [{"message": {"content": "Mocked success"}}],
        "model": "local-model"
    }, request=req)
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_res
        result = await explain_with_ai("test query", ["line 1"])
        
        assert "explanation" in result
        assert result["explanation"] == "Mocked success"

def test_placeholder():
    assert True
