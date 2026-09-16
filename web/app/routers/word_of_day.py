"""`GET /word-of-day` — daily Kochergina word widget/page (H4955).

Reads the precomputed static record written nightly by
`scripts/word_of_day_generate.py` — no per-request DB query, per the spec's
"no per-request runtime cost added to page load" acceptance line.
"""
import json
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["word-of-day"])
templates = Jinja2Templates(directory="templates")

_DEFAULT_RECORD_PATH = Path(__file__).resolve().parent.parent / "data" / "word_of_day_current.json"


def _record_path() -> Path:
    from app.settings import settings

    configured = getattr(settings, "WORD_OF_DAY_RECORD_PATH", "")
    return Path(configured) if configured else _DEFAULT_RECORD_PATH


RECORD_PATH = _record_path()


def _load_record() -> dict | None:
    if not RECORD_PATH.exists():
        return None
    return json.loads(RECORD_PATH.read_text(encoding="utf-8"))


@router.get("/api/word-of-day")
async def api_word_of_day():
    record = _load_record()
    if record is None:
        return JSONResponse({"error": "not generated yet"}, status_code=503)
    return JSONResponse(record)


@router.get("/word-of-day", response_class=HTMLResponse)
async def word_of_day_page(request: Request):
    from app.main import _template_context

    record = _load_record()

    base = ""
    try:
        from app.settings import settings
        base = settings.PUBLIC_BASE_URL.rstrip("/") if settings.PUBLIC_BASE_URL else ""
    except Exception:
        pass
    canonical_url = f"{base}/word-of-day"

    return templates.TemplateResponse(
        request=request,
        name="word_of_day_page.html",
        context=_template_context(
            ss_medium="word_of_day",
            record=record,
            canonical_url=canonical_url,
            og_title="Слово дня — санскритско-русский словарь Кочергиной",
            og_description=(
                f"{record['gloss']}" if record else "Слово дня из санскритско-русского словаря."
            ),
            og_url=canonical_url,
        ),
    )
