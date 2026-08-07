"""Correction intake: separated trust (H1926, C4/C6/C7) + durable identity (H1925, B4).

Two lanes meet in this file and both properties have to hold at once.

**Trust (Lane C).**

* **Anonymous proposals stay possible.** A reader who spots a typo in a verse
  should be able to say so without an account. They are accepted, marked
  low-trust, and rate-limited (C7).
* **Attribution requires proof.** The previous implementation resolved the
  ``email`` field of the request body against the users table and attached the
  matching account to the correction — so typing a known scholar's address was
  enough to file corrections under their name. Submitted email text is now
  stored as *contact information only*; the account link comes from a redeemed
  session (see app/services/session_service.py) or from nothing at all (C6).

**Identity (Lane B).** A correction outlives many corpus rebuilds, which makes
it the highest-risk durable reference in the system. The proposed line is
resolved against the live corpus *before* anything is stored, and the row keeps
the canonical tuple ``(source_slug, canonical_id, corpus_version)`` rather than
ordinals alone. A reference that cannot be resolved unambiguously is refused
with 409 — never parked against an ordinal that will mean a different verse
after the next ingest.
"""

import datetime
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, model_validator

from app.canonical_refs import DurableRef, resolve_one_async
from app.db import get_db
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
from app.settings import settings
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
    """A proposed correction, addressed by canonical tuple and/or legacy ordinals.

    Both address forms are accepted during the compatibility span (B4/B6):
    existing clients keep posting ``source_id``/``line_num``, newer ones post
    ``source_slug``/``canonical_id``. Whatever arrives, the stored row carries
    the canonical tuple — resolved, never guessed.
    """

    # Legacy ordinal pair — optional now that a canonical address exists.
    source_id: Optional[int] = Field(None, ge=1)
    line_num: Optional[int] = Field(None, ge=1)
    # Canonical address (H1925).
    source_slug: Optional[str] = Field(None, max_length=200)
    canonical_id: Optional[str] = Field(None, max_length=200)
    #: Which corpus the client was reading. Only meaningful for the legacy
    #: form, where it decides whether an ordinal may be bound at all.
    corpus_version: Optional[str] = Field(None, max_length=100)
    old_text: str = Field(..., min_length=1, max_length=10000)
    new_text: str = Field(..., min_length=1, max_length=10000)
    #: Optional contact address. Accepted as free text a reviewer may use to
    #: reply — it grants no attribution and no elevated capability (C6).
    email: Optional[str] = Field(None, max_length=320)  # RFC 5321 max email length
    #: Display anchor of the corrected line, when the client knows it. Kept for
    #: the audit trail; `canonical_id` above is the rebuild-surviving identity.
    link_id: Optional[str] = Field(None, max_length=128)

    @model_validator(mode="after")
    def require_an_address(self):
        has_canonical = bool(self.source_slug and self.canonical_id)
        has_legacy = self.source_id is not None and self.line_num is not None
        if not (has_canonical or has_legacy):
            raise ValueError(
                "a correction needs either (source_slug, canonical_id) or "
                "(source_id, line_num)"
            )
        return self


@router.post("/propose")
async def propose_correction(proposal: CorrectionProposal, request: Request):
    db = await _open_state_db()
    corpus_db = None
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

        # Identity resolution happens AFTER the rate-limit check on purpose: it
        # reads the corpus, and an unauthenticated caller must not be able to
        # drive corpus lookups past the bucket that exists to bound them.
        # Canonical-reference columns (0004/0005) are applied once at startup
        # by init_state_db → D1 runner (H2354); no per-request migration call.
        corpus_db = await get_db(settings.DB_PATH)
        resolution = await resolve_one_async(
            corpus_db,
            db,
            DurableRef(
                source_slug=proposal.source_slug,
                canonical_id=proposal.canonical_id,
                corpus_version=proposal.corpus_version,
                source_id=proposal.source_id,
                line_num=proposal.line_num,
                origin="corrections/propose",
            ),
        )
        if not resolution.ok:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "unresolvable_reference",
                    "status": resolution.status.value,
                    "reason": resolution.reason,
                },
            )

        cursor = await db.execute(
            """INSERT INTO corrections
               (source_id, line_num, old_text, new_text, user_id, created_at,
                trust_tier, actor_ip_hash, contact_email, link_id,
                source_slug, canonical_id, corpus_version, ref_status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                # Ordinals stay as compatibility fields, but they are now the
                # RESOLVED ones, not whatever the client happened to send.
                resolution.source_id,
                resolution.line_num,
                proposal.old_text,
                proposal.new_text,
                user_id,
                now,
                trust_tier,
                ip_hash,
                proposal.email,
                proposal.link_id,
                resolution.source_slug,
                resolution.canonical_id,
                resolution.corpus_version,
                resolution.status.value,
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
            "reference": {
                "source_slug": resolution.source_slug,
                "canonical_id": resolution.canonical_id,
                "corpus_version": resolution.corpus_version,
                "resolved_via": resolution.status.value,
            },
        }
    finally:
        await db.close()
        if corpus_db is not None:
            await corpus_db.close()


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
