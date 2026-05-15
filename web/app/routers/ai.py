from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.services.ai_service import explain_with_ai

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
        raise HTTPException(status_code=503, detail=result["error"])
    return result
