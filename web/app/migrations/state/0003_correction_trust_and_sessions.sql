-- 0003 — correction trust tiers, verified sessions, audit and rate limits
-- (H1926 / Lane C4, C7).
--
-- Splits correction intake into an anonymous low-trust path and a verified one,
-- and gives the verified path something to be verified BY. Before this, the
-- proposal endpoint resolved the email address in the request body against the
-- users table and attached the matching account — so typing a known scholar's
-- address filed corrections under their name. `user_id` is now written only
-- from a redeemed session; a submitted address lands in `contact_email` and
-- grants nothing.
--
-- Contract: web/IDENTITY_TRUST_CONTRACT.md.

-- Trust evidence on each correction. Existing rows default to 'anonymous',
-- which is the correct reading: none of them carried verified identity, since
-- no verification path existed when they were written.
-- @idempotent-error: duplicate column name
ALTER TABLE corrections ADD COLUMN trust_tier TEXT NOT NULL DEFAULT 'anonymous';

-- @idempotent-error: duplicate column name
ALTER TABLE corrections ADD COLUMN actor_ip_hash TEXT;

-- Self-declared contact text. NOT identity — see the header note.
-- @idempotent-error: duplicate column name
ALTER TABLE corrections ADD COLUMN contact_email TEXT;

-- Canonical corpus identity of the corrected line, so an audit row survives a
-- rebuild that renumbers ordinals.
-- @idempotent-error: duplicate column name
ALTER TABLE corrections ADD COLUMN link_id TEXT;

-- @idempotent-error: duplicate column name
ALTER TABLE corrections ADD COLUMN corpus_version TEXT;

-- Single-use email-verification challenges. Only token HASHES are stored, so a
-- leaked state.db yields no usable challenge.
CREATE TABLE IF NOT EXISTS email_verifications (
    token_hash  TEXT PRIMARY KEY,
    user_id     INTEGER NOT NULL,
    created_at  TEXT NOT NULL,
    expires_at  TEXT NOT NULL,
    redeemed_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Redeemed sessions — the only thing that grants verified attribution.
CREATE TABLE IF NOT EXISTS user_sessions (
    token_hash TEXT PRIMARY KEY,
    user_id    INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);

-- Append-only audit of correction-lifecycle actions. Every row names the
-- actor's trust tier, so a reviewer can tell an anonymous proposal from a
-- verified one without re-deriving it from absent evidence.
CREATE TABLE IF NOT EXISTS correction_audit (
    id            INTEGER PRIMARY KEY,
    correction_id INTEGER,
    action        TEXT NOT NULL,
    trust_tier    TEXT NOT NULL,
    actor_user_id INTEGER,
    actor_ip_hash TEXT,
    link_id       TEXT,
    created_at    TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_correction_audit_correction
    ON correction_audit(correction_id);

-- Fixed-window rate-limit counters (app/services/rate_limit.py). Kept in the
-- database rather than a process dict because the app runs multiple workers,
-- and a per-process counter silently multiplies the real limit by the worker
-- count — a limit that is not the limit reads as protection while being none.
CREATE TABLE IF NOT EXISTS rate_limits (
    bucket       TEXT NOT NULL,
    key          TEXT NOT NULL,
    window_start INTEGER NOT NULL,
    count        INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (bucket, key, window_start)
);
