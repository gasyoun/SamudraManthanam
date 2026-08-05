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

    The schema itself now lives in ordered, checksum-tracked SQL files under
    `app/migrations/state/` (H1927 / Lane D1) instead of inline CREATE/ALTER
    statements re-executed on every startup. `apply_migrations` is idempotent
    and refuses to run if an already-applied migration file was edited.

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

    # H1925 (Lane B): canonical-reference columns on `corrections` and the
    # `legacy_ref_map` table are applied by their own ordered, checksum-tracked
    # migration set rather than being spelled out here as more ad-hoc ALTERs.
    # Idempotent, so the correction path can also call it defensively.
    if settings.STATE_DB_PATH:
        import logging

        from app.canonical_state_migrations import ensure_canonical_state

        try:
            await ensure_canonical_state(settings.STATE_DB_PATH)
        except Exception:
            logging.getLogger(__name__).exception(
                "canonical reference migrations failed; corrections will fall back "
                "to legacy-only columns"
            )
