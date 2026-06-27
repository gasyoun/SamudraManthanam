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
async def test_identity_lead_persists_telegram_and_utm():
    """Telegram username + UTM params land in the users table."""
    response = client.post("/api/identity/lead", json={
        "email": "tg-user@example.com",
        "name": "Telegram User",
        "telegram_username": "@sanskritfan",
        "utm_source": "telegram",
        "utm_medium": "channel_post",
        "utm_campaign": "grammar_launch",
        "consent_data": True,
        "consent_marketing": True
    })
    assert response.status_code == 200

    async with aiosqlite.connect(settings.STATE_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT telegram_username, utm_source, utm_medium, utm_campaign FROM users WHERE email = 'tg-user@example.com'"
        ) as cursor:
            row = await cursor.fetchone()
            assert row is not None
            assert row["telegram_username"] == "@sanskritfan"
            assert row["utm_source"] == "telegram"
            assert row["utm_medium"] == "channel_post"
            assert row["utm_campaign"] == "grammar_launch"

@pytest.mark.asyncio
async def test_identity_lead_backwards_compat_omits_new_fields():
    """Old clients that don't send telegram/utm still succeed (fields are optional)."""
    response = client.post("/api/identity/lead", json={
        "email": "legacy@example.com",
        "consent_data": True,
        "consent_marketing": False
    })
    assert response.status_code == 200

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
    
    # Verify pending (dev key required). Restore APP_ENV to avoid leaking dev
    # mode into later tests that depend on production-mode behavior.
    old_env = settings.APP_ENV
    settings.APP_ENV = "development"
    try:
        response = client.get("/api/corrections/pending?key=dev")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["new_text"] == "new"
        assert data[0]["status"] == "pending"
    finally:
        settings.APP_ENV = old_env

@pytest.mark.asyncio
async def test_pending_corrections_rejects_missing_or_wrong_key():
    old_env = settings.APP_ENV
    old_admin_key = settings.ADMIN_SECRET_KEY
    settings.APP_ENV = "development"
    settings.ADMIN_SECRET_KEY = ""
    try:
        response = client.get("/api/corrections/pending")
        assert response.status_code == 403

        response = client.get("/api/corrections/pending?key=wrong")
        assert response.status_code == 403
    finally:
        settings.APP_ENV = old_env
        settings.ADMIN_SECRET_KEY = old_admin_key
