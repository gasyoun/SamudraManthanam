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


#: Prices for the fake models the test-suite talks to. Real numbers are a
#: deployment concern (`AI_MODEL_PRICES`); these exist only so the H2866
#: spend policy can price a mocked call. Deliberately cheap so the default
#: ceiling is not the thing under test unless a test says so.
TEST_MODEL_PRICES = {
    "currency": "USD",
    "models": {
        "gpt-4-mock": {"input_per_1m": 0.15, "output_per_1m": 0.60},
        "gpt-3.5-turbo": {"input_per_1m": 0.50, "output_per_1m": 1.50},
        "local-model": {"input_per_1m": 0.0, "output_per_1m": 0.0},
    },
}


@pytest.fixture
def ai_policy_allowed():
    """Enable the H2866 paid-AI policy for one test, then restore it.

    Paid AI is deny-by-default (`AI_ENABLED=False`, no configured prices),
    so any test that expects a mocked provider call to actually happen must
    opt in through this fixture. That is the point: forgetting it makes the
    call fail closed, not silently bill. Tests that assert the *rejection*
    behaviour set the settings themselves and must not use this fixture.
    """
    import json as _json

    saved = {
        name: getattr(settings, name)
        for name in (
            "AI_ENABLED",
            "AI_MODEL_PRICES",
            "AI_MAX_OUTPUT_TOKENS",
            "AI_MAX_COST_PER_CALL",
            "AI_COST_CURRENCY",
        )
    }
    settings.AI_ENABLED = True
    settings.AI_MODEL_PRICES = _json.dumps(TEST_MODEL_PRICES)
    settings.AI_MAX_OUTPUT_TOKENS = 1024
    settings.AI_MAX_COST_PER_CALL = 0.05
    settings.AI_COST_CURRENCY = "USD"
    try:
        yield settings
    finally:
        for name, value in saved.items():
            setattr(settings, name, value)
