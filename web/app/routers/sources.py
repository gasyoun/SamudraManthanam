from fastapi import APIRouter, Depends, HTTPException
from typing import List
import os
from app.db import get_db
from app.models import SourceInfo

from app.settings import settings

router = APIRouter(prefix="/api/sources", tags=["sources"])

@router.get("", response_model=List[SourceInfo])
async def get_sources():
    db = await get_db(settings.DB_PATH)
    try:
        async with db.execute(
            "SELECT id, filename, title, sort_order, slug, "
            "title_en, subtitle, credit, credit_role, imprint, publisher, year "
            "FROM sources ORDER BY sort_order"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    finally:
        await db.close()
