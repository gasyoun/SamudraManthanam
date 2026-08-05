import logging
from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
import datetime
from app.canonical_refs import DurableRef, resolve_one_async
from app.canonical_state_migrations import ensure_canonical_state
from app.db import get_db
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
    """A proposed correction, addressed by canonical tuple and/or legacy ordinals.

    Both address forms are accepted during the compatibility span (B4): existing
    clients keep posting ``source_id``/``line_num``, newer ones post
    ``source_slug``/``canonical_id``. Whatever arrives, the stored row carries
    the canonical tuple — resolved, never guessed.
    """

    # Legacy ordinal pair — optional now that a canonical address exists.
    source_id: Optional[int] = Field(None, ge=1)
    line_num: Optional[int] = Field(None, ge=1)
    # Canonical address.
    source_slug: Optional[str] = Field(None, max_length=200)
    canonical_id: Optional[str] = Field(None, max_length=200)
    # Which corpus the client was reading. Only meaningful for the legacy form,
    # where it decides whether an ordinal may be bound at all.
    corpus_version: Optional[str] = Field(None, max_length=100)
    old_text: str = Field(..., min_length=1, max_length=10000)
    new_text: str = Field(..., min_length=1, max_length=10000)
    email: Optional[str] = Field(None, max_length=320)  # RFC 5321 max email length

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
async def propose_correction(proposal: CorrectionProposal):
    # Resolve the reference against the live corpus BEFORE storing anything.
    # A correction whose target cannot be identified is rejected loudly rather
    # than parked against an ordinal that means something else next rebuild.
    corpus_db = await get_db(settings.DB_PATH)
    db = await _open_state_db()
    try:
        if settings.STATE_DB_PATH:
            try:
                await ensure_canonical_state(settings.STATE_DB_PATH)
            except Exception:
                logger.exception("corrections: canonical state migration failed")

        ref = DurableRef(
            source_slug=proposal.source_slug,
            canonical_id=proposal.canonical_id,
            corpus_version=proposal.corpus_version,
            source_id=proposal.source_id,
            line_num=proposal.line_num,
            origin="corrections/propose",
        )
        resolution = await resolve_one_async(corpus_db, db, ref)
        if not resolution.ok:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "unresolvable_reference",
                    "status": resolution.status.value,
                    "reason": resolution.reason,
                },
            )

        now = datetime.datetime.now().isoformat()
        user_id = None
        if proposal.email:
            async with db.execute("SELECT id FROM users WHERE email = ?", (proposal.email,)) as cursor:
                user = await cursor.fetchone()
                if user:
                    user_id = user[0]

        await db.execute(
            """INSERT INTO corrections
               (source_id, line_num, old_text, new_text, user_id, created_at,
                source_slug, canonical_id, corpus_version, ref_status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                # Ordinals stay as compatibility fields, but they are now the
                # RESOLVED ones, not whatever the client happened to send.
                resolution.source_id,
                resolution.line_num,
                proposal.old_text,
                proposal.new_text,
                user_id,
                now,
                resolution.source_slug,
                resolution.canonical_id,
                resolution.corpus_version,
                resolution.status.value,
            ),
        )
        await db.commit()
        return {
            "status": "success",
            "reference": {
                "source_slug": resolution.source_slug,
                "canonical_id": resolution.canonical_id,
                "corpus_version": resolution.corpus_version,
                "resolved_via": resolution.status.value,
            },
        }
    finally:
        await db.close()
        await corpus_db.close()

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
