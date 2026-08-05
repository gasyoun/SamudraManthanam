from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import datetime
import hashlib
import logging
import aiosqlite
from app.services.session_service import (
    SESSION_COOKIE,
    SESSION_TTL_DAYS,
    create_verification_challenge,
    redeem_verification,
)
from app.settings import settings
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
        # H1926 C4: the internal users.id is NOT returned. It is a database
        # primary key, not a capability — echoing it to an anonymous caller
        # publishes the account sequence and invites clients to treat a guessed
        # integer as identity. Nothing in the lead flow needs it.
        return {"status": "success"}
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        logger.exception("identity.lead failed for email=%s", lead.email)
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        await db.close()


class VerificationRequest(BaseModel):
    email: EmailStr


class VerificationConfirm(BaseModel):
    token: str = Field(..., min_length=8, max_length=256)


@router.post("/verify/request", status_code=202)
async def post_verify_request(payload: VerificationRequest):
    """Mint a single-use verification challenge for an address (H1926 C6).

    The response is identical whether or not the address has an account, so
    this endpoint cannot be used to enumerate users. See
    web/IDENTITY_TRUST_CONTRACT.md § Delivery for why the token is returned in
    non-production and logged in production rather than emailed: message
    delivery is out of scope for this lane and is not faked.
    """
    try:
        db = await get_state_db()
    except Exception:
        logger.exception("identity.verify: failed to open state DB")
        raise HTTPException(status_code=503, detail="Identity service unavailable")
    if not db:
        raise HTTPException(status_code=503, detail="Identity service unavailable")

    try:
        token = await create_verification_challenge(db, payload.email)
        response: dict = {"status": "accepted"}
        if token:
            if settings.APP_ENV == "production":
                logger.info(
                    "identity.verify: challenge issued for %s "
                    "(no mailer configured — relay manually)",
                    payload.email,
                )
            else:
                response["verification_token"] = token
        return response
    finally:
        await db.close()


@router.post("/verify/confirm")
async def post_verify_confirm(payload: VerificationConfirm, response: Response):
    """Redeem a challenge token for a session.

    A rejected token gets one undifferentiated 400: distinguishing expired from
    unknown from already-redeemed tells an attacker which guess was closer.
    """
    try:
        db = await get_state_db()
    except Exception:
        logger.exception("identity.verify_confirm: failed to open state DB")
        raise HTTPException(status_code=503, detail="Identity service unavailable")
    if not db:
        raise HTTPException(status_code=503, detail="Identity service unavailable")

    try:
        redeemed = await redeem_verification(db, payload.token)
        if not redeemed:
            raise HTTPException(status_code=400, detail="Invalid or expired token")
        session, session_token = redeemed
        response.set_cookie(
            SESSION_COOKIE,
            session_token,
            max_age=SESSION_TTL_DAYS * 24 * 3600,
            httponly=True,
            samesite="lax",
            secure=settings.APP_ENV == "production",
        )
        # Returned once so non-browser clients (scripts, the desktop app) can
        # send it back in X-Session-Token; only its hash is stored server-side.
        return {
            "status": "verified",
            "session_token": session_token,
            "expires_at": session.expires_at,
        }
    finally:
        await db.close()
