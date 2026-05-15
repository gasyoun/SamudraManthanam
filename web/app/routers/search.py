from fastapi import APIRouter, HTTPException, Request
import time
import os
import json
import re
from urllib.parse import quote
from sse_starlette.sse import EventSourceResponse
from app.db import get_db
from app.models import SearchRequest, SearchResult, SearchResultItem, SearchMode
from app.services.html_service import render_fragment, render_full_page, render_standalone
from app.services.dispatch_service import dispatch_search
from fastapi.responses import HTMLResponse

from app.settings import settings

router = APIRouter(prefix="/api/search", tags=["search"])


def parse_source_ids(source_ids_str: str | None) -> list[int] | None:
    if source_ids_str is None:
        return None

    try:
        return [int(sid) for sid in source_ids_str.split(",") if sid.strip()]
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="source_ids must be a comma-separated list of integers") from exc


def export_filename(query: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", query).strip("._")
    if not safe:
        safe = "search"
    return f"{safe[:80]}.html"


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
async def get_search_stream(request: Request, query: str, mode: SearchMode = SearchMode.plain, case_sensitive: bool = False, whole_word: bool = False):
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

@router.get("/export", response_class=HTMLResponse)
async def get_export(request: Request, query: str, mode: SearchMode = SearchMode.plain, case_sensitive: bool = False, whole_word: bool = False):
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
        html = render_standalone(query, fragment)
        
        filename = export_filename(query)
        encoded_filename = quote(filename)
        headers = {"Content-Disposition": f"attachment; filename=\"{filename}\"; filename*=UTF-8''{encoded_filename}"}
        return HTMLResponse(content=html, headers=headers)
    finally:
        await db.close()
