import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_contract_prefix_matching():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 'arjun' should match 'arjuna'
        response = await ac.post("/api/search", json={
            "query": "arjun",
            "mode": "plain"
        })
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert any("arjuna" in item["line_text"].lower() for item in data["results"])

@pytest.mark.asyncio
async def test_contract_and_logic():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 'svasti arjuna' should match only lines with both
        response = await ac.post("/api/search", json={
            "query": "svasti arjuna",
            "mode": "plain"
        })
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    for item in data["results"]:
        text = item["line_text"].lower()
        assert "svasti" in text and "arjuna" in text

@pytest.mark.asyncio
async def test_contract_whole_word():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 'arjun' with whole_word=True should NOT match 'arjuna'
        response = await ac.post("/api/search", json={
            "query": "arjun",
            "mode": "plain",
            "whole_word": True
        })
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
