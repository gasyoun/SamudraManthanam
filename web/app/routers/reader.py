from urllib.parse import quote, urlencode

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db import get_db
from app.services.language_filter import (
    filter_html_to_language,
    is_parallel_source,
    normalize_lang,
)
from app.services.source_metadata import (
    build_breadcrumb_jsonld,
    build_line_quotation,
    build_source_jsonld,
)
from app.settings import settings

router = APIRouter(prefix="/sources", tags=["reader"])
templates = Jinja2Templates(directory="templates")


def _build_variant_url(
    *, base: str, source_id: int, highlight: str | None, lang: str | None
) -> str:
    """Build a /sources/{id} URL preserving optional highlight and lang.

    Used for both the canonical URL of the current variant AND for each
    hreflang alternate. Centralised so the query-string order stays
    consistent (`highlight` first, `lang` second) — Google treats different
    orderings as the same URL but our canonical-vs-alternate parity has
    to be exact.
    """
    qs = []
    if highlight:
        qs.append(("highlight", highlight))
    if lang:
        qs.append(("lang", lang))
    path = f"{base}/sources/{source_id}"
    return f"{path}?{urlencode(qs)}" if qs else path


@router.get("/{source_id}", response_class=HTMLResponse)
async def view_source(
    request: Request,
    source_id: int,
    highlight: str | None = None,
    lang: str | None = Query(None, max_length=8),
):
    """Render a source page with optional `?highlight=` deep-link and
    `?lang=ru|sa` filter on parallel-content sources.

    `lang` is silently normalised — unknown values are ignored (treated as
    "no filter") rather than rejected, so a stray bookmark won't 4xx. The
    page-variant URL emitted in canonical / hreflang reflects the
    normalised value.
    """
    normalized_lang = normalize_lang(lang)

    db = await get_db(settings.DB_PATH)
    try:
        async with db.execute("SELECT * FROM sources WHERE id = ?", (source_id,)) as cursor:
            source = await cursor.fetchone()
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

        # `line_text` is used by JSON-LD Quotation entities; the template
        # uses `line_html` for display.
        async with db.execute(
            "SELECT line_num, link_id, chapter, line_html, line_text "
            "FROM corpus_lines WHERE source_id = ? ORDER BY line_num",
            (source_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            lines = [dict(r) for r in rows]

        # Detect parallel structure on a small sample — enough to classify
        # without scanning the entire source. Sources where the structure
        # is uneven (some lines have iast, some don't) still get classified
        # as parallel as long as any sampled line has the marker.
        sample_html = [l.get("line_html") or "" for l in lines[:10]]
        parallel = is_parallel_source(sample_html)

        # Apply the language filter to display HTML if requested AND
        # meaningful — on non-parallel sources the filter is a no-op anyway,
        # but skipping the work saves a regex pass per line.
        if parallel and normalized_lang:
            for line in lines:
                line["line_html"] = filter_html_to_language(
                    line["line_html"], normalized_lang,
                )

        source_dict = dict(source)
        base = settings.PUBLIC_BASE_URL.rstrip("/") if settings.PUBLIC_BASE_URL else ""
        from app.main import _ss_link

        site_name = "Пахтанье океана"
        # Canonical URL is the URL of THIS specific variant — different
        # `?lang=` settings emit different canonical URLs so each variant
        # has a clean identity for search engines.
        canonical_url = _build_variant_url(
            base=base, source_id=source_id, highlight=highlight, lang=normalized_lang,
        )

        # Build hreflang alternates only for parallel sources. For pages
        # whose content is genuinely the same regardless of `?lang=`, the
        # alternates would just lie to crawlers.
        hreflang_alternates: list[dict[str, str]] = []
        if parallel:
            hreflang_alternates = [
                {
                    "hreflang": "x-default",
                    "url": _build_variant_url(
                        base=base, source_id=source_id, highlight=highlight, lang=None,
                    ),
                },
                {
                    "hreflang": "ru",
                    "url": _build_variant_url(
                        base=base, source_id=source_id, highlight=highlight, lang="ru",
                    ),
                },
                {
                    "hreflang": "sa",
                    "url": _build_variant_url(
                        base=base, source_id=source_id, highlight=highlight, lang="sa",
                    ),
                },
            ]

        # Book JSON-LD inLanguage reflects the filtered surface when a
        # specific lang is requested; otherwise stays "ru" (Russian is the
        # dominant page language for the mixed default view).
        book_in_language = normalized_lang if normalized_lang else "ru"

        source_jsonld = build_source_jsonld(
            source=source_dict,
            canonical_url=canonical_url,
            site_name=site_name,
            sample_lines=lines,
            base_url=base,
            in_language=book_in_language,
        )
        breadcrumb_jsonld = build_breadcrumb_jsonld(
            source_title=source_dict.get("title", ""),
            source_url=canonical_url,
            site_name=site_name,
            site_url=base or "/",
        )

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
                    in_language=book_in_language,
                )

        return templates.TemplateResponse(
            request=request,
            name="source_view.html",
            context={
                "source": source_dict,
                "lines": lines,
                "highlight": highlight,
                "lang": normalized_lang,
                "site_name": site_name,
                "ss_url": settings.SYSTEMA_SANSCRITICUM_URL,
                "ss_link": _ss_link("source_view"),
                "og_title": f"{source_dict.get('title', 'Источник')} — Пахтанье океана",
                "og_description": f"Параллельный санскрито-русский текст: {source_dict.get('title', '')}",
                "og_url": canonical_url,
                "canonical_url": canonical_url,
                "hreflang_alternates": hreflang_alternates,
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
