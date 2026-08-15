import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from typing import List
from app.services.ai_service import compare_translations, explain_with_ai
from app.services.rate_limit import (
    AI_MONTHLY_CALL_LIMIT,
    AI_MONTHLY_WINDOW_SECONDS,
    check_and_consume,
)
from app.services.session_service import resolve_session, session_token_from_request
from app.settings import settings
from app.state_db import get_state_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["ai"])

# Frontend caps context to 25 lines; mirror that on the server so a direct
# API client can't blow up the AI-provider bill by sending 10K lines.
MAX_CONTEXT_LINES = 50
MAX_CONTEXT_LINE_LEN = 2000

# /compare-translations bounds — each verse comparison sends at most ~14
# entries on the live corpus (Bhagavadgita with all sources). Cap a bit
# higher to leave room for future works without making the bound trivially
# bypassable for a denial-of-wallet attack.
MAX_COMPARE_TRANSLATIONS = 20
MAX_COMPARE_TEXT_LEN = 4000
MAX_COMPARE_LABEL_LEN = 200


async def _open_state_db():
    """Open state.db with a clean 503 on configuration / connection failure.

    Mirrors the pattern in corrections.py / identity.py — avoids leaking raw
    aiosqlite tracebacks.
    """
    try:
        db = await get_state_db()
    except Exception:
        logger.exception("ai: failed to open state DB")
        raise HTTPException(status_code=503, detail="State service unavailable")
    if not db:
        raise HTTPException(status_code=503, detail="State service unavailable")
    return db


async def _require_quota(request: Request):
    """Auth + hard monthly quota gate for every `/api/ai/*` route (H2772).

    A dead `AI_API_KEY` answers 503 today, which makes these routes look
    harmless — they are actually reachable with no authentication and no
    cap. Whoever next funds the key inherits that exposure unless this gate
    runs first. Returns the resolved user_id for logging/bucket purposes.

    Fails **closed** on a storage error, unlike the corrections rate limiter:
    a broken `rate_limits` table must not let a billable call through
    uncounted.
    """
    db = await _open_state_db()
    try:
        session = await resolve_session(
            db, session_token_from_request(request.headers, request.cookies)
        )
        if not session:
            raise HTTPException(status_code=401, detail="Authentication required")

        decision = await check_and_consume(
            db,
            bucket="ai.call",
            key=f"user:{session.user_id}",
            limit=AI_MONTHLY_CALL_LIMIT,
            window_seconds=AI_MONTHLY_WINDOW_SECONDS,
            fail_open=False,
        )
        if not decision.allowed:
            raise HTTPException(
                status_code=429,
                detail="Monthly AI quota exceeded. Please try again later.",
                headers={"Retry-After": str(decision.retry_after_seconds)},
            )
        return session.user_id
    finally:
        await db.close()


class AIRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    context_lines: List[str] = Field(..., max_length=MAX_CONTEXT_LINES)

    @field_validator("context_lines")
    @classmethod
    def each_line_bounded(cls, v: List[str]) -> List[str]:
        for line in v:
            if len(line) > MAX_CONTEXT_LINE_LEN:
                raise ValueError(
                    f"context_lines item exceeds {MAX_CONTEXT_LINE_LEN} chars"
                )
        return v


class TranslationEntry(BaseModel):
    label: str = Field(..., min_length=1, max_length=MAX_COMPARE_LABEL_LEN)
    role: str = Field("translation", max_length=32)
    text: str = Field(..., min_length=1, max_length=MAX_COMPARE_TEXT_LEN)


class CompareTranslationsRequest(BaseModel):
    work_title: str = Field(..., min_length=1, max_length=200)
    work_title_iast: str = Field("", max_length=200)
    chapter: int = Field(..., ge=1, le=999)
    verse: int = Field(..., ge=1, le=9999)
    iast: str = Field("", max_length=MAX_COMPARE_TEXT_LEN)
    translations: List[TranslationEntry] = Field(..., min_length=2, max_length=MAX_COMPARE_TRANSLATIONS)


@router.post("/explain")
async def post_explain(request: AIRequest, _user_id: str = Depends(_require_quota)):
    """Context-aware AI explanation of free-form search results."""
    result = await explain_with_ai(request.query, request.context_lines)
    if "error" in result:
        # ai_service may include provider-internal detail in result["error"]; log
        # it for operators and return a stable client-facing message in production.
        logger.warning("ai.explain returned error: %s", result["error"])
        detail = result["error"] if settings.APP_ENV == "development" else "AI service unavailable"
        raise HTTPException(status_code=503, detail=detail)
    return result


@router.post("/compare-translations")
async def post_compare_translations(
    request: CompareTranslationsRequest, _user_id: str = Depends(_require_quota)
):
    """Synthesize a scholarly comparison across multiple translations of one verse.

    Powers the "✨ Сравнить переводы" button on `/compare/{work}/{ch}.{v}`.
    Body shape mirrors the data the comparison page already has on hand,
    so the frontend just serialises its embedded JSON payload.
    """
    result = await compare_translations(
        work_title=request.work_title,
        work_title_iast=request.work_title_iast,
        chapter=request.chapter,
        verse=request.verse,
        iast=request.iast,
        translations=[t.model_dump() for t in request.translations],
    )
    if "error" in result:
        logger.warning("ai.compare_translations returned error: %s", result["error"])
        detail = result["error"] if settings.APP_ENV == "development" else "AI service unavailable"
        raise HTTPException(status_code=503, detail=detail)
    return result
