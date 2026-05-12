import re
import aiosqlite
from typing import List, Dict, Any, Optional

async def search_plain(db: aiosqlite.Connection, query: str, case_sensitive: bool, whole_word: bool, source_ids: Optional[List[int]], limit: int) -> List[Dict[str, Any]]:
    # Handle multi-line queries
    queries = [q.strip() for q in query.split('\n') if q.strip()]
    if not queries:
        return []
    
    # Build FTS5 query string
    # We combine multiple lines with OR
    fts_parts = []
    for q in queries:
        part = f'"{q}"' if whole_word else q
        fts_parts.append(part)
    
    fts_query = " OR ".join(fts_parts)
    
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
    
    if case_sensitive:
        # For multi-word, we need to check if ANY of the words match with case sensitivity
        # This is a bit tricky with LIKE, but we can do it row by row or just use a regex check in Python
        # For performance, we'll fetch rows and filter in Python if case_sensitive is True
        pass

    async with db.execute(sql, params) as cursor:
        rows = await cursor.fetchall()
        results = [dict(row) for row in rows]
        
    if case_sensitive:
        import re
        filtered = []
        # Create a combined regex for all sub-queries
        patterns = [re.escape(q) for q in queries]
        combined_pattern = re.compile("|".join(patterns))
        for r in results:
            if combined_pattern.search(r["line_text"]):
                filtered.append(r)
        return filtered
        
    return results

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
