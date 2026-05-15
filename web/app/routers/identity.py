from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from typing import Optional
import datetime
import hashlib
import logging
import aiosqlite
from app.state_db import get_state_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/identity", tags=["identity"])

class LeadRequest(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    telegram_username: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    consent_data: bool
    consent_marketing: bool

@router.post("/lead")
async def post_lead(request: Request, lead: LeadRequest):
    try:
        db = await get_state_db()
    except Exception:
        logger.exception("identity.lead: failed to open state DB")
        raise HTTPException(status_code=503, detail="Identity service unavailable")
    if not db:
        raise HTTPException(status_code=503, detail="Identity service unavailable")

    try:
        now = datetime.datetime.now().isoformat()
        # Use client host for IP hash (truncated for privacy)
        client_host = request.client.host if request.client else "unknown"
        ip_hash = hashlib.sha256(client_host.encode()).hexdigest()[:16]

        # 1. Store/Update User. UTM fields are write-once (first-touch attribution);
        #    telegram_username is overwritten on each submit if provided.
        try:
            await db.execute(
                """INSERT INTO users
                   (email, name, telegram_username, utm_source, utm_medium, utm_campaign, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (lead.email, lead.name, lead.telegram_username,
                 lead.utm_source, lead.utm_medium, lead.utm_campaign, now)
            )
        except aiosqlite.IntegrityError:
            await db.execute(
                """UPDATE users
                   SET name = COALESCE(?, name),
                       telegram_username = COALESCE(?, telegram_username)
                   WHERE email = ?""",
                (lead.name, lead.telegram_username, lead.email)
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
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        logger.exception("identity.lead failed for email=%s", lead.email)
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        await db.close()
