"""Process-wide corpus metadata cache.

Loaded once at lifespan startup from `corpus_meta` so templates can show
the corpus version in the footer without a per-request DB query. A corpus
re-ingest is followed by a service restart (see `reindex.sh` /
`DEPLOYMENT.md`), so a startup-time snapshot cannot go stale in practice.

Both attributes stay None when corpus.db is missing or pre-dates the
`corpus_meta` table — consumers must degrade (hide the version) rather
than fail.
"""
import logging

logger = logging.getLogger(__name__)

corpus_version: str | None = None
generated_at: str | None = None


async def load(db) -> None:
    """Populate the module cache from an open corpus.db connection."""
    global corpus_version, generated_at
    try:
        async with db.execute(
            "SELECT key, value FROM corpus_meta "
            "WHERE key IN ('corpus_version', 'generated_at')"
        ) as cursor:
            rows = await cursor.fetchall()
        kv = {row[0]: row[1] for row in rows}
        corpus_version = kv.get("corpus_version") or None
        generated_at = kv.get("generated_at") or None
        logger.info(
            "corpus_info: version=%s generated_at=%s",
            corpus_version, generated_at,
        )
    except Exception:
        corpus_version = None
        generated_at = None
        logger.exception("corpus_info: failed to read corpus_meta")
