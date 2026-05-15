import aiosqlite
import datetime
from app.settings import settings

async def get_state_db():
    """Returns an async connection to the state database."""
    if not settings.STATE_DB_PATH:
        return None
    db = await aiosqlite.connect(settings.STATE_DB_PATH)
    db.row_factory = aiosqlite.Row
    return db

async def init_state_db(db):
    """Initializes the state database schema."""
    await db.execute("""
    CREATE TABLE IF NOT EXISTS migrations (
        id INTEGER PRIMARY KEY,
        version INTEGER NOT NULL,
        applied_at TEXT NOT NULL
    );
    """)

    await db.execute("""
    CREATE TABLE IF NOT EXISTS morph_cache (
        query TEXT PRIMARY KEY,
        stems_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        refreshed_at TEXT NOT NULL
    );
    """)

    await db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        name TEXT,
        telegram_username TEXT,
        utm_source TEXT,
        utm_medium TEXT,
        utm_campaign TEXT,
        created_at TEXT NOT NULL
    );
    """)

    # Idempotent migration: add columns to pre-existing users tables
    async with db.execute("PRAGMA table_info(users)") as cursor:
        existing_cols = {row[1] for row in await cursor.fetchall()}
    for col in ("telegram_username", "utm_source", "utm_medium", "utm_campaign"):
        if col not in existing_cols:
            await db.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")

    await db.execute("""
    CREATE TABLE IF NOT EXISTS consent (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        consent_type TEXT NOT NULL, -- 'data' or 'marketing'
        granted INTEGER NOT NULL,    -- 0 or 1
        timestamp TEXT NOT NULL,
        ip_hash TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """)

    await db.execute("""
    CREATE TABLE IF NOT EXISTS corrections (
        id INTEGER PRIMARY KEY,
        source_id INTEGER NOT NULL,
        line_num INTEGER NOT NULL,
        old_text TEXT NOT NULL,
        new_text TEXT NOT NULL,
        user_id INTEGER, -- optional
        status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'applied', 'rejected'
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """)
    
    await db.execute("PRAGMA journal_mode=WAL")
    await db.commit()
