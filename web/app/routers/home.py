"""The site root page.

Extracted from `app.main` by H1927 / Lane D2, following the same per-router
`Jinja2Templates` convention the other page routers already use.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app import corpus_info
from app.search_urls import can_use_pretty_path, expand_source_token, pretty_search_path
from app.settings import settings
from app.site_context import ss_link, template_context

router = APIRouter(tags=["pages"])

templates = Jinja2Templates(directory="templates")
# Module object, not a snapshot — attributes are read at render time, so the
# footer reflects whatever lifespan loaded.
templates.env.globals["corpus_info"] = corpus_info


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    q = (request.query_params.get("q") or "").strip()
    if q:
        src = request.query_params.get("src")
        slugs = None
        if src and "," not in src and not src.isdigit():
            slugs = [expand_source_token(src)]
        extra_flags = any(request.query_params.get(k) for k in ("mode", "cs", "ww"))
        if not extra_flags and can_use_pretty_path(query=q, source_slugs=slugs):
            return RedirectResponse(url=pretty_search_path(q, slugs), status_code=301)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=template_context(
            ss_medium="navbar",
            engaged_ss_link=ss_link("engaged_banner"),
            og_title="Пахтанье океана — поиск по санскрито-русскому корпусу",
            og_description=settings.SITE_DESCRIPTION,
            og_url=settings.PUBLIC_BASE_URL or "/",
        ),
    )
