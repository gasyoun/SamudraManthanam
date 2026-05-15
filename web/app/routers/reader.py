from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.db import get_db
from app.settings import settings
import os

router = APIRouter(prefix="/sources", tags=["reader"])
templates = Jinja2Templates(directory="templates")

@router.get("/{source_id}", response_class=HTMLResponse)
async def view_source(request: Request, source_id: int, highlight: str = None):
    db = await get_db(settings.DB_PATH)
    try:
        # Get source info
        async with db.execute("SELECT * FROM sources WHERE id = ?", (source_id,)) as cursor:
            source = await cursor.fetchone()
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
            
        # Get all lines for this source
        async with db.execute(
            "SELECT line_num, link_id, chapter, line_html FROM corpus_lines WHERE source_id = ? ORDER BY line_num",
            (source_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            lines = [dict(r) for r in rows]
            
        return templates.TemplateResponse(
            request=request,
            name="source_view.html",
            context={
                "source": dict(source),
                "lines": lines,
                "highlight": highlight
            }
        )
    finally:
        await db.close()

@router.get("/{source_id}/line/{line_num}", response_class=HTMLResponse)
async def view_line_context(request: Request, source_id: int, line_num: int):
    # Redirect to the main source view with a highlight parameter
    return await view_source(request, source_id, highlight=str(line_num))
