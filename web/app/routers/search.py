"""Search API routes.

Note: GET /api/search/stream (SSE progress events) is intentionally kept but
not wired into the frontend (search.js) — see PLAN_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md
R7. It is covered by hermetic tests in tests/test_api.py.
"""
from fastapi import APIRouter, HTTPException, Request, Query
import time
import os
import json
import re
import csv
import io
from urllib.parse import quote, urlencode
from sse_starlette.sse import EventSourceResponse
from app.db import get_db
from app.models import SearchRequest, SearchResult, SearchResultItem, SearchMode
from app.services.html_service import render_fragment, render_full_page, render_standalone, kwic_excerpt
from app.services.dispatch_service import dispatch_search
from app.services.regex_executor import validate_patterns
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from app.settings import settings

router = APIRouter(prefix="/api/search", tags=["search"])

# H1831 — bulk-download exposure cap for JSON/CSV export.
# Mechanism: per-row snippet truncation to the same KWIC window the live
# search UI uses (40 chars each side of the match ≈ 80+ chars total), NOT
# full verse+translation text. HTML export is already snippet-based via
# render_fragment and is left unchanged. This keeps export as a search-result
# set, never a reconstruct-the-corpus bulk dump.
_EXPORT_SNIPPET_WINDOW = 40


def _export_snippet_text(line_text: str, query: str) -> str:
    """Return a UI-equivalent KWIC snippet of plain text for export."""
    parts = kwic_excerpt(line_text or "", query, window=_EXPORT_SNIPPET_WINDOW)
    snippet = f"{parts.get('before', '')}{parts.get('match', '')}{parts.get('after', '')}"
    return snippet


def _export_snippet_html(line_text: str, query: str) -> str:
    """Export HTML field is capped to a plain-text KWIC snippet (escaped).

    Full line_html is intentionally NOT emitted in JSON export — that was the
    bulk-download hole. Callers needing markup use the HTML export format,
    which goes through render_fragment (already snippet-oriented).
    """
    import html as _html
    return _html.escape(_export_snippet_text(line_text, query), quote=False)


import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def parse_source_ids(source_ids_str: str | None) -> list[int] | None:
    if source_ids_str is None:
        return None

    try:
        return [int(sid) for sid in source_ids_str.split(",") if sid.strip()]
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="source_ids must be a comma-separated list of integers") from exc


def export_filename(query: str, extension: str = "html") -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", query).strip("._")
    if not safe:
        safe = "search"
    return f"{safe[:80]}.{extension}"


async def get_corpus_version(db) -> str | None:
    try:
        async with db.execute("SELECT value FROM corpus_meta WHERE key = 'corpus_version'") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None
    except Exception:
        return None


@router.post("", response_model=SearchResult)
async def post_search(request: SearchRequest):
    start_time = time.time()
    db = await get_db(settings.DB_PATH)
    search_metadata = None
    try:
        search_data = await dispatch_search(
            db, request.query, request.mode, request.case_sensitive, 
            request.whole_word, request.source_ids, request.limit
        )
        results = search_data["results"]
        search_metadata = search_data["search_metadata"]
        elapsed_ms = (time.time() - start_time) * 1000
        sources_hit = len(set(r["source_id"] for r in results))
        
        # Telemetry: Log search parameters and performance (omitting full query in production)
        log_query = request.query if settings.APP_ENV == "development" else f"{request.query[:50]}..."
        logger.info(f"search: mode={request.mode} query='{log_query}' sources={len(request.source_ids) if request.source_ids else 'all'} total={len(results)} elapsed={elapsed_ms:.2f}ms")
        
        html_fragment = render_fragment(
            request.query,
            results,
            search_metadata=search_metadata,
            elapsed_ms=elapsed_ms,
        )

        return SearchResult(
            query=request.query,
            total=len(results),
            elapsed_ms=elapsed_ms,
            sources_hit=sources_hit,
            results=[SearchResultItem(**r) for r in results],
            html_fragment=html_fragment,
            search_metadata=search_metadata,
            # Without the version, a result's canonical id names a passage but
            # not the corpus it was read from (H1925, B2).
            corpus_version=await get_corpus_version(db),
        )
    finally:
        await db.close()

@router.get("/stream")
async def get_search_stream(
    request: Request,
    query: str = Query(..., min_length=1, max_length=1000),
    mode: SearchMode = SearchMode.plain,
    case_sensitive: bool = False,
    whole_word: bool = False,
):
    # Handle source_ids from query params
    source_ids = parse_source_ids(request.query_params.get("source_ids"))

    # Validate against the published regex contract before opening a stream.
    # H1926: `re.compile` accepted patterns the executor refuses (over-long,
    # too many) and echoed the engine's message — which quotes the pattern and
    # internal parser state — straight back to the caller.
    if mode == SearchMode.regex:
        validate_patterns(query.split('\n'), case_sensitive)

    async def event_generator():
        start_time = time.time()
        db = await get_db(settings.DB_PATH)
        try:
            # For SSE, we scan source-by-source to report progress
            # First, get sources
            if source_ids is not None:
                if len(source_ids) == 0:
                    yield {"data": json.dumps({"type": "done", "total": 0, "elapsed_ms": 0})}
                    return
                placeholders = ",".join(['?'] * len(source_ids))
                sql = f"SELECT id FROM sources WHERE id IN ({placeholders}) ORDER BY sort_order"
                params = source_ids
            else:
                sql = "SELECT id FROM sources ORDER BY sort_order"
                params = []
                
            async with db.execute(sql, params) as cursor:
                sources = await cursor.fetchall()
            
            if not sources:
                yield {"data": json.dumps({"type": "done", "total": 0, "elapsed_ms": 0})}
                return
            
            total_found = 0
            for i, source in enumerate(sources):
                sid = source[0]
                # Search only in this source
                search_data = await dispatch_search(
                    db, query, mode, case_sensitive, whole_word, [sid], 5000
                )
                res = search_data["results"]

                
                total_found += len(res)
                percent = int((i + 1) / len(sources) * 100)
                
                yield {
                    "data": json.dumps({
                        "type": "progress",
                        "source_id": sid,
                        "found_so_far": total_found,
                        "percent": percent
                    })
                }
                # Artificial delay for demo if needed, but not in production
                # await asyncio.sleep(0.01)
                
            elapsed_ms = (time.time() - start_time) * 1000
            yield {
                "data": json.dumps({
                    "type": "done",
                    "total": total_found,
                    "elapsed_ms": elapsed_ms
                })
            }
        finally:
            await db.close()

    return EventSourceResponse(event_generator())

@router.get("/context")
async def get_context(
    source_id: int,
    line_num: int,
    window: int = Query(default=5, ge=1, le=20),
):
    """Return up to `window` lines before and after `line_num` in the given source."""
    db = await get_db(settings.DB_PATH)
    try:
        async with db.execute(
            """SELECT cl.line_num, cl.link_id, cl.chapter, cl.line_html,
                      cl.canonical_id, s.slug AS source_slug
               FROM corpus_lines cl
               JOIN sources s ON s.id = cl.source_id
               WHERE cl.source_id = ? AND cl.line_num BETWEEN ? AND ?
               ORDER BY cl.line_num""",
            (source_id, line_num - window, line_num + window),
        ) as cursor:
            rows = await cursor.fetchall()
            lines = [dict(r) for r in rows]

        return {
            "before":  [l for l in lines if l["line_num"] < line_num],
            "current": next((l for l in lines if l["line_num"] == line_num), None),
            "after":   [l for l in lines if l["line_num"] > line_num],
            "corpus_version": await get_corpus_version(db),
        }
    finally:
        await db.close()


@router.get("/export")
async def get_export(
    request: Request,
    query: str = Query(..., min_length=1, max_length=1000),
    mode: SearchMode = SearchMode.plain,
    case_sensitive: bool = False,
    whole_word: bool = False,
    format: str = Query("html", pattern="^(html|json|csv)$"),
):
    # Handle source_ids from query params
    source_ids = parse_source_ids(request.query_params.get("source_ids"))

    # Same contract gate as /stream — see the note there.
    if mode == SearchMode.regex:
        validate_patterns(query.split('\n'), case_sensitive)

    db = await get_db(settings.DB_PATH)
    search_metadata = None
    try:
        limit = 5000
        search_data = await dispatch_search(
            db, query, mode, case_sensitive, whole_word, source_ids, limit
        )
        results = search_data["results"]
        search_metadata = search_data["search_metadata"]

            
        limit_reached = len(results) >= limit
        fragment = render_fragment(
            query,
            results,
            limit_reached=limit_reached,
            search_metadata=search_metadata,
        )
        
        # Collect export metadata
        corpus_version = await get_corpus_version(db)

        # Build a live-search permalink so the reader can reopen this query in the app
        qs: list[tuple] = [("q", query)]
        if mode != SearchMode.plain:
            qs.append(("mode", str(mode)))
        if case_sensitive:
            qs.append(("cs", "1"))
        if whole_word:
            qs.append(("ww", "1"))
        if source_ids:
            qs.append(("src", ",".join(str(s) for s in source_ids)))
        live_search_url = "/?" + urlencode(qs)

        metadata = {
            "query": query,
            "mode": mode,
            "result_count": len(results),
            "corpus_version": corpus_version,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_filter": f"{len(source_ids)} selected" if source_ids else "all",
            "live_search_url": live_search_url,
        }

        if format == "json":
            filename = export_filename(query, "json")
            encoded_filename = quote(filename)
            headers = {"Content-Disposition": f"attachment; filename=\"{filename}\"; filename*=UTF-8''{encoded_filename}"}
            payload = {
                "metadata": metadata,
                "results": [
                    {
                        "source_id": r["source_id"],
                        "source_title": r["source_title"],
                        "chapter": r["chapter"],
                        "line_num": r["line_num"],
                        "link_id": r["link_id"],
                        # Canonical tuple (H1925): an exported citation must
                        # still resolve after the corpus is rebuilt. The
                        # version lives once, in `metadata.corpus_version`.
                        "source_slug": r.get("source_slug"),
                        "canonical_id": r.get("canonical_id"),
                        # H1831: KWIC snippets only — never full untruncated text.
                        "line_html": _export_snippet_html(r.get("line_text") or "", query),
                        "line_text": _export_snippet_text(r.get("line_text") or "", query),
                    }
                    for r in results
                ],
            }
            return JSONResponse(content=payload, headers=headers)

        if format == "csv":
            filename = export_filename(query, "csv")
            encoded_filename = quote(filename)
            headers = {"Content-Disposition": f"attachment; filename=\"{filename}\"; filename*=UTF-8''{encoded_filename}"}
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            for key in ("query", "mode", "corpus_version", "timestamp", "source_filter", "result_count"):
                writer.writerow([f"# {key}", metadata.get(key)])
            writer.writerow([])
            writer.writerow([
                "source_id", "source_title", "chapter", "line_num", "link_id",
                "source_slug", "canonical_id", "line_text",
            ])
            for r in results:
                writer.writerow([
                    r["source_id"],
                    r["source_title"],
                    r["chapter"],
                    r["line_num"],
                    r["link_id"],
                    r.get("source_slug") or "",
                    r.get("canonical_id") or "",
                    # H1831: KWIC snippet, not full verse text.
                    _export_snippet_text(r.get("line_text") or "", query),
                ])
            return PlainTextResponse(content=buffer.getvalue(), media_type="text/csv", headers=headers)

        html = render_standalone(query, fragment, metadata=metadata)

        filename = export_filename(query, "html")
        encoded_filename = quote(filename)
        headers = {"Content-Disposition": f"attachment; filename=\"{filename}\"; filename*=UTF-8''{encoded_filename}"}
        return HTMLResponse(content=html, headers=headers)
    finally:
        await db.close()
