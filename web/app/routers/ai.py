import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import List
from app.services.ai_service import explain_with_ai
from app.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["ai"])

# Frontend caps context to 25 lines; mirror that on the server so a direct
# API client can't blow up the AI-provider bill by sending 10K lines.
MAX_CONTEXT_LINES = 50
MAX_CONTEXT_LINE_LEN = 2000


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

@router.post("/explain")
async def post_explain(request: AIRequest):
    """
    Endpoint for context-aware AI explanations of search results.
    """
    result = await explain_with_ai(request.query, request.context_lines)
    if "error" in result:
        # ai_service may include provider-internal detail in result["error"]; log
        # it for operators and return a stable client-facing message in production.
        logger.warning("ai.explain returned error: %s", result["error"])
        detail = result["error"] if settings.APP_ENV == "development" else "AI service unavailable"
        raise HTTPException(status_code=503, detail=detail)
    return result
