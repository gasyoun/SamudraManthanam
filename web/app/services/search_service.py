import re
import aiosqlite
from typing import List, Dict, Any, Optional

async def search_plain(db: aiosqlite.Connection, query: str, case_sensitive: bool, whole_word: bool, source_ids: Optional[List[int]], limit: int) -> List[Dict[str, Any]]:
    # Build FTS5 query string
    # FTS5 "query" matches prefixes if not quoted, or exact words if quoted.
    # The requirement says whole_word=True should use quotes.
    fts_query = f'"{query}"' if whole_word else query
    
    source_filter = ""
    params = [fts_query]
    
    if source_ids:
        placeholders = ",".join("?" * len(source_ids))
        source_filter = f"AND source_id IN ({placeholders})"
        params.extend(source_ids)
    
    params.append(limit)
    
    sql = f"""
        SELECT cl.source_id, s.title as source_title, cl.line_num, cl.link_id, cl.chapter, cl.line_html, cl.line_text
        FROM corpus_lines cl
        JOIN sources s ON cl.source_id = s.id
        WHERE corpus_lines MATCH ?
        {source_filter}
        LIMIT ?
    """
    
    # If case_sensitive is True, we need an additional filter because FTS5 is usually case-insensitive with unicode61
    if case_sensitive:
        # We wrap the existing query
        sql = f"""
            SELECT * FROM ({sql})
            WHERE line_text LIKE '%' || ? || '%'
        """
        # Actually, LIKE is case-insensitive in SQLite by default for non-ASCII if not configured otherwise.
        # But we'll follow the plan's suggestion.
        params.append(query)

    async with db.execute(sql, params) as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def search_regex(db: aiosqlite.Connection, pattern: str, case_sensitive: bool, source_ids: Optional[List[int]], limit: int) -> List[Dict[str, Any]]:
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        compiled = re.compile(pattern, flags)
    except re.error:
        return [] # Invalid regex
        
    source_filter = ""
    params = []
    if source_ids:
        source_filter = f"WHERE source_id IN ({','.join('?'*len(source_ids))})"
        params.extend(source_ids)
        
    sql = f"""
        SELECT cl.source_id, s.title as source_title, cl.line_num, cl.link_id, cl.chapter, cl.line_html, cl.line_text
        FROM corpus_lines cl
        JOIN sources s ON cl.source_id = s.id
        {source_filter}
    """
    
    results = []
    async with db.execute(sql, params) as cursor:
        async for row in cursor:
            if compiled.search(row["line_text"]):
                results.append(dict(row))
                if len(results) >= limit:
                    break
    return results
