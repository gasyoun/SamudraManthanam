import os
import logging
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["offline-page"])

_templates_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..", "templates",
)
templates = Jinja2Templates(directory=_templates_dir)


def _pack_info(pack_dir: str, pack_type: str) -> dict:
    """Return sizes + sha256 for a built pack, or None values when absent.

    size_mb  = raw .db size = the on-device OPFS footprint after install.
    wire_mb  = gzipped .db.gz size = what the user actually downloads
               (served Content-Encoding: gzip). None when no .gz was built.
    """
    db_path = os.path.join(pack_dir, f"{pack_type}.db")
    gz_path = db_path + ".gz"
    sha_path = db_path + ".sha256"
    if not os.path.exists(db_path):
        return {"built": False, "size_mb": None, "wire_mb": None, "sha256": None}
    size_bytes = os.path.getsize(db_path)
    wire_mb = None
    if os.path.exists(gz_path):
        wire_mb = round(os.path.getsize(gz_path) / 1_048_576, 1)
    sha = None
    try:
        with open(sha_path, encoding="utf-8") as f:
            sha = f.read().strip() or None
    except FileNotFoundError:
        pass
    return {
        "built": True,
        "size_mb": round(size_bytes / 1_048_576, 1),
        "wire_mb": wire_mb,
        "sha256": sha,
    }


@router.get("/offline-settings")
async def offline_settings(request: Request):
    """Offline settings page.

    This is the ONLY page that sets COEP: require-corp.  All resources loaded
    here are self-hosted (no Google Fonts, no CDN scripts), so COEP is safe.

    COEP makes the page cross-origin isolated, which is what lets it spawn the
    search worker (a cross-origin-isolated document requires its dedicated
    worker's script to also carry COEP — see the security_headers middleware in
    main.py).  Note the durable storage VFS (opfs-sahpool) does NOT require
    isolation or SharedArrayBuffer; whether COEP can be dropped entirely is an
    open item in docs/DECISIONS_NEEDED.md.
    """
    pack_dir = settings.OFFLINE_PACKS_DIR
    context = {
        "site_name": "Пахтанье океана",
        "og_title": "Офлайн-настройки",
        "og_description": "Управление офлайн-кешем и поиском без сети.",
        "navbar_light": True,
        "base_pack": _pack_info(pack_dir, "base"),
        "dict_pack": _pack_info(pack_dir, "dict"),
        "ss_link": "",
    }
    response = templates.TemplateResponse(
        request=request, name="offline_settings.html", context=context
    )
    # COEP: require-corp is scoped to this page only.
    # All other pages intentionally omit COEP (see security_headers middleware).
    response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
    return response
