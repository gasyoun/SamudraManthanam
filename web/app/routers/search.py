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
from app.services.html_service import render_fragment, render_full_page, render_standalone
from app.services.dispatch_service import dispatch_search
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from app.settings import settings

router = APIRouter(prefix="/api/search", tags=["search"])


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
        
        html_fragment = render_fragment(request.query, results, search_metadata=search_metadata)
        
        return SearchResult(
            query=request.query,
            total=len(results),
            elapsed_ms=elapsed_ms,
            sources_hit=sources_hit,
            results=[SearchResultItem(**r) for r in results],
            html_fragment=html_fragment,
            search_metadata=search_metadata
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

    # Validate regex if needed
    if mode == SearchMode.regex:
        patterns = [p.strip() for p in query.split('\n') if p.strip()]
        for p in patterns:
            try:
                re.compile(p)
            except re.error as e:
                raise HTTPException(status_code=400, detail=f"Invalid regex: {e}")
    
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
            """SELECT line_num, link_id, chapter, line_html
               FROM corpus_lines
               WHERE source_id = ? AND line_num BETWEEN ? AND ?
               ORDER BY line_num""",
            (source_id, line_num - window, line_num + window),
        ) as cursor:
            rows = await cursor.fetchall()
            lines = [dict(r) for r in rows]

        return {
            "before":  [l for l in lines if l["line_num"] < line_num],
            "current": next((l for l in lines if l["line_num"] == line_num), None),
            "after":   [l for l in lines if l["line_num"] > line_num],
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

    # Validate regex if needed
    if mode == SearchMode.regex:
        patterns = [p.strip() for p in query.split('\n') if p.strip()]
        for p in patterns:
            try:
                re.compile(p)
            except re.error as e:
                raise HTTPException(status_code=400, detail=f"Invalid regex: {e}")

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
        fragment = render_fragment(query, results, limit_reached=limit_reached, search_metadata=search_metadata)
        
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
                        "line_html": r["line_html"],
                        "line_text": r["line_text"],
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
            writer.writerow(["source_id", "source_title", "chapter", "line_num", "link_id", "line_text"])
            for r in results:
                writer.writerow([
                    r["source_id"],
                    r["source_title"],
                    r["chapter"],
                    r["line_num"],
                    r["link_id"],
                    r["line_text"],
                ])
            return PlainTextResponse(content=buffer.getvalue(), media_type="text/csv", headers=headers)

        html = render_standalone(query, fragment, metadata=metadata)

        filename = export_filename(query, "html")
        encoded_filename = quote(filename)
        headers = {"Content-Disposition": f"attachment; filename=\"{filename}\"; filename*=UTF-8''{encoded_filename}"}
        return HTMLResponse(content=html, headers=headers)
    finally:
        await db.close()
