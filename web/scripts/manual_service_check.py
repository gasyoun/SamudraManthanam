import asyncio
import os
import sys

# Add app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db import get_db
from app.services.search_service import search_plain, search_regex
from app.services.morph_service import search_morphological, detect_encoding, to_slp1

async def run_tests():
    db_path = "corpus.db"
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found. Please run ingestion first.")
        return

    db = await get_db(db_path)
    
    print("--- Testing Plain Search ---")
    results = await search_plain(db, "Арджун", case_sensitive=False, whole_word=False, source_ids=None, limit=10)
    print(f"Found {len(results)} results for 'Арджун'")
    if results:
        print(f"First result: {results[0]['source_title']} - {results[0]['chapter']}")

    print("\n--- Testing Regex Search ---")
    results = await search_regex(db, "Арджун.*Кришна", case_sensitive=False, source_ids=None, limit=10)
    print(f"Found {len(results)} results for 'Арджун.*Кришна'")

    print("\n--- Testing Encoding Detection ---")
    print(f"arjuna -> {detect_encoding('arjuna')}")
    print(f"arjunat -> {detect_encoding('arjuṇat')}")
    print(f"arjuna (dev) -> {detect_encoding('अर्जुन')}")

    print("\n--- Testing Morphological Search (IAST) ---")
    # This might take time as it calls the Heritage API
    try:
        results = await search_morphological(db, "arjuna", source_ids=None, limit=10)
        print(f"Found {len(results)} results for morphological 'arjuna'")
    except Exception as e:
        print(f"Morph search failed (likely API timeout): {e}")

    await db.close()

if __name__ == "__main__":
    asyncio.run(run_tests())
