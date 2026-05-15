import logging
from fastapi import APIRouter
from app.settings import settings
from app.db import get_db
from app.state_db import get_state_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/health", tags=["health"])


def _public_error(exc: Exception) -> str:
    """Return a stable error label suitable for unauthenticated /api/health callers.

    In development we surface full exception text for fast debugging. In production
    we surface only the exception class name (e.g. "OperationalError") so paths,
    SQL fragments, and stack traces never leak to anonymous monitors.
    """
    if settings.APP_ENV == "development":
        return str(exc)
    return type(exc).__name__


@router.get("")
async def get_health():
    corpus_ok = False
    state_ok = False
    source_count = 0
    corpus_meta = {}
    corpus_error = None
    state_error = None

    # Check corpus.db
    db = None
    try:
        db = await get_db(settings.DB_PATH)
        async with db.execute("SELECT COUNT(*) FROM sources") as cursor:
            row = await cursor.fetchone()
            source_count = row[0]

        corpus_meta = {}
        try:
            async with db.execute("SELECT key, value FROM corpus_meta") as cursor:
                rows = await cursor.fetchall()
                corpus_meta = {r[0]: r[1] for r in rows}
        except Exception:
            pass

        corpus_ok = True
    except Exception as e:
        logger.exception("health: corpus DB probe failed")
        corpus_error = _public_error(e)
    finally:
        if db:
            await db.close()

    # Check state.db
    if not settings.STATE_DB_PATH:
        state_error = "STATE_DB_PATH not configured"
    else:
        sdb = None
        try:
            sdb = await get_state_db()
            if sdb:
                await sdb.execute("SELECT 1")
                state_ok = True
            else:
                state_error = "Could not connect to state database"
        except Exception as e:
            logger.exception("health: state DB probe failed")
            state_error = _public_error(e)
        finally:
            if sdb:
                await sdb.close()

    status = "ok" if (corpus_ok and state_ok) else "degraded"

    return {
        "status": status,
        "corpus_db": {
            "ok": corpus_ok,
            "source_count": source_count,
            "metadata": corpus_meta,
            "error": corpus_error
        },
        "state_db": {
            "ok": state_ok,
            "error": state_error
        }
    }
