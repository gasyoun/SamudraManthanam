from fastapi import APIRouter, Depends, HTTPException
from typing import List
import os
from app.db import get_db
from app.models import SourceInfo

router = APIRouter(prefix="/api/sources", tags=["sources"])

# Get DB path from environment or default
DB_PATH = os.environ.get("DB_PATH", "corpus.db")

@router.get("", response_model=List[SourceInfo])
async def get_sources():
    db = await get_db(DB_PATH)
    try:
        async with db.execute("SELECT id, filename, title, sort_order FROM sources ORDER BY sort_order") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    finally:
        await db.close()
