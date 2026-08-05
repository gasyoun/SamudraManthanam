"""In-place corpus.db compatibility shims — the grandfathered exception.

`corpus.db` is generated and, per `app.migrations.corpus_policy`, is rebuilt
rather than migrated. This module holds the one startup mutation that predates
that policy: the slug-routing backfill. Removing it would 404 `/sources/{slug}`
for every deployment that has not re-ingested since the slug era began, so it
stays — but it lives here, named for what it is, instead of hiding inside the
application entrypoint.

Nothing new belongs in this module. A new corpus schema requirement is a
rebuild (bump `CORPUS_SCHEMA_VERSION`), not another shim.

Extracted verbatim from `app.main` by H1927 / Lane D2.
"""

import logging

logger = logging.getLogger(__name__)


async def ensure_slug_column_and_backfill(db) -> None:
    """Migrate corpus.db to the slug-routing era.

    Two idempotent steps so an operator can roll back and forward without
    losing data:

    1. Add the `slug` column if missing (ALTER TABLE; no-op when already
       present — PRAGMA table_info gates it).
    2. Backfill `slug` for every row where it's NULL or empty. Slugs are
       derived from filename via `derive_slug` with `make_unique_slug`
       collision resolution against the set of slugs already populated.

    Runs at lifespan startup so any pre-migration corpus.db transparently
    gains slug routing without operator action.
    """
    try:
        async with db.execute("PRAGMA table_info(sources)") as cur:
            columns = {row[1] for row in await cur.fetchall()}
        if "slug" not in columns:
            await db.execute("ALTER TABLE sources ADD COLUMN slug TEXT")
            await db.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_sources_slug "
                "ON sources(slug) WHERE slug IS NOT NULL AND slug != ''"
            )
            await db.commit()
            logger.info("lifespan: added sources.slug column")
    except Exception:
        logger.exception("lifespan: failed to add sources.slug column")
        return

    # Backfill any unset slugs. Idempotent.
    try:
        async with db.execute(
            "SELECT id, filename FROM sources "
            "WHERE slug IS NULL OR slug = '' ORDER BY id"
        ) as cur:
            missing = await cur.fetchall()
        if not missing:
            return

        # Existing slugs (from prior runs or partial migrations).
        async with db.execute(
            "SELECT slug FROM sources WHERE slug IS NOT NULL AND slug != ''"
        ) as cur:
            existing = {row[0] for row in await cur.fetchall()}

        from app.services.slug import make_unique_slug
        for row in missing:
            slug = make_unique_slug(row[1], existing)
            existing.add(slug)
            await db.execute("UPDATE sources SET slug = ? WHERE id = ?", (slug, row[0]))
        await db.commit()
        logger.info("lifespan: backfilled slugs for %d source(s)", len(missing))
    except Exception:
        logger.exception(
            "lifespan: slug backfill failed; /sources/{slug} routes may 404 "
            "for un-migrated rows until next startup or re-ingest"
        )
