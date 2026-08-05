"""Correction intake with separated anonymous and verified trust (H1926, C4/C6/C7).

Two properties have to hold at once here, and the pre-H1926 code held neither:

* **Anonymous proposals stay possible.** A reader who spots a typo in a verse
  should be able to say so without an account. They are accepted, marked
  low-trust, and rate-limited (C7).
* **Attribution requires proof.** The previous implementation resolved the
  ``email`` field of the request body against the users table and attached the
  matching account to the correction — so typing a known scholar's address was
  enough to file corrections under their name. Submitted email text is now
  stored as *contact information only*; the account link comes from a redeemed
  session (see app/services/session_service.py) or from nothing at all (C6).
"""

import datetime
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.security import require_admin
from app.services.rate_limit import (
    ANONYMOUS_CORRECTION_LIMIT,
    CORRECTION_WINDOW_SECONDS,
    VERIFIED_CORRECTION_LIMIT,
    check_and_consume,
    client_fingerprint,
)
from app.services.session_service import (
    TRUST_ANONYMOUS,
    TRUST_VERIFIED,
    resolve_session,
    session_token_from_request,
)
from app.state_db import get_state_db

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
    #: Optional contact address. Accepted as free text a reviewer may use to
    #: reply — it grants no attribution and no elevated capability (C6).
    email: Optional[str] = Field(None, max_length=320)  # RFC 5321 max email length
    #: Canonical corpus identity of the corrected line, when the client knows
    #: it. Recorded alongside the ordinal so the audit row survives a rebuild
    #: that renumbers lines.
    link_id: Optional[str] = Field(None, max_length=128)


@router.post("/propose")
async def propose_correction(proposal: CorrectionProposal, request: Request):
    db = await _open_state_db()
    try:
        now = datetime.datetime.now().isoformat()

        # Trust tier comes from a redeemed session and nothing else.
        session = await resolve_session(
            db, session_token_from_request(request.headers, request.cookies)
        )
        trust_tier = TRUST_VERIFIED if session else TRUST_ANONYMOUS
        user_id = session.user_id if session else None

        ip_hash = client_fingerprint(request.client.host if request.client else None)
        limit = (
            VERIFIED_CORRECTION_LIMIT if session else ANONYMOUS_CORRECTION_LIMIT
        )
        bucket_key = f"user:{session.user_id}" if session else f"ip:{ip_hash}"
        decision = await check_and_consume(
            db,
            bucket="corrections.propose",
            key=bucket_key,
            limit=limit,
            window_seconds=CORRECTION_WINDOW_SECONDS,
        )
        if not decision.allowed:
            raise HTTPException(
                status_code=429,
                detail="Too many correction proposals. Please try again later.",
                headers={"Retry-After": str(decision.retry_after_seconds)},
            )

        cursor = await db.execute(
            """INSERT INTO corrections
               (source_id, line_num, old_text, new_text, user_id, created_at,
                trust_tier, actor_ip_hash, contact_email, link_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                proposal.source_id,
                proposal.line_num,
                proposal.old_text,
                proposal.new_text,
                user_id,
                now,
                trust_tier,
                ip_hash,
                proposal.email,
                proposal.link_id,
            ),
        )
        correction_id = cursor.lastrowid
        await db.execute(
            """INSERT INTO correction_audit
               (correction_id, action, trust_tier, actor_user_id, actor_ip_hash,
                link_id, created_at)
               VALUES (?, 'proposed', ?, ?, ?, ?, ?)""",
            (correction_id, trust_tier, user_id, ip_hash, proposal.link_id, now),
        )
        await db.commit()
        return {
            "status": "success",
            "trust_tier": trust_tier,
            "remaining_today": decision.remaining,
        }
    finally:
        await db.close()


@router.get("/pending", dependencies=[Depends(require_admin)])
async def get_pending_corrections():
    """Review queue. Admin-only, header-authenticated (H1926 C3)."""
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
