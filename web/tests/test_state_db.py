import pytest
import aiosqlite
import os
from app.state_db import init_state_db, get_state_db
from app.settings import settings

@pytest.mark.asyncio
async def test_init_state_db_idempotent(tmp_path):
    db_path = str(tmp_path / "state.db")
    settings.STATE_DB_PATH = db_path
    
    # First init
    db = await aiosqlite.connect(db_path)
    await init_state_db(db)
    
    # Check tables exist
    async with db.execute("SELECT name FROM sqlite_master WHERE type='table'") as cursor:
        tables = [row[0] for row in await cursor.fetchall()]
        assert "migrations" in tables
        assert "morph_cache" in tables
    
    # Second init (idempotency check)
    await init_state_db(db)
    
    # Should still be fine
    async with db.execute("SELECT name FROM sqlite_master WHERE type='table'") as cursor:
        tables = [row[0] for row in await cursor.fetchall()]
        assert "migrations" in tables
        assert "morph_cache" in tables
        
    await db.close()

@pytest.mark.asyncio
async def test_get_state_db_none_if_no_path():
    settings.STATE_DB_PATH = ""
    db = await get_state_db()
    assert db is None
