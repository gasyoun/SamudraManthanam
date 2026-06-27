import logging
from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel, Field
from typing import Optional, List
import datetime
from app.state_db import get_state_db
from app.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/corrections", tags=["corrections"])


async def _open_state_db():
    """Open state.db with a clean 503 on configuration / connection failure.
    Mirrors the pattern in identity.py — avoids leaking raw aiosqlite tracebacks."""
    try:
        db = await get_state_db()
    except Exception:
        logger.exception("corrections: failed to open state DB")
        raise HTTPException(status_code=503, detail="State service unavailable")
    if not db:
        raise HTTPException(status_code=503, detail="State service unavailable")
    return db

class CorrectionProposal(BaseModel):
    source_id: int = Field(..., ge=1)
    line_num: int = Field(..., ge=1)
    old_text: str = Field(..., min_length=1, max_length=10000)
    new_text: str = Field(..., min_length=1, max_length=10000)
    email: Optional[str] = Field(None, max_length=320)  # RFC 5321 max email length

@router.post("/propose")
async def propose_correction(proposal: CorrectionProposal):
    db = await _open_state_db()
    try:
        now = datetime.datetime.now().isoformat()
        user_id = None
        if proposal.email:
            async with db.execute("SELECT id FROM users WHERE email = ?", (proposal.email,)) as cursor:
                user = await cursor.fetchone()
                if user:
                    user_id = user[0]
                    
        await db.execute(
            """INSERT INTO corrections 
               (source_id, line_num, old_text, new_text, user_id, created_at) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (proposal.source_id, proposal.line_num, proposal.old_text, proposal.new_text, user_id, now)
        )
        await db.commit()
        return {"status": "success"}
    finally:
        await db.close()

@router.get("/pending")
async def get_pending_corrections(key: str = Query("")):
    if not settings.ADMIN_SECRET_KEY or key != settings.ADMIN_SECRET_KEY:
        if settings.APP_ENV != "development" or key != "dev":
            raise HTTPException(status_code=403, detail="Forbidden")
    try:
        db = await get_state_db()
    except Exception:
        logger.exception("corrections.pending: failed to open state DB")
        return []
    if not db:
        return []
    try:
        async with db.execute("SELECT * FROM corrections WHERE status = 'pending'") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
    finally:
        await db.close()
