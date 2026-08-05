"""The site root page.

Extracted from `app.main` by H1927 / Lane D2, following the same per-router
`Jinja2Templates` convention the other page routers already use.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app import corpus_info
from app.settings import settings
from app.site_context import ss_link, template_context

router = APIRouter(tags=["pages"])

templates = Jinja2Templates(directory="templates")
# Module object, not a snapshot — attributes are read at render time, so the
# footer reflects whatever lifespan loaded.
templates.env.globals["corpus_info"] = corpus_info


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
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
