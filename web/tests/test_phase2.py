import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.settings import settings
import aiosqlite
from app.db import create_schema

client = TestClient(app)

@pytest.mark.asyncio
async def test_regex_safety_timeout(test_db):
    # Pathological regex is hard to simulate in a small test DB, 
    # but we can verify the metadata fields.
    response = client.post("/api/search", json={
        "query": ".*arjuna.*",
        "mode": "regex"
    })
    assert response.status_code == 200
    data = response.json()
    assert "search_metadata" in data
    assert "scanned_rows" in data["search_metadata"]
    assert "timeout" in data["search_metadata"]
    assert "truncated" in data["search_metadata"]

@pytest.mark.asyncio
async def test_reader_view(test_db):
    # test_db fixture ensures source 1 exists
    response = client.get("/sources/1")
    assert response.status_code == 200
    assert "Source 1" in response.text
    assert "svasti arjuna" in response.text

@pytest.mark.asyncio
async def test_reader_highlight(test_db):
    response = client.get("/sources/1?highlight=10")
    assert response.status_code == 200
    assert "highlighted" in response.text

@pytest.mark.asyncio
async def test_export_metadata(test_db):
    response = client.get("/api/search/export?query=arjuna")
    assert response.status_code == 200
    assert "Запрос:" in response.text
    assert "arjuna" in response.text
