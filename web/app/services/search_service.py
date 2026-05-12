import re
import aiosqlite
from typing import List, Dict, Any, Optional

def escape_fts(term: str) -> str:
    # Remove characters that have special meaning in FTS5
    # and wrap in quotes.
    safe = term.replace('"', '""')
    return f'"{safe}"'

async def search_plain(db: aiosqlite.Connection, query: str, case_sensitive: bool, whole_word: bool, source_ids: Optional[List[int]], limit: int) -> List[Dict[str, Any]]:
    # Handle multi-line queries
    queries = [q.strip() for q in query.split('\n') if q.strip()]
    if not queries:
        return []
    
    # Build FTS5 query string using OR for multiple lines
    # Each term is escaped and quoted to prevent FTS5 syntax errors
    fts_parts = [escape_fts(q) for q in queries]
    fts_query = " OR ".join(fts_parts)
    
    source_filter = ""
    params = [fts_query]
    
    if source_ids is not None:
        # If source_ids is empty list, the query should return nothing (P1-6)
        if len(source_ids) == 0:
            return []
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
    
    async with db.execute(sql, params) as cursor:
        rows = await cursor.fetchall()
        results = [dict(row) for row in rows]
        
    # Apply reliable Python-side filtering for case sensitivity and whole word
    if case_sensitive or whole_word:
        filtered = []
        for r in results:
            text = r["line_text"]
            match = False
            for q in queries:
                if whole_word:
                    # Simple whole word check using boundaries
                    pattern = rf'\b{re.escape(q)}\b'
                    if re.search(pattern, text, 0 if case_sensitive else re.IGNORECASE):
                        match = True
                        break
                else:
                    if case_sensitive:
                        if q in text:
                            match = True
                            break
                    else:
                        if q.lower() in text.lower():
                            match = True
                            break
            if match:
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
