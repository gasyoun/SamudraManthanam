import logging
from fastapi import APIRouter, HTTPException, Query
from app.state_db import get_state_db
from app.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.post("/vacuum")
async def post_vacuum(key: str = Query(...)):
    """
    Manually triggers a SQLite VACUUM to reclaim space and optimize the state database.
    Protected by ADMIN_SECRET_KEY in production, 'dev' key in development.
    """
    if settings.APP_ENV == "production":
        if not settings.ADMIN_SECRET_KEY or key != settings.ADMIN_SECRET_KEY:
            raise HTTPException(status_code=403, detail="Forbidden: Invalid administrative key")
    else:
        if key != "dev":
            raise HTTPException(status_code=403, detail="Forbidden: Use 'dev' key in non-production")

    db = await get_state_db()
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
