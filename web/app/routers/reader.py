from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from urllib.parse import quote
from app.db import get_db
from app.services.source_metadata import (
    build_breadcrumb_jsonld,
    build_line_quotation,
    build_source_jsonld,
)
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
            
        # Get all lines for this source. `line_text` is the plain-text strip
        # used by JSON-LD Quotation entities; the template still uses `line_html`
        # for display.
        async with db.execute(
            "SELECT line_num, link_id, chapter, line_html, line_text "
            "FROM corpus_lines WHERE source_id = ? ORDER BY line_num",
            (source_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            lines = [dict(r) for r in rows]
            
        source_dict = dict(source)
        base = settings.PUBLIC_BASE_URL.rstrip("/") if settings.PUBLIC_BASE_URL else ""
        from app.main import _ss_link

        site_name = "Пахтанье океана"
        canonical_url = f"{base}/sources/{source_id}"
        # Build JSON-LD ahead of render so the template just dumps it. Keeping
        # the schema generation in the service module means tests can validate
        # the structured-data shape without spinning up the HTTP layer.
        source_jsonld = build_source_jsonld(
            source=source_dict,
            canonical_url=canonical_url,
            site_name=site_name,
            sample_lines=lines,
            base_url=base,
        )
        breadcrumb_jsonld = build_breadcrumb_jsonld(
            source_title=source_dict.get("title", ""),
            source_url=canonical_url,
            site_name=site_name,
            site_url=base or "/",
        )

        # When the reader URL has `?highlight=X`, surface that specific verse
        # as its own top-level Quotation entity. The `@id` on the Quotation
        # matches the URL the user is on, so Google can attribute the
        # structured data to this exact page variant. Falls back gracefully
        # when the highlight doesn't match any line in the source.
        highlight_jsonld = None
        if highlight:
            highlighted_line = next(
                (l for l in lines
                 if l.get("link_id") == highlight or str(l.get("line_num")) == highlight),
                None,
            )
            if highlighted_line:
                highlight_jsonld = build_line_quotation(
                    line=highlighted_line,
                    source_id=source_id,
                    source_url=canonical_url,
                    base_url=base,
                )

        return templates.TemplateResponse(
            request=request,
            name="source_view.html",
            context={
                "source": source_dict,
                "lines": lines,
                "highlight": highlight,
                "site_name": site_name,
                "ss_url": settings.SYSTEMA_SANSCRITICUM_URL,
                "ss_link": _ss_link("source_view"),
                "og_title": f"{source_dict.get('title', 'Источник')} — Пахтанье океана",
                "og_description": f"Параллельный санскрито-русский текст: {source_dict.get('title', '')}",
                "og_url": canonical_url,
                "canonical_url": canonical_url,
                "source_jsonld": source_jsonld,
                "breadcrumb_jsonld": breadcrumb_jsonld,
                "highlight_jsonld": highlight_jsonld,
            }
        )
    finally:
        await db.close()

@router.get("/{source_id}/line/{line_num}", response_class=HTMLResponse)
async def view_line_context(request: Request, source_id: int, line_num: int):
    return await view_source(request, source_id, highlight=str(line_num))

@router.get("/{source_id}/anchor/{link_id}", response_class=RedirectResponse)
async def anchor_redirect(source_id: int, link_id: str):
    """Stable permalink for a line identified by its link_id attribute.

    `link_id` may contain characters that have meaning in URLs (`&`, `#`, `?`, `=`).
    quote() with `safe=''` ensures all of them are percent-encoded so the
    `highlight` query param survives intact through the redirect.
    """
    safe_link = quote(link_id, safe="")
    return RedirectResponse(url=f"/sources/{source_id}?highlight={safe_link}", status_code=302)
