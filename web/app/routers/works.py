"""`/works` — a clickable size-and-chronology index of the parallel
Sanskrit–Russian corpus.

Same two-surface split as the chronology page (JSON API + SEO page):

- ``GET /api/works``  the ``works_index.json`` data layer built by
  ``corpus_builder/works_index/build_works_index.py`` — each work carries its
  period/date (inherited from the chronology crosswalk, not re-derived), a
  size 1–10 (log10 of Sanskrit text volume), and its ``parts``.
- ``GET /works``  a Jinja page that renders the works two ways side by side:
  merged works (the Mahābhārata as one book) on the left, every part (each
  parvan separately) on the right, grouped by period. Title → live reading
  page; size badge → the work on ``/chronology``.

The JSON is read once and cached in-process (restart to pick up a rebuild).
Missing file fails soft to 503 so the rest of the app keeps serving.
"""
import json
import logging
import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates

from app import corpus_info
from app.settings import settings

router = APIRouter(tags=["works"])
templates = Jinja2Templates(directory="templates")
templates.env.globals["corpus_info"] = corpus_info
logger = logging.getLogger(__name__)

# app/routers/works.py -> web/
_WEB_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DATA_PATH = os.path.join(
    _WEB_DIR, "corpus_builder", "works_index", "works_index.json"
)

_cache: dict[str, str | None] = {"text": None}


def _load_text() -> str:
    """Read the works-index JSON once and cache the raw text. Raises
    FileNotFoundError if the build hasn't been run."""
    if _cache["text"] is None:
        with open(_DATA_PATH, encoding="utf-8") as f:
            _cache["text"] = f.read()
    return _cache["text"]


@router.get("/api/works")
async def works_data():
    """Serve the works-index JSON verbatim (parsed by the page client-side)."""
    try:
        text = _load_text()
    except FileNotFoundError:
        logger.warning("works: data file missing at %s", _DATA_PATH)
        return JSONResponse(
            {"detail": "works index not built; run "
                       "corpus_builder/works_index/build_works_index.py"},
            status_code=503,
        )
    return Response(
        content=text,
        media_type="application/json",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.get("/works", response_class=HTMLResponse)
async def works_page(request: Request):
    from app.main import _template_context

    base = settings.PUBLIC_BASE_URL.rstrip("/") if settings.PUBLIC_BASE_URL else ""
    n_works = 0
    try:
        data = json.loads(_load_text())
        n_works = data.get("n_works", 0)
    except Exception:
        pass

    return templates.TemplateResponse(
        request=request,
        name="works.html",
        context=_template_context(
            ss_medium="works",
            n_works=n_works,
            canonical_url=f"{base}/works",
            og_title="Указатель текстов корпуса — Пахтанье океана",
            og_description=(
                "Все тексты санскрито-русского параллельного корпуса: по периодам, "
                "с размером каждого произведения (1–10) и ссылками на чтение. "
                "«Махабхарата» — как единая книга и по парвам."
            ),
            og_url=f"{base}/works",
        ),
    )
