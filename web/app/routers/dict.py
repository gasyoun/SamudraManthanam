"""Dictionary layer UI router (H7790) — the five RU Sanskrit dictionaries
as a first-class surface on samudra.samskrte.ru.

Routes (registered BEFORE the /s/{query} catch-all in main.py):
    /slovari                          — dict landing: the five dicts + counts
    /slovari/lookup?q=...             — headword lookup (Deva/IAST/SLP1)
    /slovari/ru/{query}               — reverse RU→Sa gloss search (badges)
    /slovari/{dict}                   — per-dict page + alphabet index
    /slovari/{dict}/a/{letter}        — headword list for an alphabet letter
    /slovari/{dict}/{slug}            — structured entry page (homonyms/POS)

Mirrors the search-page discipline: server-rendered HTML, canonical URLs,
noindex on zero-result and helper pages.
"""
from __future__ import annotations

import logging
import math

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app import corpus_info
from app.db import get_db
from app.services import dict_service
from app.services.dict_service import (
    DICTS,
    alphabet_index,
    alphabet_sort_key,
    bucket_of,
    get_dict_index,
    normalize_query,
    entry_matches,
    prefix_matches,
)
from app.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["dict"])
templates = Jinja2Templates(directory="templates")
templates.env.globals["corpus_info"] = corpus_info

PAGE_SIZE = 120


def _ctx(request: Request, **kw):
    from app.site_context import template_context
    base = settings.PUBLIC_BASE_URL.rstrip("/") if settings.PUBLIC_BASE_URL else ""
    kw.setdefault("canonical_url", base + request.url.path)
    kw.setdefault("og_title", "Словари санскрита — Пахтанье океана")
    kw.setdefault("og_description", settings.SITE_DESCRIPTION)
    kw.setdefault("og_url", base + request.url.path)
    kw.setdefault("noindex", False)
    return template_context(ss_medium="dict", request=request, **kw)


async def _dict_counts(db, source_ids: dict[str, int]) -> dict[str, int]:
    counts = {}
    for slug, sid in source_ids.items():
        async with db.execute(
            "SELECT COUNT(*) FROM corpus_lines WHERE source_id = ?", (sid,)
        ) as cur:
            counts[slug] = (await cur.fetchone())[0]
    return counts


def _dict_or_404(code: str):
    d = DICTS.get(code)
    if not d:
        return None
    return d


@router.get("/slovari", response_class=HTMLResponse)
async def dict_landing(request: Request):
    db = await get_db(settings.DB_PATH)
    try:
        source_ids = await dict_service.resolve_dict_source_ids(db)
        counts = await _dict_counts(db, source_ids)
    finally:
        await db.close()
    dicts = []
    for code, meta in sorted(DICTS.items(), key=lambda kv: kv[1]["order"]):
        dicts.append({
            "code": code,
            "title": meta["title"],
            "short": meta["short"],
            "description": meta["description"],
            "entries": counts.get(code, 0),
            "available": code in source_ids,
        })
    return templates.TemplateResponse(
        request=request, name="dict_index.html",
        context=_ctx(request, dicts=dicts, total=sum(d["entries"] for d in dicts)),
    )


@router.get("/slovari/lookup", response_class=HTMLResponse)
async def dict_lookup(request: Request, q: str = ""):
    q = q.strip()
    if not q:
        return RedirectResponse(url="/slovari", status_code=302)
    db = await get_db(settings.DB_PATH)
    try:
        source_ids = await dict_service.resolve_dict_source_ids(db)
        keys = normalize_query(q)
        exact: list[dict] = []
        partial: list[dict] = []
        for code, sid in source_ids.items():
            entries = await get_dict_index(
                db, settings.DB_PATH, corpus_info.corpus_version or "", sid, code)
            for e in entries:
                if entry_matches(e, keys):
                    exact.append({"work": code, "badge": DICTS[code]["short"],
                                   "entry": e})
        if not exact:
            for code, sid in source_ids.items():
                entries = await get_dict_index(
                    db, settings.DB_PATH, corpus_info.corpus_version or "", sid, code)
                for e in prefix_matches(entries, keys, limit=20):
                    partial.append({"work": code, "badge": DICTS[code]["short"],
                                    "entry": e})
        if len(exact) == 1 and not partial:
            h = exact[0]
            return RedirectResponse(
                url=f"/slovari/{h['work']}/{h['entry'].slug}", status_code=303)
    finally:
        await db.close()
    return templates.TemplateResponse(
        request=request, name="dict_lookup.html",
        context=_ctx(request, query=q, exact=exact[:40], partial=partial[:40],
                     noindex=True),
    )


@router.get("/slovari/ru", response_class=HTMLResponse)
async def dict_ru_form(request: Request):
    return RedirectResponse(url="/slovari", status_code=302)


@router.get("/slovari/ru/{query:path}", response_class=HTMLResponse)
async def dict_ru_search(request: Request, query: str):
    db = await get_db(settings.DB_PATH)
    try:
        source_ids = await dict_service.resolve_dict_source_ids(db)
        id_to_work = {sid: code for code, sid in source_ids.items()}
        cards = await dict_service.search_gloss(db, id_to_work, query, limit=60)
    finally:
        await db.close()
    noindex = not cards
    return templates.TemplateResponse(
        request=request, name="dict_ru.html",
        context=_ctx(
            request, query=query, cards=cards, noindex=noindex,
            og_title=f"«{query}» — санскритские слова с русским значением | "
                     "Пахтанье океана",
        ),
    )


@router.get("/slovari/{code}", response_class=HTMLResponse)
async def dict_page(request: Request, code: str):
    d = _dict_or_404(code)
    if not d:
        return RedirectResponse(url="/slovari", status_code=302)
    db = await get_db(settings.DB_PATH)
    try:
        source_ids = await dict_service.resolve_dict_source_ids(db)
        sid = source_ids.get(code)
        if sid is None:
            return templates.TemplateResponse(
                request=request, name="dict_page.html",
                context=_ctx(request, dict_code=code, meta=d, available=False,
                             letters=[], total=0, page=0, letter="", entries=[],
                             pages=0, noindex=True),
            )
        entries = await get_dict_index(
            db, settings.DB_PATH, corpus_info.corpus_version or "", sid, code)
    finally:
        await db.close()
    letters = alphabet_index(entries)
    return templates.TemplateResponse(
        request=request, name="dict_page.html",
        context=_ctx(request, dict_code=code, meta=d, available=True,
                     letters=letters, total=len(entries),
                     og_title=f"{d['title']} — Пахтанье океана"),
    )


@router.get("/slovari/{code}/a/{letter}", response_class=HTMLResponse)
async def dict_letter(request: Request, code: str, letter: str, page: int = 1):
    d = _dict_or_404(code)
    if not d:
        return RedirectResponse(url="/slovari", status_code=302)
    page = max(1, page)
    db = await get_db(settings.DB_PATH)
    try:
        source_ids = await dict_service.resolve_dict_source_ids(db)
        sid = source_ids.get(code)
        entries = [] if sid is None else await get_dict_index(
            db, settings.DB_PATH, corpus_info.corpus_version or "", sid, code)
    finally:
        await db.close()
    bucket = [e for e in entries if bucket_of(e.iast or e.cyr or "") == letter]
    bucket.sort(key=lambda e: alphabet_sort_key(e.iast or e.cyr or ""))
    pages = max(1, math.ceil(len(bucket) / PAGE_SIZE))
    page = min(page, pages)
    start = (page - 1) * PAGE_SIZE
    return templates.TemplateResponse(
        request=request, name="dict_page.html",
        context=_ctx(request, dict_code=code, meta=d, available=True,
                     letters=alphabet_index(entries), total=len(bucket),
                     letter=letter, entries=bucket[start:start + PAGE_SIZE],
                     page=page, pages=pages,
                     og_title=f"{d['short']}: слова на {letter} — "
                              "Пахтанье океана"),
    )


@router.get("/slovari/{code}/{slug}", response_class=HTMLResponse)
async def dict_entry_page(request: Request, code: str, slug: str):
    d = _dict_or_404(code)
    if not d:
        return RedirectResponse(url="/slovari", status_code=302)
    db = await get_db(settings.DB_PATH)
    try:
        source_ids = await dict_service.resolve_dict_source_ids(db)
        sid = source_ids.get(code)
        entries = [] if sid is None else await get_dict_index(
            db, settings.DB_PATH, corpus_info.corpus_version or "", sid, code)
        from app.services.dict_service import iast_to_slp1
        want = slug.strip().strip("/")
        matches = [e for e in entries if e.slug.lower() == want.lower()]
        if not matches:
            # slug may be IAST — compare pre-normalized too
            matches = [e for e in entries
                       if (iast_to_slp1(e.iast or "").lower() == want.lower())]
        cross = []
        if matches:
            head = matches[0]
            for other, osid in source_ids.items():
                if other == code:
                    continue
                try:
                    oentries = await get_dict_index(
                        db, settings.DB_PATH,
                        corpus_info.corpus_version or "", osid, other)
                except Exception:
                    continue
                for oe in oentries:
                    if oe.slug.lower() == head.slug.lower():
                        cross.append({"work": other,
                                      "badge": DICTS[other]["short"],
                                      "slug": oe.slug})
                        break
    finally:
        await db.close()
    if not matches:
        return templates.TemplateResponse(
            request=request, name="dict_entry.html",
            context=_ctx(request, dict_code=code, meta=d, headword=slug,
                         entries=[], noindex=True),
            status_code=404,
        )
    head = matches[0]
    hw = head.display_iast() or head.display_deva() or slug
    return templates.TemplateResponse(
        request=request, name="dict_entry.html",
        context=_ctx(request, dict_code=code, meta=d, headword=hw,
                     entries=matches, cross=cross, letter=bucket_of(head.iast),
                     og_title=f"{hw} — {d['short']} | Пахтанье океана"),
    )
