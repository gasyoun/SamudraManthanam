import aiosqlite
import pytest

from app.db import create_schema


async def _table_names(db):
    async with db.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ) as cur:
        rows = await cur.fetchall()
    return {row[0] for row in rows}


@pytest.mark.asyncio
async def test_fresh_schema_has_no_morph_cache(tmp_path):
    db_path = str(tmp_path / "fresh.db")
    db = await aiosqlite.connect(db_path)
    try:
        await create_schema(db)
        assert "morph_cache" not in await _table_names(db)
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_create_schema_drops_existing_morph_cache(tmp_path):
    db_path = str(tmp_path / "legacy.db")
    db = await aiosqlite.connect(db_path)
    try:
        await db.execute(
            "CREATE TABLE morph_cache (query TEXT PRIMARY KEY, stems TEXT NOT NULL)"
        )
        await db.commit()
        assert "morph_cache" in await _table_names(db)

        await create_schema(db)
        assert "morph_cache" not in await _table_names(db)
    finally:
        await db.close()
