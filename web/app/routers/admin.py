import logging
from fastapi import APIRouter, Depends, HTTPException
from app.security import require_admin
from app.state_db import get_state_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.post("/vacuum", dependencies=[Depends(require_admin)])
async def post_vacuum():
    """
    Manually triggers a SQLite VACUUM to reclaim space and optimize the state database.

    Authenticated by the ADMIN_SECRET_KEY presented in the X-Admin-Key or
    Authorization: Bearer header (H1926 C3). A `?key=` query parameter is
    refused with 400 — see app/security.py for why accepting both is worse
    than refusing one.
    """
    try:
        db = await get_state_db()
    except Exception:
        logger.exception("admin.vacuum: failed to open state DB")
        raise HTTPException(status_code=503, detail="State DB not available")
    if not db:
        raise HTTPException(status_code=503, detail="State DB not available")

    try:
        await db.execute("VACUUM")
        return {"status": "success", "message": "State database vacuumed and optimized"}
    except Exception:
        logger.exception("admin.vacuum failed")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        await db.close()
