import aiosqlite
import time
from typing import List, Dict, Any, Optional

# Prefer the third-party `regex` engine when available: it supports a genuine
# per-match `timeout=` that aborts catastrophic backtracking mid-call.
# stdlib `re` has no per-call timeout — its only wall-clock check sits BETWEEN
# rows, so a single pathological pattern vs one line can hang the event loop
# (H1830). Fall back to stdlib re only when `regex` is not installed; that path
# still has the between-row budget but is not fully ReDoS-safe.
try:
    import regex as _re_engine  # type: ignore
    _HAS_REGEX_TIMEOUT = True
except ImportError:  # pragma: no cover - exercised only when regex missing
    import re as _re_engine  # type: ignore
    _HAS_REGEX_TIMEOUT = False

import re as _stdlib_re  # always available for escape_fts / whole-word filters

# Per-match wall-clock budget for user-supplied regex (seconds).
# Well under the 5s whole-scan MAX_TIME and the H1830 <2s regression bound.
_REGEX_MATCH_TIMEOUT = 0.05


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
        SELECT cl.source_id, s.title as source_title, s.filename as source_filename,
               cl.line_num, cl.link_id, cl.chapter, cl.line_html, cl.line_text
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
                    _stdlib_re.search(rf'\b{_stdlib_re.escape(w)}\b', text, 0 if case_sensitive else _stdlib_re.IGNORECASE)
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


def _compile_user_regex(pattern: str, flags: int):
    """Compile a user-supplied pattern with the timeout-capable engine."""
    return _re_engine.compile(pattern, flags)


def _regex_search(compiled, text: str) -> bool:
    """Search with a genuine per-match timeout when the engine supports it.

    On timeout (catastrophic backtracking) treat as non-match and let the
    outer scan continue — the between-row MAX_TIME budget still bounds the
    whole request.
    """
    if not text:
        return False
    try:
        if _HAS_REGEX_TIMEOUT:
            return compiled.search(text, timeout=_REGEX_MATCH_TIMEOUT) is not None
        return compiled.search(text) is not None
    except TimeoutError:
        # regex package raises TimeoutError when timeout= is exceeded.
        return False
    except Exception:
        # Other engine errors (e.g. interrupted) → non-match, keep scanning.
        return False


async def search_regex(db: aiosqlite.Connection, pattern: str, case_sensitive: bool, source_ids: Optional[List[int]], limit: int) -> Dict[str, Any]:
    # Handle multi-line patterns
    patterns = [p.strip() for p in pattern.split('\n') if p.strip()]
    if not patterns:
        return {"results": [], "search_metadata": None}

    flags = 0 if case_sensitive else _re_engine.IGNORECASE
    compiled_patterns = []
    for p in patterns:
        try:
            compiled_patterns.append(_compile_user_regex(p, flags))
        except (_re_engine.error, _stdlib_re.error):
            continue

    if not compiled_patterns:
        return {"results": [], "search_metadata": None}

    source_filter = ""
    params = []
    if source_ids is not None:
        if len(source_ids) == 0:
            return {"results": [], "search_metadata": None}
        source_filter = f"WHERE source_id IN ({','.join('?'*len(source_ids))})"
        params.extend(source_ids)

    sql = f"""
        SELECT cl.source_id, s.title as source_title, s.filename as source_filename,
               cl.line_num, cl.link_id, cl.chapter, cl.line_html, cl.line_text
        FROM corpus_lines cl
        JOIN sources s ON cl.source_id = s.id
        {source_filter}
        ORDER BY s.sort_order, cl.line_num
    """

    results = []
    start_time = time.time()
    MAX_TIME = 5.0 # seconds
    MAX_SCANNED_ROWS = 1000000 # 1M rows budget

    scanned_rows = 0
    timeout = False
    budget_exceeded = False

    async with db.execute(sql, params) as cursor:
        async for row in cursor:
            scanned_rows += 1
            if time.time() - start_time > MAX_TIME:
                timeout = True
                break
            if scanned_rows > MAX_SCANNED_ROWS:
                budget_exceeded = True
                break

            matched = False
            for cp in compiled_patterns:
                if _regex_search(cp, row["line_text"]):
                    matched = True
                    break

            if matched:
                results.append(dict(row))
                if len(results) >= limit:
                    break

    return {
        "results": results,
        "search_metadata": {
            "scanned_rows": scanned_rows,
            "timeout": timeout,
            "budget_exceeded": budget_exceeded,
            "truncated": timeout or budget_exceeded
        }
    }
