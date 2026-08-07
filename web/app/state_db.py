import aiosqlite
from app.migrations.runner import apply_migrations
from app.settings import settings

async def get_state_db():
    """Returns an async connection to the state database."""
    if not settings.STATE_DB_PATH:
        return None
    db = await aiosqlite.connect(settings.STATE_DB_PATH)
    db.row_factory = aiosqlite.Row
    return db

async def init_state_db(db):
    """Bring the state database up to the latest schema.

    The schema lives in ordered, checksum-tracked SQL files under
    `app/migrations/state/` (H1927 / Lane D1, H2354 absorb of H1925 B).
    One runner applies base schema, marketing columns, trust/session tables,
    and canonical-reference columns/indices. `apply_migrations` is idempotent
    and refuses to run if an already-applied migration file was edited.
    Pre-H2354 DBs that still have a `canonical_ref_migrations` ledger are
    adopted into `schema_migrations` in that same call.

    Raises MigrationError on a tampered or missing migration. The caller
    (lifespan) already treats a state-DB init failure as degraded mode rather
    than fatal, so a refusal surfaces as clean 503s on state-dependent routes
    while corpus search keeps serving.
    """
    await apply_migrations(db)

    # WAL is a per-database persistent setting, not schema — it belongs at
    # connection setup, not in a migration whose checksum would then cover it.
    await db.execute("PRAGMA journal_mode=WAL")
    await db.commit()
