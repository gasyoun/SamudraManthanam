import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from app.services.ai_service import explain_with_ai
from app.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["ai"])

class AIRequest(BaseModel):
    query: str
    context_lines: List[str]

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
