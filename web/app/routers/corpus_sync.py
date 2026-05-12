from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from app.db import get_db

router = APIRouter(prefix="/api/corpus-sync", tags=["sync"])

DB_PATH = os.environ.get("DB_PATH", "corpus.db")
CORPUS_PATH = os.environ.get("CORPUS_PATH", "../Index/lib/x86_64-win64")

@router.get("/manifest")
async def get_manifest():
    db = await get_db(DB_PATH)
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
async def get_file(filename: str):
    file_path = os.path.join(CORPUS_PATH, "Data", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)
