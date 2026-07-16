import datetime
import logging
import re
import json
import aiosqlite
import httpx
from typing import List, Dict, Set, Optional, Any

from app.settings import settings
from app.vendor import sanskrit_util as _su

logger = logging.getLogger(__name__)

DEVANAGARI_RANGE = range(0x0900, 0x0980)
IAST_MARKERS = set('āīūṛṝḷṃḥñṭḍṇśṣ')

def detect_encoding(word: str) -> str:
    if any(ord(c) in DEVANAGARI_RANGE for c in word):
        return "Devanagari"
    if any(c in IAST_MARKERS for c in word.lower()):
        return "IAST"
    return "SLP1"

def to_slp1(word: str, source_encoding: str) -> str:
    if source_encoding == "IAST":
        return _su.to_slp1(word)
    if source_encoding == "Devanagari":
        return _su.deva_to_slp1(word)
    return word  # already SLP1

def to_all_encodings(slp1_word: str) -> List[str]:
    return [
        _su.from_slp1(slp1_word),
        slp1_word,
        _su.slp1_to_devanagari(slp1_word)
    ]

async def _cache_read(slp1_word: str) -> Optional[List[str]]:
    """Return cached stems from state.db, or None on miss/unavailable."""
    if not settings.STATE_DB_PATH:
        return None
    try:
        async with aiosqlite.connect(settings.STATE_DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT stems_json FROM morph_cache WHERE query = ?", (slp1_word,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return json.loads(row["stems_json"])
    except Exception as e:
        logger.warning("morph cache read failed for '%s': %s", slp1_word, e)
    return None

async def _cache_write(slp1_word: str, stems: List[str]) -> None:
    """Write stems to state.db morph_cache. Failures are non-fatal."""
    if not settings.STATE_DB_PATH:
        return
    now = datetime.datetime.now().isoformat()
    try:
        async with aiosqlite.connect(settings.STATE_DB_PATH) as db:
            await db.execute(
                """INSERT OR REPLACE INTO morph_cache
                   (query, stems_json, created_at, refreshed_at)
                   VALUES (?, ?, ?, ?)""",
                (slp1_word, json.dumps(stems), now, now)
            )
            await db.commit()
    except Exception as e:
        logger.warning("morph cache write failed for '%s': %s", slp1_word, e)

async def expand_word(slp1_word: str) -> List[str]:
    """
    Return a list of morphological stems for slp1_word.
    Tries state.db cache first; falls back to Sanskrit Heritage API.
    Always returns at least [slp1_word] even when the API is unreachable.
    """
    cached = await _cache_read(slp1_word)
    if cached is not None:
        return cached

    # Pass query params through httpx so '&' / '=' / unicode are safely encoded.
    url = "https://sanskrit.inria.fr/cgi-bin/SKT/sktlex.cgi"
    params = {"lex": "SH", "q": slp1_word, "t": "xml"}
    stems: Set[str] = {slp1_word}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=5.0)
            if response.status_code == 200:
                for s in re.findall(r'<stem>(.*?)</stem>', response.text):
                    stems.add(s)
    except Exception as e:
        logger.warning("Sanskrit Heritage lookup failed for '%s': %s", slp1_word, e)

    stems_list = list(stems)
    await _cache_write(slp1_word, stems_list)
    return stems_list

async def search_morphological(
    db: aiosqlite.Connection,
    query: str,
    source_ids: Optional[List[int]],
    limit: int,
) -> Dict[str, Any]:
    queries = [q.strip() for q in query.split('\n') if q.strip()]
    if not queries:
        return {"results": [], "stems": [], "variants": []}
    if source_ids is not None and len(source_ids) == 0:
        return {"results": [], "stems": [], "variants": []}

    variants: Set[str] = set()
    all_stems: Set[str] = set()
    for q in queries:
        encoding = detect_encoding(q)
        slp1 = to_slp1(q, encoding)
        stems = await expand_word(slp1)
        all_stems.update(stems)
        for s in stems:
            variants.update(to_all_encodings(s))

    from app.services.search_service import search_plain

    all_results = []
    seen: Set[tuple] = set()
    for variant in sorted(variants):
        for r in await search_plain(db, variant, False, False, source_ids, limit):
            key = (r["source_id"], r["line_num"])
            if key not in seen:
                seen.add(key)
                all_results.append(r)
            if len(all_results) >= limit:
                break
        if len(all_results) >= limit:
            break

    return {
        "results": all_results,
        "stems": sorted(all_stems),
        "variants": sorted(variants),
    }
