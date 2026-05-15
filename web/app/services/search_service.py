import re
import aiosqlite
import time
from typing import List, Dict, Any, Optional

def escape_fts(term: str, whole_word: bool = False) -> str:
    tokens = [t for t in term.split() if t]
    if not tokens:
        safe = term.replace('"', '""')
        return f'"{safe}"' if whole_word else f'"{safe}"*'
    parts = []
    for token in tokens:
        safe = token.replace('"', '""')
        # whole_word: exact token match (no prefix *); prefix mode: trailing *
        parts.append(f'"{safe}"' if whole_word else f'"{safe}"*')
    return " AND ".join(parts)

async def search_plain(db: aiosqlite.Connection, query: str, case_sensitive: bool, whole_word: bool, source_ids: Optional[List[int]], limit: int) -> List[Dict[str, Any]]:
    queries = [q.strip() for q in query.split('\n') if q.strip()]
    if not queries:
        return []

    fts_parts = [escape_fts(q, whole_word) for q in queries]
    fts_query = " OR ".join(fts_parts)

    source_filter = ""
    params = [fts_query]

    if source_ids is not None:
        if len(source_ids) == 0:
            return []
        placeholders = ",".join("?" * len(source_ids))
        source_filter = f"AND source_id IN ({placeholders})"
        params.extend(source_ids)

    needs_python_filter = case_sensitive or whole_word
    if needs_python_filter:
        # Over-fetch so Python filtering can still fill `limit` results.
        # FTS5 returns case-insensitive candidates; Python narrows to correct case/boundary.
        sql_limit = min(limit * 10, 50000)
    else:
        sql_limit = limit
    params.append(sql_limit)

    sql = f"""
        SELECT cl.source_id, s.title as source_title, cl.line_num, cl.link_id, cl.chapter, cl.line_html, cl.line_text
        FROM corpus_lines cl
        JOIN sources s ON cl.source_id = s.id
        WHERE corpus_lines MATCH ?
        {source_filter}
        ORDER BY s.sort_order, cl.line_num
        LIMIT ?
    """

    async with db.execute(sql, params) as cursor:
        rows = await cursor.fetchall()
        results = [dict(row) for row in rows]

    if not needs_python_filter:
        return results

    filtered = []
    for r in results:
        text = r["line_text"]
        matched = False
        for q in queries:
            words = [t for t in q.split() if t]
            if not words:
                continue
            if whole_word:
                # Each token must appear as a whole word independently (not as a phrase)
                if all(
                    re.search(rf'\b{re.escape(w)}\b', text, 0 if case_sensitive else re.IGNORECASE)
                    for w in words
                ):
                    matched = True
                    break
            else:
                # case_sensitive=True, whole_word=False: each token as case-sensitive substring
                if all(w in text for w in words):
                    matched = True
                    break
        if matched:
            filtered.append(r)
            if len(filtered) >= limit:
                break
    return filtered

async def search_regex(db: aiosqlite.Connection, pattern: str, case_sensitive: bool, source_ids: Optional[List[int]], limit: int) -> List[Dict[str, Any]]:
    # Handle multi-line patterns
    patterns = [p.strip() for p in pattern.split('\n') if p.strip()]
    if not patterns:
        return []
        
    flags = 0 if case_sensitive else re.IGNORECASE
    compiled_patterns = []
    for p in patterns:
        try:
            compiled_patterns.append(re.compile(p, flags))
        except re.error:
            continue
            
    if not compiled_patterns:
        return []
        
    source_filter = ""
    params = []
    if source_ids is not None:
        if len(source_ids) == 0:
            return []
        source_filter = f"WHERE source_id IN ({','.join('?'*len(source_ids))})"
        params.extend(source_ids)
        
    sql = f"""
        SELECT cl.source_id, s.title as source_title, cl.line_num, cl.link_id, cl.chapter, cl.line_html, cl.line_text
        FROM corpus_lines cl
        JOIN sources s ON cl.source_id = s.id
        {source_filter}
        ORDER BY s.sort_order, cl.line_num
    """
    
    results = []
    start_time = time.time()
    MAX_TIME = 5.0 # seconds
    
    async with db.execute(sql, params) as cursor:
        async for row in cursor:
            # Check timeout
            if time.time() - start_time > MAX_TIME:
                break
            matched = False
            for cp in compiled_patterns:
                if cp.search(row["line_text"]):
                    matched = True
                    break
            
            if matched:
                results.append(dict(row))
                if len(results) >= limit:
                    break
    return results
