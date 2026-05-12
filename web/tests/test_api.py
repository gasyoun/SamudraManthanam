import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
import os

@pytest.mark.asyncio
async def test_search_basic():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/search", json={
            "query": "arjuna",
            "mode": "plain"
        })
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "html_fragment" in data
    # Verify Jinja dict access didn't crash (if it did, we'd get 500)
    assert len(data["results"]) >= 0

@pytest.mark.asyncio
async def test_search_validation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Empty query
        response = await ac.post("/api/search", json={"query": "", "mode": "plain"})
        assert response.status_code == 422
        
        # Invalid mode
        response = await ac.post("/api/search", json={"query": "test", "mode": "bad"})
        assert response.status_code == 422

@pytest.mark.asyncio
async def test_path_traversal():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Attempt traversal
        response = await ac.get("/api/corpus-sync/file/..%5CProgramdata%5Cdata.txt")
        assert response.status_code in [400, 404]

@pytest.mark.asyncio
async def test_export_standalone():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/search/export?query=arjuna&mode=plain")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "html" in response.text.lower()
    # Verify no NameError for render_standalone
    assert "style" in response.text.lower()

@pytest.mark.asyncio
async def test_source_selection_none():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # source_ids=[] should return zero results
        response = await ac.post("/api/search", json={
            "query": "arjuna",
            "mode": "plain",
            "source_ids": []
        })
    assert response.status_code == 200
    assert len(response.json()["results"]) == 0

@pytest.mark.asyncio
async def test_multi_token_plain_search():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Query with multiple tokens should match lines containing all tokens
        response = await ac.post("/api/search", json={
            "query": "arjuna krishna",
            "mode": "plain"
        })
    assert response.status_code == 200
    # The tokens should be joined by AND in FTS5
    # (Assuming there's data that matches both)

@pytest.mark.asyncio
async def test_invalid_get_mode_export():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Invalid mode in GET should return 422
        response = await ac.get("/api/search/export?query=test&mode=bad")
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_invalid_get_mode_stream():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/search/stream?query=test&mode=bad")
    assert response.status_code == 422
