from typing import List, Dict, Any, Optional
import aiosqlite
from app.models import SearchMode
from app.services.search_service import search_plain, search_regex
from app.services.morph_service import search_morphological

async def dispatch_search(
    db: aiosqlite.Connection, 
    query: str, 
    mode: SearchMode, 
    case_sensitive: bool = False, 
    whole_word: bool = False, 
    source_ids: Optional[List[int]] = None, 
    limit: int = 5000
) -> Dict[str, Any]:
    """
    Unified entry point for all search types.
    Returns a dict with 'results' and optional 'search_metadata'.
    """
    search_metadata = None
    
    if mode == SearchMode.plain:
        results = await search_plain(db, query, case_sensitive, whole_word, source_ids, limit)
    elif mode == SearchMode.regex:
        regex_data = await search_regex(db, query, case_sensitive, source_ids, limit)
        results = regex_data["results"]
        search_metadata = regex_data["search_metadata"]
    elif mode == SearchMode.morphological:
        morph_data = await search_morphological(db, query, source_ids, limit)
        results = morph_data["results"]
        search_metadata = {
            "stems": morph_data["stems"],
            "variants": morph_data["variants"]
        }
    else:
        results = []
        
    return {
        "results": results,
        "search_metadata": search_metadata
    }
