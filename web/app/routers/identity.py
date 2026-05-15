from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from typing import Optional
import datetime
import hashlib
import aiosqlite
from app.state_db import get_state_db

router = APIRouter(prefix="/api/identity", tags=["identity"])

class LeadRequest(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    consent_data: bool
    consent_marketing: bool

@router.post("/lead")
async def post_lead(request: Request, lead: LeadRequest):
    db = await get_state_db()
    if not db:
        raise HTTPException(status_code=503, detail="Identity service unavailable")
        
    try:
        now = datetime.datetime.now().isoformat()
        # Use client host for IP hash (truncated for privacy)
        client_host = request.client.host if request.client else "unknown"
        ip_hash = hashlib.sha256(client_host.encode()).hexdigest()[:16]
        
        # 1. Store/Update User
        # Note: SQLite doesn't have ON CONFLICT DO UPDATE in all versions, 
        # but modern ones used by aiosqlite usually do.
        try:
            await db.execute(
                "INSERT INTO users (email, name, created_at) VALUES (?, ?, ?)",
                (lead.email, lead.name, now)
            )
        except aiosqlite.IntegrityError:
            await db.execute(
                "UPDATE users SET name = ? WHERE email = ?",
                (lead.name, lead.email)
            )
        
        # Get user id
        async with db.execute("SELECT id FROM users WHERE email = ?", (lead.email,)) as cursor:
            user = await cursor.fetchone()
            user_id = user[0]
            
        # 2. Store Consents
        await db.execute(
            "INSERT INTO consent (user_id, consent_type, granted, timestamp, ip_hash) VALUES (?, ?, ?, ?, ?)",
            (user_id, "data", 1 if lead.consent_data else 0, now, ip_hash)
        )
        await db.execute(
            "INSERT INTO consent (user_id, consent_type, granted, timestamp, ip_hash) VALUES (?, ?, ?, ?, ?)",
            (user_id, "marketing", 1 if lead.consent_marketing else 0, now, ip_hash)
        )
        
        await db.commit()
        return {"status": "success", "user_id": user_id}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await db.close()
