from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from app.db import get_db

from app.settings import settings

router = APIRouter(prefix="/api/corpus-sync", tags=["sync"])

CORPUS_PATH = os.environ.get("CORPUS_PATH", "../Index/lib/x86_64-win64")

@router.get("/manifest")
async def get_manifest():
    db = await get_db(settings.DB_PATH)
    try:
        async with db.execute("SELECT filename, sha256, size FROM sources") as cursor:
            rows = await cursor.fetchall()
            return {
                "version": "2026.05", # Dynamic version could be added
                "files": [dict(row) for row in rows]
            }
    finally:
        await db.close()

@router.get("/file/{filename}")
async def get_corpus_file(filename: str):
    # Sanitize filename to prevent path traversal
    safe_filename = os.path.basename(filename)
    if safe_filename != filename:
         raise HTTPException(status_code=400, detail="Invalid filename")

    db = await get_db(settings.DB_PATH)
    try:
        # Verify file exists in database manifest
        async with db.execute("SELECT 1 FROM sources WHERE filename = ?", (safe_filename,)) as cursor:
            if not await cursor.fetchone():
                raise HTTPException(status_code=404, detail="File not found in manifest")
                
        file_path = os.path.join(CORPUS_PATH, "Data", safe_filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Physical file not found")
        
        return FileResponse(file_path)
    finally:
        await db.close()
