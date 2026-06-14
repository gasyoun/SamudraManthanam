import logging
import os
from fastapi import APIRouter
from fastapi.responses import FileResponse, StreamingResponse
from app.settings import settings
from app.db import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["offline"])


def _read_sha256(pack_dir: str, pack_type: str) -> str | None:
    """Read the sidecar .sha256 file written by build_offline_pack.py.

    Returns None when the file doesn't exist (pack not yet built).
    """
    sidecar = os.path.join(pack_dir, f"{pack_type}.db.sha256")
    try:
        with open(sidecar, encoding="utf-8") as f:
            return f.read().strip() or None
    except FileNotFoundError:
        return None
    except Exception:
        logger.exception("offline: failed to read %s", sidecar)
        return None


def _db_size(pack_dir: str, pack_type: str) -> int | None:
    """Raw (uncompressed) byte size of a pack's .db, or None when absent.

    This is the size the browser reconstructs after decoding Content-Encoding:
    gzip, so the client uses it as the download-progress denominator (the wire
    Content-Length is the COMPRESSED size and would make a byte-counting bar
    overshoot). None-safe so /api/corpus-version still works before packs build.
    """
    try:
        return os.path.getsize(os.path.join(pack_dir, f"{pack_type}.db"))
    except OSError:
        return None


@router.get("/corpus-version")
async def corpus_version():
    """Return the current corpus version, offline pack SHA-256 hashes, and raw
    pack byte sizes.

    Used by the offline search client to detect stale installed packs, verify
    integrity, and show accurate gzip-on-wire download progress. SHA-256 and
    pack_bytes values are None when the corresponding pack has not been built.
    """
    version = None
    db = None
    try:
        db = await get_db(settings.DB_PATH)
        async with db.execute(
            "SELECT value FROM corpus_meta WHERE key = 'corpus_version'"
        ) as cur:
            row = await cur.fetchone()
            if row:
                version = row[0]
    except Exception:
        logger.exception("offline: failed to read corpus_version from DB")
    finally:
        if db:
            try:
                await db.close()
            except Exception:
                pass

    pack_dir = settings.OFFLINE_PACKS_DIR
    return {
        "corpus_version": version,
        "pack_sha256": {
            "base": _read_sha256(pack_dir, "base"),
            "dict": _read_sha256(pack_dir, "dict"),
        },
        # Raw decoded sizes — the client's gzip-on-wire progress denominator.
        "pack_bytes": {
            "base": _db_size(pack_dir, "base"),
            "dict": _db_size(pack_dir, "dict"),
        },
    }


def _gz_uncompressed_size(gz_path: str) -> int | None:
    """Read the uncompressed size from a gzip file's ISIZE trailer (last 4
    bytes, little-endian, mod 2^32). Exact for files < 4 GiB — all packs are.
    Used only as a fallback for the X-Db-Bytes header when the raw .db is absent
    (an operator may ship just the .gz to save disk)."""
    try:
        with open(gz_path, "rb") as f:
            f.seek(-4, os.SEEK_END)
            return int.from_bytes(f.read(4), "little")
    except Exception:
        return None


def _file_chunks(path: str, chunk_size: int = 1 << 20):
    """Yield a file in chunks. Used as a StreamingResponse body for the gzipped
    pack so the response has NO Range handling (see serve_offline_pack). Starlette
    runs a sync generator in a threadpool, so the blocking reads don't stall the
    event loop."""
    with open(path, "rb") as f:
        while True:
            block = f.read(chunk_size)
            if not block:
                break
            yield block


@router.get("/offline-packs/{pack_type}.db")
async def serve_offline_pack(pack_type: str):
    """Serve an offline search pack as a binary download.

    Packs are large SQLite files built by scripts/build_offline_pack.py. Only
    'base' and 'dict' are valid pack types.

    Serving is gzip-on-wire: when a precompressed {type}.db.gz exists it is sent
    with Content-Encoding: gzip (the browser decodes it transparently, so the
    client's SHA-256 still matches the raw-.db sidecar and importDb receives the
    raw SQLite bytes). The raw .db is the fallback when no .gz is present.

    The X-Db-Bytes header carries the RAW (decoded) size so the client can show
    accurate download progress — Content-Length is the COMPRESSED size under
    Content-Encoding, which would make a byte-counting progress bar overshoot.
    """
    if pack_type not in ("base", "dict"):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Unknown pack type")

    pack_dir = settings.OFFLINE_PACKS_DIR
    raw_path = os.path.join(pack_dir, f"{pack_type}.db")
    gz_path = raw_path + ".gz"

    # Raw (decoded) size for the progress header — prefer the .db, fall back to
    # the gzip ISIZE trailer when only the .gz was shipped.
    raw_size = None
    if os.path.exists(raw_path):
        raw_size = os.path.getsize(raw_path)
    elif os.path.exists(gz_path):
        raw_size = _gz_uncompressed_size(gz_path)

    headers = {}
    if raw_size is not None:
        headers["X-Db-Bytes"] = str(raw_size)

    if os.path.exists(gz_path):
        # StreamingResponse, NOT FileResponse, for the gzipped artifact. A
        # FileResponse advertises Accept-Ranges: bytes and HONOURS an inbound
        # Range header by returning a 206 slice computed over the COMPRESSED .gz
        # offsets while still setting Content-Encoding: gzip — a byte-slice of a
        # gzip stream is not independently decodable. (Setting Accept-Ranges:none
        # does NOT prevent this: Starlette decides 206 from the request's Range
        # header, not the advertised value.) StreamingResponse has no range
        # handling at all, so a Range request just gets the full 200 body.
        # Content-Length is set explicitly to the compressed size (correct for
        # the wire); X-Db-Bytes carries the raw decoded size for progress.
        headers["Content-Encoding"] = "gzip"
        headers["Content-Length"] = str(os.path.getsize(gz_path))
        headers["Content-Disposition"] = f'attachment; filename="samudra-{pack_type}.db"'
        return StreamingResponse(
            _file_chunks(gz_path),
            media_type="application/octet-stream",
            headers=headers,
        )

    if os.path.exists(raw_path):
        # Raw fallback: FileResponse is fine here — no Content-Encoding, so its
        # Range support is correct and even useful for resumable downloads.
        return FileResponse(
            raw_path,
            media_type="application/octet-stream",
            filename=f"samudra-{pack_type}.db",
            headers=headers,
        )

    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail=f"{pack_type} pack not built yet")
