import os
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.settings import settings
import aiosqlite
from app.state_db import init_state_db

client = TestClient(app)

@pytest_asyncio.fixture(autouse=True)
async def setup_state_db(tmp_path):
    db_path = str(tmp_path / "state_test_p3.db")
    settings.STATE_DB_PATH = db_path
    async with aiosqlite.connect(db_path) as db:
        await init_state_db(db)
    yield
    if os.path.exists(db_path):
        os.remove(db_path)

@pytest.mark.asyncio
async def test_identity_lead_success():
    response = client.post("/api/identity/lead", json={
        "email": "test@example.com",
        "name": "Test User",
        "consent_data": True,
        "consent_marketing": False
    })
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify persistence
    async with aiosqlite.connect(settings.STATE_DB_PATH) as db:
        async with db.execute("SELECT * FROM users WHERE email = 'test@example.com'") as cursor:
            user = await cursor.fetchone()
            assert user is not None
            assert user[2] == "Test User" # name

@pytest.mark.asyncio
async def test_identity_lead_invalid_email():
    response = client.post("/api/identity/lead", json={
        "email": "invalid-email",
        "consent_data": True,
        "consent_marketing": False
    })
    assert response.status_code == 422 # Pydantic validation error

@pytest.mark.asyncio
async def test_correction_proposal():
    # First create a user
    client.post("/api/identity/lead", json={
        "email": "corrector@example.com",
        "consent_data": True,
        "consent_marketing": True
    })
    
    response = client.post("/api/corrections/propose", json={
        "source_id": 1,
        "line_num": 10,
        "old_text": "old",
        "new_text": "new",
        "email": "corrector@example.com"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify pending
    response = client.get("/api/corrections/pending")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["new_text"] == "new"
    assert data[0]["status"] == "pending"
