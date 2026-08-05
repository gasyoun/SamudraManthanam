-- 0001 — initial state.db schema (H1927 / Lane D1).
--
-- This is the *baseline* migration. Every statement is IF NOT EXISTS so it is
-- safe to apply to a long-lived production state.db that predates the runner:
-- the tables already exist, the statements no-op, and the DB is adopted into
-- checksum tracking without a dump/restore.
--
-- Carved verbatim out of app.state_db.init_state_db, which now delegates here.

-- Legacy version marker table. Superseded by schema_migrations (written by the
-- runner) and retained only so older tooling that probes it keeps working.
CREATE TABLE IF NOT EXISTS migrations (
    id INTEGER PRIMARY KEY,
    version INTEGER NOT NULL,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS morph_cache (
    query TEXT PRIMARY KEY,
    stems_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    refreshed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS consent (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    consent_type TEXT NOT NULL, -- 'data' or 'marketing'
    granted INTEGER NOT NULL,   -- 0 or 1
    timestamp TEXT NOT NULL,
    ip_hash TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

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

-- AI response cache. `request_hash` includes the system prompt + user prompt +
-- model so a prompt-template change automatically invalidates affected
-- entries. `created_at` is Unix epoch seconds so TTL math needs no ISO parsing.
CREATE TABLE IF NOT EXISTS ai_cache (
    request_hash TEXT PRIMARY KEY,
    task         TEXT NOT NULL,
    response     TEXT NOT NULL, -- JSON payload returned to the caller
    model        TEXT,
    created_at   INTEGER NOT NULL,
    latency_ms   INTEGER
);

CREATE INDEX IF NOT EXISTS idx_ai_cache_created_at ON ai_cache(created_at);
CREATE INDEX IF NOT EXISTS idx_ai_cache_task ON ai_cache(task);
