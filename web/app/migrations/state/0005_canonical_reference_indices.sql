-- 0005 — indices for canonical reference lookups
-- (H1925 Lane B migration 2, absorbed into D1 by H2354).
--
-- CREATE INDEX IF NOT EXISTS is already idempotent; no directive needed.

CREATE INDEX IF NOT EXISTS idx_corrections_canonical
    ON corrections(source_slug, canonical_id);

CREATE INDEX IF NOT EXISTS idx_corrections_ref_status
    ON corrections(ref_status);

CREATE INDEX IF NOT EXISTS idx_legacy_ref_map_canonical
    ON legacy_ref_map(source_slug, canonical_id);
