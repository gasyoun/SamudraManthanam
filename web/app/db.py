import aiosqlite
import os

async def get_db(db_path: str):
    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row
    return db

async def create_schema(db):
    await db.execute("""
    CREATE TABLE IF NOT EXISTS sources (
        id          INTEGER PRIMARY KEY,
        filename    TEXT    NOT NULL UNIQUE,
        title       TEXT    NOT NULL,
        sort_order  INTEGER NOT NULL DEFAULT 0,
        sha256      TEXT,
        size        INTEGER,
        slug        TEXT,
        title_en    TEXT,
        subtitle    TEXT,
        credit      TEXT,
        credit_role TEXT,
        imprint     TEXT,
        publisher   TEXT,
        year        INTEGER
    );
    """)
    # Migrate existing DBs that were created before these columns existed.
    for _col in [
        "title_en TEXT",
        "subtitle TEXT",
        "credit TEXT",
        "credit_role TEXT",
        "imprint TEXT",
        "publisher TEXT",
        "year INTEGER",
    ]:
        try:
            await db.execute(f"ALTER TABLE sources ADD COLUMN {_col}")
        except Exception:
            pass  # column already present
    # Unique index on slug. `IF NOT EXISTS` + nullable column means existing
    # DBs without slugs populated yet won't violate the constraint at startup;
    # the lifespan backfill fills them in before serving slug URLs.
    await db.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_sources_slug
        ON sources(slug) WHERE slug IS NOT NULL AND slug != ''
    """)

    # Migrate FTS5 table if canonical_id column is absent (LINE_ID_SCHEME §6).
    # FTS5 virtual tables cannot be altered — drop and recreate; ingest will repopulate.
    async with db.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='corpus_lines'"
    ) as _cur:
        _fts_row = await _cur.fetchone()
    if _fts_row and "canonical_id" not in (_fts_row[0] or ""):
        await db.execute("DROP TABLE IF EXISTS corpus_lines")

    await db.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS corpus_lines USING fts5(
        line_text,               -- HTML-stripped plain text (what is searched)
        line_html    UNINDEXED,  -- Original HTML line (what is displayed)
        source_id    UNINDEXED,
        line_num     UNINDEXED,
        link_id      UNINDEXED,  -- value of id= attribute on the line, if present
        chapter      UNINDEXED,  -- current H1 heading at point of line
        canonical_id UNINDEXED,  -- LINE_ID_SCHEME canonical ID (nullable until JSONL ingest)
        tokenize="unicode61"     -- Support for IAST diacritics
    );
    """)

    await db.execute("""
    CREATE TABLE IF NOT EXISTS morph_cache (
        query  TEXT PRIMARY KEY,
        stems  TEXT NOT NULL    -- JSON: ["stem1","stem2",...]
    );
    """)
    
    # Enable WAL mode for better concurrency
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("""
    CREATE TABLE IF NOT EXISTS corpus_meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    """)
    
    await db.commit()
