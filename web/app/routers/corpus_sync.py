from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from app.db import get_db
from app.settings import settings

router = APIRouter(prefix="/api/corpus-sync", tags=["sync"])


@router.get("/manifest")
async def get_manifest():
    db = await get_db(settings.DB_PATH)
    try:
        async with db.execute("SELECT filename, sha256, size FROM sources") as cursor:
            rows = await cursor.fetchall()
        # Derive version from corpus_meta if available, otherwise omit
        version = None
        try:
            async with db.execute("SELECT value FROM corpus_meta WHERE key='corpus_version'") as cur:
                row = await cur.fetchone()
                if row:
                    version = row[0]
        except Exception:
            pass
        result = {"files": [dict(row) for row in rows]}
        if version:
            result["version"] = version
        return result
    finally:
        await db.close()


@router.get("/file/{filename}")
async def get_corpus_file(filename: str):
    # Sanitize before anything else so traversal attempts always get 400
    safe_filename = os.path.basename(filename)
    if safe_filename != filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not settings.CORPUS_PATH:
        raise HTTPException(status_code=503, detail="CORPUS_PATH not configured")

    db = await get_db(settings.DB_PATH)
    try:
        async with db.execute("SELECT 1 FROM sources WHERE filename = ?", (safe_filename,)) as cursor:
            if not await cursor.fetchone():
                raise HTTPException(status_code=404, detail="File not found in manifest")

        file_path = os.path.join(settings.CORPUS_PATH, "Data", safe_filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Physical file not found")

        return FileResponse(file_path)
    finally:
        await db.close()
