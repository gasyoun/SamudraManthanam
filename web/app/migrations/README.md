# State migrations

_Created: 05-08-2026 · Last updated: 07-08-2026_

Ordered, checksum-tracked SQL migrations for the mutable `state.db`, plus the
policy that keeps the generated `corpus.db` out of the migration business
entirely. Introduced by [H1927](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1927-Opus_SamudraManthanam_runtime-migrations-dual-deploy_30.07.26.md)
(Lane D1/D2 of [IMPLEMENTATION_SAMUDRAMANTHANAM_ARCHITECTURE_INTEGRITY.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/IMPLEMENTATION_SAMUDRAMANTHANAM_ARCHITECTURE_INTEGRITY.md));
canonical-reference steps from [H1925](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1925-Opus_SamudraManthanam_durable-reference-zero-orphan_30.07.26.md)
were absorbed into this same runner by [H2354](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2354-Grok_SamudraManthanam_absorb-canonical-ref-migrations-into-d1_07.08.26.md).

## Two databases, two policies

| DB | Policy | Why |
|---|---|---|
| `state.db` | Ordered migrations, checksums recorded, applied once | Holds users, consent, corrections, AI cache — none of it regenerable |
| `corpus.db` | **Rebuild, never migrate in place** | Fully generated from the canonical JSONL corpus; an in-place edit produces a DB that matches no manifest |

The corpus half is enforced by [`corpus_policy.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/migrations/corpus_policy.py):
a declared `CORPUS_SCHEMA_VERSION` and a startup probe that reports which side
is stale. It never mutates and never raises — a corpus mismatch degrades, it
does not take search down.

## Adding a migration

1. Create `state/NNNN_short_slug.sql` with the next free number (`0003`, …).
2. Write plain SQL. It runs inside the application's own connection.
3. Never edit a migration that has shipped — the runner will refuse to start
   against a database that applied the earlier bytes. Add a new file instead.

Filenames must match `NNNN_slug.sql`; a duplicate version number is an error,
because two files claiming `0003` would apply in filesystem order.

## Checksums

Each applied migration is recorded in `schema_migrations` with the SHA-256 of
its **newline-normalised** bytes. Normalisation is load-bearing, not cosmetic:
this repo is authored on Windows and cloned on Linux CI, so a CRLF checkout
would otherwise change every checksum and refuse every deployment.

Two refusals, both deliberate:

- **Edited applied migration** → `MigrationChecksumError`. The recorded bytes
  and the file on disk disagree, so what the database contains is no longer
  what the repository says it contains.
- **Recorded migration missing from disk** → `MigrationMissingError`. The
  database is ahead of the code — usually a rollback that deployed old code
  onto an already-migrated DB.

## The idempotent-error directive

SQLite has no conditional `ALTER TABLE`, and production `state.db` files
predate this runner, so they already carry columns that `0002` adds. A single
statement may declare the one error it tolerates:

```sql
-- @idempotent-error: duplicate column name
ALTER TABLE users ADD COLUMN telegram_username TEXT;
```

Only that statement, and only an error containing that substring, is swallowed.
This is deliberately per-statement: a file-level `try/except` would hide a
genuine failure in any other statement, which is exactly the silent-divergence
mode the checksums exist to prevent.

## Adopting an existing database

`0001` is the baseline and is written entirely with `IF NOT EXISTS`, so
applying it to a long-lived production `state.db` is a no-op that simply
records the DB as migrated. No dump/restore, no downtime.

## H2354 — one runner, dual-ledger adopt

Until H2354, Lane B applied two canonical-reference migrations under a
separate table `canonical_ref_migrations` (module
`app.canonical_state_migrations`), *after* the D1 runner had written
`schema_migrations`. That left two ledgers and two code paths at startup.

Absorb design (prefer refile + bridge):

| Piece | Where it lives now |
|---|---|
| B migration 1 (`canonical_reference_columns`) | [`state/0004_canonical_reference_columns.sql`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/migrations/state/0004_canonical_reference_columns.sql) |
| B migration 2 (`canonical_reference_indices`) | [`state/0005_canonical_reference_indices.sql`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/migrations/state/0005_canonical_reference_indices.sql) |
| Startup | `init_state_db` → `apply_migrations` once (no second ensure call) |
| Old ledger | If `canonical_ref_migrations` still has rows, the runner **imports** matching names into `schema_migrations` as versions `0004`/`0005` |

Bridge rules:

1. Match by **migration name** (`canonical_reference_columns` → `0004`,
   `canonical_reference_indices` → `0005`), not by B's integer id.
2. Stamp the **current** D1 file checksum (newline-normalised SHA-256), not
   B's old statement-join hash — algorithms differ; carrying the old hash
   would refuse every startup.
3. Do **not** re-execute SQL for bridged versions; the columns/indices are
   already on disk. Pending versions still apply normally.
4. New writes never touch `canonical_ref_migrations`. The table may remain
   as historical residue; it is no longer a second source of truth.
5. Edited-after-apply and missing-file refusals are unchanged for every
   `schema_migrations` row, including adopted ones.

Scripts that only have a filesystem path (e.g. the canonical-ref backfill)
call `apply_migrations_at_path` / the thin wrappers in
`app.canonical_state_migrations` — same ledger, same bridge.

## Reversibility

Forward migrations only, by design — SQLite's `ALTER` support is too narrow for
honest down-migrations, and a generated down-file that has never been executed
is worse than none. The documented rollback is: stop the app, restore the
`state.db` backup taken before deployment, deploy the previous revision. `0001`
and `0002` are both additive, so rolling back application code alone is safe
without touching the database at all.

_Dr. Mārcis Gasūns_
