"""`/chronology` — interactive timeline of the corpus, dated via VisualDCS.

Two surfaces, mirroring the search_page split (JSON API + SEO-friendly page):

- ``GET /api/chronology``  the crosswalk JSON (periods + texts) — the data layer
  built by ``corpus_builder/chronology/build_chronology.py``. Dates are not
  re-derived here: each text carries its own DCS date, inherits its period
  bucket's date, or (author-datable medieval works) a flagged scholarly date.
- ``GET /chronology``  a Jinja page that fetches the JSON and draws a
  period-lane scatter + sortable table. Classification scheme after
  DharmaMitra's sanskrit-dating chronology.

The JSON file is read once and cached in-process; editing it requires a
restart (same lifecycle as the corpus DB snapshot). Missing file fails soft
to a 503 so the rest of the app keeps serving.
"""
import json
import logging
import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates

from app import corpus_info
from app.settings import settings

router = APIRouter(tags=["chronology"])
templates = Jinja2Templates(directory="templates")
templates.env.globals["corpus_info"] = corpus_info
logger = logging.getLogger(__name__)

# web/app/routers/chronology.py -> web/
_WEB_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DATA_PATH = os.path.join(
    _WEB_DIR, "corpus_builder", "chronology", "texts_chronology.json"
)

_cache: dict[str, str | None] = {"text": None}


def _load_text() -> str:
    """Read the crosswalk JSON once and cache the raw text. Raises
    FileNotFoundError if the build hasn't been run."""
    if _cache["text"] is None:
        with open(_DATA_PATH, encoding="utf-8") as f:
            _cache["text"] = f.read()
    return _cache["text"]


@router.get("/api/chronology")
async def chronology_data():
    """Serve the crosswalk JSON verbatim (parsed by the page client-side)."""
    try:
        text = _load_text()
    except FileNotFoundError:
        logger.warning("chronology: data file missing at %s", _DATA_PATH)
        return JSONResponse(
            {"detail": "chronology data not built; run "
                       "corpus_builder/chronology/build_chronology.py"},
            status_code=503,
        )
    return Response(
        content=text,
        media_type="application/json",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.get("/chronology", response_class=HTMLResponse)
async def chronology_page(request: Request):
    from app.main import _template_context

    base = settings.PUBLIC_BASE_URL.rstrip("/") if settings.PUBLIC_BASE_URL else ""
    n_dated = 0
    try:
        data = json.loads(_load_text())
        n_dated = sum(1 for t in data.get("texts", []) if t.get("date_ce") is not None)
    except Exception:
        pass

    return templates.TemplateResponse(
        request=request,
        name="chronology.html",
        context=_template_context(
            ss_medium="chronology",
            n_dated=n_dated,
            canonical_url=f"{base}/chronology",
            og_title="Хронология санскритского корпуса — Пахтанье океана",
            og_description=(
                "Каждый датируемый текст санскрито-русского и санскрито-английского "
                "корпуса на временной шкале; датировка по хронологии VisualDCS."
            ),
            og_url=f"{base}/chronology",
        ),
    )
