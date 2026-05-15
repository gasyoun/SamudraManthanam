from fastapi import APIRouter
from app.settings import settings
from app.db import get_db
from app.state_db import get_state_db

router = APIRouter(prefix="/api/health", tags=["health"])

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
        corpus_error = str(e)
    finally:
        if db:
            await db.close()

    # Check state.db
    if not settings.STATE_DB_PATH:
        state_error = "STATE_DB_PATH not configured"
    else:
        try:
            sdb = await get_state_db()
            if sdb:
                # Just a simple ping
                await sdb.execute("SELECT 1")
                await sdb.close()
                state_ok = True
            else:
                state_error = "Could not connect to state database"
        except Exception as e:
            state_error = str(e)

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
