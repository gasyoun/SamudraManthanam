import aiosqlite
import logging
import time
from typing import List, Dict, Any, Optional

import re as _stdlib_re  # escape_fts / whole-word filters (never user patterns)

# H1926: every bound on user-supplied regex — engine choice, per-match timeout,
# hard deadline, pattern caps, stable error codes — lives in one module.
from app.services.regex_executor import (
    HARD_DEADLINE_SECONDS,
    MAX_SCANNED_ROWS,
    BoundedRegexExecutor,
    ScanStats,
)

logger = logging.getLogger(__name__)


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

    # s.slug / cl.canonical_id are the canonical half of every result's identity
    # (H1925, Lane B B2). They ride along with the ordinal fields rather than
    # replacing them — see app/canonical_refs.py for why the ordinals alone
    # cannot survive a corpus rebuild.
    sql = f"""
        SELECT cl.source_id, s.title as source_title, s.filename as source_filename,
               s.slug as source_slug, cl.canonical_id,
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


async def search_regex(db: aiosqlite.Connection, pattern: str, case_sensitive: bool, source_ids: Optional[List[int]], limit: int) -> Dict[str, Any]:
    """Scan the corpus with user-supplied patterns under published bounds.

    Raises :class:`RegexContractError` for a pattern the contract refuses (bad
    syntax, over-long, too many, or no timeout-capable engine installed) so the
    route can answer with a stable error instead of an empty result set that
    looks like a legitimate "no hits".
    """
    # Handle multi-line patterns
    patterns = [p.strip() for p in pattern.split('\n') if p.strip()]
    if not patterns:
        return {"results": [], "search_metadata": None}

    # Raises RegexContractError; deliberately NOT caught here.
    executor = BoundedRegexExecutor.compile_patterns(patterns, case_sensitive)

    source_filter = ""
    params = []
    if source_ids is not None:
        if len(source_ids) == 0:
            return {"results": [], "search_metadata": None}
        source_filter = f"WHERE source_id IN ({','.join('?'*len(source_ids))})"
        params.extend(source_ids)

    sql = f"""
        SELECT cl.source_id, s.title as source_title, s.filename as source_filename,
               s.slug as source_slug, cl.canonical_id,
               cl.line_num, cl.link_id, cl.chapter, cl.line_html, cl.line_text
        FROM corpus_lines cl
        JOIN sources s ON cl.source_id = s.id
        {source_filter}
        ORDER BY s.sort_order, cl.line_num
    """

    results = []
    start_time = time.time()
    stats = ScanStats()

    async with db.execute(sql, params) as cursor:
        async for row in cursor:
            stats.scanned_rows += 1
            # H1926 C1: hard wall-clock deadline (was a 5 s soft budget). The
            # per-match timeout bounds one match; this bounds the whole scan.
            if time.time() - start_time > HARD_DEADLINE_SECONDS:
                stats.deadline_exceeded = True
                break
            if stats.scanned_rows > MAX_SCANNED_ROWS:
                stats.budget_exceeded = True
                break

            if executor.matches(row["line_text"], stats):
                results.append(dict(row))
                if len(results) >= limit:
                    break

    return {"results": results, "search_metadata": stats.as_metadata()}
