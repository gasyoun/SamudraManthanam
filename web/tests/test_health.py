import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.settings import settings
from app.state_db import init_state_db
import aiosqlite

client = TestClient(app)

def test_health_ok(test_db):
    # test_db fixture already sets settings.DB_PATH
    # We need a state_db too for full 'ok'
    # Actually conftest.py doesn't set STATE_DB_PATH
    pass

@pytest.mark.asyncio
async def test_health_logic(test_db, tmp_path):
    # Test with both DBs OK
    state_db_path = str(tmp_path / "state_health.db")
    settings.STATE_DB_PATH = state_db_path
    async with aiosqlite.connect(state_db_path) as db:
        await init_state_db(db)
    
    # settings.DB_PATH is set by test_db fixture
    
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["corpus_db"]["ok"] is True
    assert data["corpus_db"]["source_count"] > 0
    assert data["state_db"]["ok"] is True

@pytest.mark.asyncio
async def test_health_degraded_missing_corpus(tmp_path):
    settings.DB_PATH = str(tmp_path / "nonexistent_corpus.db")
    settings.STATE_DB_PATH = "" # Not configured
    
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["corpus_db"]["ok"] is False
    assert data["state_db"]["ok"] is False
