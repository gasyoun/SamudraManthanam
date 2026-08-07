-- 0004 — canonical reference columns + legacy_ref_map
-- (H1925 Lane B, absorbed into D1 by H2354).
--
-- Adds durable corpus identity on corrections so a rebuild that renumbers
-- ordinals does not orphan the row, plus the mapping table used by the
-- backfill that converts a stored (corpus_version, source_id, line_num)
-- into (source_slug, canonical_id).
--
-- Every ALTER uses the per-statement @idempotent-error directive: production
-- state.db files may already carry these columns from the pre-absorb
-- canonical_state_migrations runner (canonical_ref_migrations ledger). That
-- path is bridged into schema_migrations at startup; the directives also
-- cover the race where 0003 already added corpus_version.

-- @idempotent-error: duplicate column name
ALTER TABLE corrections ADD COLUMN source_slug TEXT;

-- @idempotent-error: duplicate column name
ALTER TABLE corrections ADD COLUMN canonical_id TEXT;

-- How the stored reference was resolved when the row was written or
-- backfilled: one of canonical / legacy_mapped / legacy_direct / unresolved.
-- Keeps an un-backfillable row visible instead of letting it look canonical.
-- @idempotent-error: duplicate column name
ALTER TABLE corrections ADD COLUMN ref_status TEXT;

-- corpus_version may already exist from 0003 (link_id cohort). Tolerate.
-- @idempotent-error: duplicate column name
ALTER TABLE corrections ADD COLUMN corpus_version TEXT;

CREATE TABLE IF NOT EXISTS legacy_ref_map (
    corpus_version TEXT    NOT NULL,
    source_id      INTEGER NOT NULL,
    line_num       INTEGER NOT NULL,
    source_slug    TEXT    NOT NULL,
    canonical_id   TEXT    NOT NULL,
    fingerprint    TEXT,
    created_at     TEXT    NOT NULL,
    PRIMARY KEY (corpus_version, source_id, line_num)
);
