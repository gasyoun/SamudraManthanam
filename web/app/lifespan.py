"""Application startup/shutdown — the composition root's lifespan half.

Extracted from `app.main` by H1927 / Lane D2. Behaviour is unchanged: the
corpus probe still runs first, a failed state-DB init still degrades rather
than crashes, and both still log the operator-facing explanation of what will
be broken until it is fixed.

The one addition is the corpus schema-version probe (Lane D2), which reports a
rebuild requirement instead of letting a shape mismatch surface later as
mystery query errors.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import corpus_info
from app.corpus_compat import ensure_slug_column_and_backfill
from app.db import get_db
from app.migrations.corpus_policy import check_corpus_schema_version
from app.services.ai_policy import log_policy_config
from app.settings import settings
from app.state_db import get_state_db, init_state_db

logger = logging.getLogger(__name__)


async def check_corpus_db() -> None:
    """Log a clear warning at startup if corpus.db is missing or has no sources.

    `aiosqlite.connect` will silently CREATE an empty SQLite file at the path
    if it doesn't exist, so missing-corpus shows up downstream as "no results"
    instead of a startup error. This one-shot probe surfaces the misconfig to
    operators via logs without crashing the app.
    """
    if not os.path.exists(settings.DB_PATH):
        logger.warning(
            "lifespan: corpus DB does not exist at DB_PATH=%s — aiosqlite will "
            "create an empty file on first access; the app will serve zero "
            "search results until the corpus is ingested.", settings.DB_PATH
        )
        return
    try:
        db = await get_db(settings.DB_PATH)
        try:
            async with db.execute("SELECT COUNT(*) FROM sources") as cursor:
                row = await cursor.fetchone()
                count = row[0] if row else 0
            if count == 0:
                logger.warning(
                    "lifespan: corpus DB at %s has zero sources — search will "
                    "return no results until an ingest completes.", settings.DB_PATH
                )
            else:
                logger.info("lifespan: corpus DB OK — %d sources loaded.", count)
            # Rebuild-not-migrate policy check (D2). Never raises; a stale
            # corpus is served with a loud log rather than taking search down.
            await check_corpus_schema_version(db)
            # Slug routing migration. Idempotent; runs every startup so a
            # pre-migration corpus.db gains slug URLs without operator action.
            await ensure_slug_column_and_backfill(db)
            # Snapshot corpus version for the page footer / citations.
            await corpus_info.load(db)
        finally:
            await db.close()
    except Exception:
        logger.exception(
            "lifespan: corpus DB probe failed at DB_PATH=%s — search routes will "
            "return 500 until the corpus is fixed.", settings.DB_PATH
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks. A failed state.db init must NOT crash the whole app —
    the corpus search should keep working in degraded mode while the operator
    fixes the state DB. State-dependent routes will surface clean 503s."""
    await check_corpus_db()
    # H2866: state the paid-AI posture once, at startup, so "is the AI on?"
    # is answerable from the log rather than by reading the env by hand.
    log_policy_config()
    if settings.STATE_DB_PATH:
        db = None
        try:
            db = await get_state_db()
            if db is not None:
                await init_state_db(db)
        except Exception:
            logger.exception(
                "lifespan: state DB init failed; identity/corrections/AI cache "
                "endpoints will return 503 until the operator fixes STATE_DB_PATH"
            )
        finally:
            if db is not None:
                try:
                    await db.close()
                except Exception:
                    logger.exception("lifespan: failed to close state DB after init")
    yield
