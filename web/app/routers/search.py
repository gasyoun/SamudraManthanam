from fastapi import APIRouter, HTTPException, Request
import time
import os
import json
import asyncio
from sse_starlette.sse import EventSourceResponse
from app.db import get_db
from app.models import SearchRequest, SearchResult, SearchResultItem, SearchMode
from app.services.html_service import render_fragment, render_full_page, render_standalone
from app.services.search_service import search_plain, search_regex
from app.services.morph_service import search_morphological
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/api/search", tags=["search"])

DB_PATH = os.environ.get("DB_PATH", "corpus.db")

@router.post("", response_model=SearchResult)
async def post_search(request: SearchRequest):
    start_time = time.time()
    db = await get_db(DB_PATH)
    try:
        if request.mode == "plain":
            results = await search_plain(
                db, request.query, request.case_sensitive, 
                request.whole_word, request.source_ids, request.limit
            )
        elif request.mode == "regex":
            results = await search_regex(
                db, request.query, request.case_sensitive, 
                request.source_ids, request.limit
            )
        elif request.mode == "morphological":
            results = await search_morphological(
                db, request.query, request.source_ids, request.limit
            )
        else:
            results = []
            
        elapsed_ms = (time.time() - start_time) * 1000
        sources_hit = len(set(r["source_id"] for r in results))
        
        html_fragment = render_fragment(request.query, results)
        
        return SearchResult(
            query=request.query,
            total=len(results),
            elapsed_ms=elapsed_ms,
            sources_hit=sources_hit,
            results=[SearchResultItem(**r) for r in results],
            html_fragment=html_fragment
        )
    finally:
        await db.close()

@router.get("/stream")
async def get_search_stream(request: Request, query: str, mode: SearchMode = SearchMode.plain, case_sensitive: bool = False, whole_word: bool = False):
    # Handle source_ids from query params
    source_ids_str = request.query_params.get("source_ids")
    if source_ids_str is not None:
        source_ids = [int(sid) for sid in source_ids_str.split(",") if sid.strip()]
    else:
        source_ids = None
    
    async def event_generator():
        start_time = time.time()
        db = await get_db(DB_PATH)
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
            
            total_found = 0
            for i, source in enumerate(sources):
                sid = source[0]
                # Search only in this source
                if mode == SearchMode.plain:
                    res = await search_plain(db, query, case_sensitive, whole_word, [sid], 5000)
                elif mode == SearchMode.regex:
                    res = await search_regex(db, query, case_sensitive, [sid], 5000)
                elif mode == SearchMode.morphological:
                    res = await search_morphological(db, query, [sid], 5000)
                else:
                    res = []
                
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
    source_ids_str = request.query_params.get("source_ids")
    if source_ids_str is not None:
        source_ids = [int(sid) for sid in source_ids_str.split(",") if sid.strip()]
    else:
        source_ids = None

    db = await get_db(DB_PATH)
    try:
        limit = 5000
        if mode == SearchMode.plain:
            results = await search_plain(db, query, case_sensitive, whole_word, source_ids, limit)
        elif mode == SearchMode.regex:
            results = await search_regex(db, query, case_sensitive, source_ids, limit)
        elif mode == SearchMode.morphological:
            results = await search_morphological(db, query, source_ids, limit)
        else:
            results = []
            
        limit_reached = len(results) >= limit
        fragment = render_fragment(query, results, limit_reached=limit_reached)
        html = render_standalone(query, fragment)
        
        headers = {"Content-Disposition": f'attachment; filename="{query}.html"'}
        return HTMLResponse(content=html, headers=headers)
    finally:
        await db.close()
