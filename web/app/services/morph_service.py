from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
import httpx
import json
import aiosqlite
import re
from typing import List, Dict, Set

DEVANAGARI_RANGE = range(0x0900, 0x0980)
IAST_MARKERS = set('āīūṛṝḷṃḥñṭḍṇśṣ')

def detect_encoding(word: str) -> str:
    if any(ord(c) in DEVANAGARI_RANGE for c in word):
        return "Devanagari"
    if any(c in IAST_MARKERS for c in word.lower()):
        return "IAST"
    return "SLP1"

def to_slp1(word: str, source_encoding: str) -> str:
    scheme_map = {
        "IAST": sanscript.IAST, 
        "Devanagari": sanscript.DEVANAGARI, 
        "SLP1": sanscript.SLP1
    }
    return transliterate(word, scheme_map[source_encoding], sanscript.SLP1)

def to_all_encodings(slp1_word: str) -> List[str]:
    return [
        transliterate(slp1_word, sanscript.SLP1, sanscript.IAST),
        slp1_word,
        transliterate(slp1_word, sanscript.SLP1, sanscript.DEVANAGARI)
    ]

async def expand_word(slp1_word: str, db: aiosqlite.Connection) -> List[str]:
    # Check cache
    async with db.execute("SELECT stems FROM morph_cache WHERE query = ?", (slp1_word,)) as cursor:
        row = await cursor.fetchone()
        if row:
            return json.loads(row[0])

    # Call Sanskrit Heritage API (Phase 4 Option A)
    # GET https://sanskrit.inria.fr/cgi-bin/SKT/sktlex.cgi?lex=SH&q=<slp1_word>&t=xml
    url = f"https://sanskrit.inria.fr/cgi-bin/SKT/sktlex.cgi?lex=SH&q={slp1_word}&t=xml"
    
    stems = {slp1_word}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5.0)
            if response.status_code == 200:
                # Parse XML for <stem> elements
                # Simple regex parsing to avoid heavy XML libs if possible
                found_stems = re.findall(r'<stem>(.*?)</stem>', response.text)
                for s in found_stems:
                    stems.add(s)
    except Exception as e:
        print(f"Morph expansion error: {e}")

    stems_list = list(stems)
    # Save to cache
    await db.execute("INSERT OR REPLACE INTO morph_cache (query, stems) VALUES (?, ?)", (slp1_word, json.dumps(stems_list)))
    await db.commit()
    
    return stems_list

async def search_morphological(db: aiosqlite.Connection, query: str, source_ids: List[int], limit: int) -> List[Dict]:
    encoding = detect_encoding(query)
    slp1 = to_slp1(query, encoding)
    
    stems = await expand_word(slp1, db)
    
    # Expand each stem to all 3 encodings
    variants = set()
    for s in stems:
        variants.update(to_all_encodings(s))
    
    # Run search for each variant and union
    all_results = []
    seen = set() # (source_id, line_num)
    
    from app.services.search_service import search_plain
    
    for variant in variants:
        res = await search_plain(db, variant, False, False, source_ids, limit)
        for r in res:
            key = (r["source_id"], r["line_num"])
            if key not in seen:
                seen.add(key)
                all_results.append(r)
            if len(all_results) >= limit:
                break
        if len(all_results) >= limit:
            break
            
    return all_results
