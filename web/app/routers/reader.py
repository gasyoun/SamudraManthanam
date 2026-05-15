from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
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
            
        source_dict = dict(source)
        base = settings.PUBLIC_BASE_URL.rstrip("/") if settings.PUBLIC_BASE_URL else ""
        return templates.TemplateResponse(
            request=request,
            name="source_view.html",
            context={
                "source": source_dict,
                "lines": lines,
                "highlight": highlight,
                "site_name": "Пахтанье океана",
                "ss_url": settings.SYSTEMA_SANSCRITICUM_URL,
                "og_title": f"{source_dict.get('title', 'Источник')} — Пахтанье океана",
                "og_description": f"Параллельный санскрито-русский текст: {source_dict.get('title', '')}",
                "og_url": f"{base}/sources/{source_id}",
            }
        )
    finally:
        await db.close()

@router.get("/{source_id}/line/{line_num}", response_class=HTMLResponse)
async def view_line_context(request: Request, source_id: int, line_num: int):
    return await view_source(request, source_id, highlight=str(line_num))

@router.get("/{source_id}/anchor/{link_id}", response_class=RedirectResponse)
async def anchor_redirect(source_id: int, link_id: str):
    """Stable permalink for a line identified by its link_id attribute."""
    return RedirectResponse(url=f"/sources/{source_id}?highlight={link_id}", status_code=302)
