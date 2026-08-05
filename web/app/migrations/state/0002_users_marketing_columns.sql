-- 0002 — marketing/attribution columns on users (H1927 / Lane D1).
--
-- Previously an inline PRAGMA-gated ALTER loop in init_state_db, re-run on
-- every single startup. A state.db that predates the runner already carries
-- these columns, and SQLite has no conditional ALTER, so each statement
-- declares the one error it may tolerate. Only "duplicate column name" is
-- swallowed, and only for the statement it precedes — see runner.py.

-- @idempotent-error: duplicate column name
ALTER TABLE users ADD COLUMN telegram_username TEXT;

-- @idempotent-error: duplicate column name
ALTER TABLE users ADD COLUMN utm_source TEXT;

-- @idempotent-error: duplicate column name
ALTER TABLE users ADD COLUMN utm_medium TEXT;

-- @idempotent-error: duplicate column name
ALTER TABLE users ADD COLUMN utm_campaign TEXT;
