import pytest
import pytest_asyncio
import os
import aiosqlite
import asyncio
from app.db import create_schema
from app.settings import settings

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def test_db(tmp_path_factory):
    if os.environ.get("USE_REAL_CORPUS"):
        return settings.DB_PATH

    # Create a temporary DB file
    tmp_dir = tmp_path_factory.mktemp("db")
    db_path = str(tmp_dir / "test_corpus.db")
    
    # Override settings
    settings.DB_PATH = db_path
    
    db = await aiosqlite.connect(db_path)
    await create_schema(db)
    
    # Seed data
    # 2 sources, each with a slug populated so /sources/{slug} routes work
    # without going through the lifespan backfill in tests.
    await db.execute(
        "INSERT INTO sources (id, filename, title, sort_order, slug) "
        "VALUES (1, 'source1.html', 'Source 1', 1, 'source1')"
    )
    await db.execute(
        "INSERT INTO sources (id, filename, title, sort_order, slug) "
        "VALUES (2, 'source2.html', 'Source 2', 2, 'source2')"
    )
    
    # Sanskrit/IAST text
    await db.execute("""
        INSERT INTO corpus_lines (line_text, line_html, source_id, line_num, link_id, chapter)
        VALUES ('svasti arjuna', '<p>svasti arjuna</p>', 1, 10, '1.10', 'Chapter 1')
    """)
    await db.execute("""
        INSERT INTO corpus_lines (line_text, line_html, source_id, line_num, link_id, chapter)
        VALUES ('sat tat', '<p>sat tat</p>', 1, 11, '1.11', 'Chapter 1')
    """)
    
    # Russian line
    await db.execute("""
        INSERT INTO corpus_lines (line_text, line_html, source_id, line_num, link_id, chapter)
        VALUES ('Привет мир быть', '<p>Привет мир быть</p>', 2, 1, '2.1', 'Глава 1')
    """)
    
    # Line with HTML tags and id
    await db.execute("""
        INSERT INTO corpus_lines (line_text, line_html, source_id, line_num, link_id, chapter)
        VALUES ('tagged line', '<p id="tag1">tagged <b>line</b></p>', 2, 2, 'tag1', 'Глава 1')
    """)
    
    await db.commit()
    await db.close()
    
    return db_path

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db(test_db):
    # Ensure settings.DB_PATH is always pointing to test_db for every test
    settings.DB_PATH = test_db
