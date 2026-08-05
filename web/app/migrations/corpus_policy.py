"""corpus.db schema-version policy — rebuild, never migrate (H1927 / Lane D2).

``corpus.db`` is a *generated view* of the canonical JSONL corpus. Every row in
it can be reproduced by re-running ingest, and nothing a user authored lives
there. So a schema change to corpus.db is a **rebuild requirement**, not a
migration: mutating a 500 MB production corpus DB in place trades a cheap,
verifiable regeneration for an irreversible edit whose result no longer matches
any manifest.

That policy is the D2 acceptance criterion. This module supplies the mechanical
half — a declared expected version, and a startup probe that says plainly which
side is stale instead of failing later as mystery query errors.

Grandfathered exception
-----------------------
``app.corpus_compat.ensure_slug_column_and_backfill`` still performs one
in-place ALTER on corpus.db at startup (the slug-routing backfill). It predates
this policy and removing it would 404 the ``/sources/{slug}`` routes of every
deployment that has not re-ingested. It is documented here rather than silently
tolerated, and it is the *only* sanctioned in-place corpus mutation; new schema
work goes through a rebuild.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Bump when the ingest pipeline changes corpus.db's shape in a way the
# application depends on. A bump means "every deployment must re-ingest",
# which is why it is a deliberate, reviewed edit and not a computed value.
CORPUS_SCHEMA_VERSION = 1

CORPUS_SCHEMA_VERSION_KEY = "corpus_schema_version"


@dataclass(frozen=True)
class CorpusSchemaVerdict:
    ok: bool
    found: int | None
    expected: int
    message: str


async def check_corpus_schema_version(db) -> CorpusSchemaVerdict:
    """Compare corpus.db's recorded schema version against the expected one.

    Never raises and never mutates: a corpus mismatch must not take the site
    down, because search over a slightly-old corpus is far better than a 500.
    The verdict is logged and surfaced through ``/api/health``.
    """
    found: int | None = None
    try:
        async with db.execute(
            "SELECT value FROM corpus_meta WHERE key = ?", (CORPUS_SCHEMA_VERSION_KEY,)
        ) as cursor:
            row = await cursor.fetchone()
        if row and row[0] is not None and str(row[0]).strip() != "":
            found = int(str(row[0]).strip())
    except Exception:
        # Missing corpus_meta row or a non-integer value. Both mean "built
        # before versioning"; treat as unknown rather than as a failure.
        found = None

    if found is None:
        message = (
            f"corpus.db carries no {CORPUS_SCHEMA_VERSION_KEY} (built before corpus "
            f"schema versioning). Expected {CORPUS_SCHEMA_VERSION}; re-ingest to "
            f"stamp it. Serving anyway."
        )
        logger.info("corpus policy: %s", message)
        return CorpusSchemaVerdict(True, None, CORPUS_SCHEMA_VERSION, message)

    if found == CORPUS_SCHEMA_VERSION:
        return CorpusSchemaVerdict(
            True, found, CORPUS_SCHEMA_VERSION, f"corpus schema v{found} matches"
        )

    message = (
        f"corpus.db is schema v{found} but this application expects "
        f"v{CORPUS_SCHEMA_VERSION}. corpus.db is generated and is never migrated in "
        f"place — REBUILD it (run ingest against the pinned bundle) rather than "
        f"altering it."
    )
    logger.warning("corpus policy: %s", message)
    return CorpusSchemaVerdict(False, found, CORPUS_SCHEMA_VERSION, message)
