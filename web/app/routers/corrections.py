from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
import datetime
from app.state_db import get_state_db

router = APIRouter(prefix="/api/corrections", tags=["corrections"])

class CorrectionProposal(BaseModel):
    source_id: int
    line_num: int
    old_text: str
    new_text: str
    email: Optional[str] = None # Link to user if available

@router.post("/propose")
async def propose_correction(proposal: CorrectionProposal):
    db = await get_state_db()
    if not db:
        raise HTTPException(status_code=503, detail="State service unavailable")
        
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
async def get_pending_corrections():
    db = await get_state_db()
    if not db:
        return []
    try:
        async with db.execute("SELECT * FROM corrections WHERE status = 'pending'") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
    finally:
        await db.close()
