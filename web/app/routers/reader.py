import re
from collections import OrderedDict
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

# Matches `<div class="chapter_title">…</div>` blocks in corpus line_html.
# The Lazarus-built corpus uses this class for chapter headings; only a
# subset of sources additionally wrap chapter names in <H1>. parse_html.py
# captures the H1 case, so most corpus_lines rows have an empty `chapter`
# column. This regex is the render-time fallback that lets the sidebar
# work for the chapter_title-style majority.
_CHAPTER_TITLE_PATTERN = re.compile(
    r'<div class="chapter_title"[^>]*>(.*?)</div>',
    re.IGNORECASE | re.DOTALL,
)
_HTML_TAGS = re.compile(r"<[^>]+>")

def _merge_jsonl_lines(lines: list[dict]) -> list[dict]:
    """Group JSONL segment rows by passage and assemble citation_block HTML.

    JSONL ingest emits one corpus_lines row per segment (sa, ru, comm0 …).
    All segments of one passage share the same link_id.  This function
    groups them and reconstructs the citation_block / chapter_block HTML
    structure so the language filter and template behave identically to the
    legacy HTML-parsed ingest path.

    canonical_id encodes the segment type as a '#seg' suffix, e.g.:
        rigveda:1.1.1#sa  → Sanskrit
        rigveda:1.1.1#ru  → Russian translation
        rigveda:1.1.1#comm0 → first commentary block
    Records without a '#' in canonical_id (older DB fixtures or manual rows)
    are grouped by link_id and emitted unchanged via the single-record fallback.
    """
    groups: OrderedDict[str, list[dict]] = OrderedDict()
    for line in lines:
        key = line.get("link_id") or str(line.get("line_num", ""))
        if key not in groups:
            groups[key] = []
        groups[key].append(line)

    merged: list[dict] = []
    for key, recs in groups.items():
        recs_sorted = sorted(recs, key=lambda r: r.get("line_num", 0))

        sa_html = ""
        ru_html = ""
        comm_items: list[str] = []
        chapter = None
        line_num = recs_sorted[0]["line_num"]
        link_id = recs_sorted[0].get("link_id", "")
        line_text = ""

        for rec in recs_sorted:
            cid = rec.get("canonical_id") or ""
            h = rec.get("line_html") or ""
            if cid.endswith("#sa"):
                sa_html = h
                chapter = rec.get("chapter")
                line_text = rec.get("line_text", "")
            elif cid.endswith("#ru"):
                ru_html = h
                if not line_text:
                    line_text = rec.get("line_text", "")
            elif "#comm" in cid:
                comm_items.append(h)

        parts: list[str] = []
        if sa_html or ru_html:
            inner = ""
            if sa_html:
                inner += f'<div class="chapter_block iast">{sa_html}</div>'
            if ru_html:
                inner += f'<div class="chapter_block translation">{ru_html}</div>'
            parts.append(f'<div class="chapter_content">{inner}</div>')
        if comm_items:
            items_html = "".join(
                f'<div class="comment_item">{c}</div>' for c in comm_items
            )
            parts.append(f'<div class="comments">{items_html}</div>')

        passage_html = (
            "".join(parts) if parts else (recs_sorted[0].get("line_html") or "")
        )

        merged.append({
            "line_num": line_num,
            "link_id": link_id,
            "chapter": chapter,
            "line_html": passage_html,
            "line_text": line_text,
        })

    return merged


router = APIRouter(prefix="/sources", tags=["reader"])
templates = Jinja2Templates(directory="templates")
from app import corpus_info
templates.env.globals["corpus_info"] = corpus_info


def _build_variant_url(
    *, base: str, slug: str, highlight: str | None, lang: str | None
) -> str:
    """Build a /sources/{slug} URL preserving optional highlight and lang.

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
    path = f"{base}/sources/{quote(slug)}"
    return f"{path}?{urlencode(qs)}" if qs else path


@router.get("/{slug_or_id}", response_class=HTMLResponse)
async def view_source(
    request: Request,
    slug_or_id: str,
    highlight: str | None = None,
    lang: str | None = Query(None, max_length=8),
):
    """Render a source page with optional `?highlight=` deep-link and
    `?lang=ru|sa` filter on parallel-content sources.

    Accepts both forms for backward compatibility with bookmarks / external
    indexes:

    * `/sources/{slug}` (canonical) — looks up by `sources.slug`.
    * `/sources/{int_id}` (legacy) — looks up by `sources.id`, then 301
      redirects to the slug URL. Lets Google transition its index toward
      the stable URL.

    `lang` is silently normalised — unknown values are ignored (treated as
    "no filter") rather than rejected, so a stray bookmark won't 4xx. The
    page-variant URL emitted in canonical / hreflang reflects the
    normalised value.
    """
    normalized_lang = normalize_lang(lang)

    db = await get_db(settings.DB_PATH)
    try:
        # Numeric path param → legacy ID. Look up, redirect to slug URL.
        if slug_or_id.isdigit():
            async with db.execute(
                "SELECT slug FROM sources WHERE id = ?", (int(slug_or_id),),
            ) as cur:
                legacy = await cur.fetchone()
            if not legacy or not legacy[0]:
                raise HTTPException(status_code=404, detail="Source not found")
            # Preserve query string on the redirect so highlight/lang survive.
            target = f"/sources/{quote(legacy[0])}"
            qs = request.url.query
            if qs:
                target += f"?{qs}"
            return RedirectResponse(target, status_code=301)

        # Slug lookup.
        async with db.execute(
            "SELECT * FROM sources WHERE slug = ?", (slug_or_id,),
        ) as cursor:
            source = await cursor.fetchone()
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        source_id = source["id"]

        # `line_text` is used by JSON-LD Quotation entities; the template
        # uses `line_html` for display.
        async with db.execute(
            "SELECT line_num, link_id, chapter, line_html, line_text, canonical_id "
            "FROM corpus_lines WHERE source_id = ? ORDER BY line_num",
            (source_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            lines = [dict(r) for r in rows]

        # JSONL ingest emits one row per segment (sa/ru/comm). Detect via
        # the '#seg' suffix in canonical_id and merge segments into full
        # citation_block HTML before the language filter and template see them.
        if any("#" in (r.get("canonical_id") or "") for r in lines[:20]):
            lines = _merge_jsonl_lines(lines)

        # Detect parallel structure AFTER potential JSONL merge so the
        # assembled HTML carries the chapter_block iast/translation markers.
        sample_html = [l.get("line_html") or "" for l in lines[:10]]
        parallel = is_parallel_source(sample_html)

        # Build a chapter table-of-contents for the sticky sidebar.
        # Two detection paths:
        #   1. Use the `chapter` column when populated (sources with <H1>).
        #   2. Otherwise scan `line_html` for `<div class="chapter_title">`,
        #      which the majority of corpus sources use instead.
        # Dedup by name and skip consecutive repeats so each chapter appears
        # exactly once.
        chapters: list[dict] = []
        seen_chapters: set[str] = set()
        for line in lines:
            ch = (line.get("chapter") or "").strip()
            if not ch:
                m = _CHAPTER_TITLE_PATTERN.search(line.get("line_html") or "")
                if m:
                    ch = _HTML_TAGS.sub("", m.group(1)).strip()
            if ch and ch not in seen_chapters:
                seen_chapters.add(ch)
                chapters.append({
                    "name": ch,
                    "line_num": line["line_num"],
                    "link_id": line.get("link_id") or "",
                })

        # Apply the language filter to display HTML if requested AND
        # meaningful — on non-parallel sources the filter is a no-op anyway,
        # but skipping the work saves a regex pass per line.
        if parallel and normalized_lang:
            for line in lines:
                line["line_html"] = filter_html_to_language(
                    line["line_html"], normalized_lang,
                )

        source_dict = dict(source)
        slug = source_dict["slug"]
        base = settings.PUBLIC_BASE_URL.rstrip("/") if settings.PUBLIC_BASE_URL else ""
        from app.main import _ss_link

        site_name = "Пахтанье океана"
        # Canonical URL is the URL of THIS specific variant — different
        # `?lang=` settings emit different canonical URLs so each variant
        # has a clean identity for search engines.
        canonical_url = _build_variant_url(
            base=base, slug=slug, highlight=highlight, lang=normalized_lang,
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
                        base=base, slug=slug, highlight=highlight, lang=None,
                    ),
                },
                {
                    "hreflang": "ru",
                    "url": _build_variant_url(
                        base=base, slug=slug, highlight=highlight, lang="ru",
                    ),
                },
                {
                    "hreflang": "sa",
                    "url": _build_variant_url(
                        base=base, slug=slug, highlight=highlight, lang="sa",
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
                    slug=slug,
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
                "og_type": "article",
                "canonical_url": canonical_url,
                "hreflang_alternates": hreflang_alternates,
                "chapters": chapters,
                "is_parallel": parallel,
                "slug": slug,
                "source_jsonld": source_jsonld,
                "breadcrumb_jsonld": breadcrumb_jsonld,
                "highlight_jsonld": highlight_jsonld,
            }
        )
    finally:
        await db.close()


@router.get("/{slug_or_id}/line/{line_num}", response_class=HTMLResponse)
async def view_line_context(request: Request, slug_or_id: str, line_num: int):
    """Render a source page with the line highlighted. Accepts both slug
    and legacy numeric forms; `view_source` handles the disambiguation."""
    return await view_source(request, slug_or_id, highlight=str(line_num))


@router.get("/{slug_or_id}/anchor/{link_id}", response_class=RedirectResponse)
async def anchor_redirect(slug_or_id: str, link_id: str):
    """Stable permalink for a line identified by its link_id attribute.

    `link_id` may contain characters that have meaning in URLs (`&`, `#`, `?`, `=`).
    `quote(..., safe='')` ensures all of them are percent-encoded so the
    `highlight` query param survives intact through the redirect.

    The redirect target preserves whatever path form the caller used —
    slug or legacy numeric. Numeric URLs hitting `view_source` will then
    cascade to a second 301 onto the canonical slug URL.
    """
    safe_link = quote(link_id, safe="")
    safe_path = quote(slug_or_id, safe="")
    return RedirectResponse(
        url=f"/sources/{safe_path}?highlight={safe_link}", status_code=302,
    )
