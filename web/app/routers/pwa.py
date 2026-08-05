"""PWA service-worker route (root-scoped).

Extracted from `app.main` by H1927 / Lane D2.
"""

import os

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.static_assets import STATIC_DIR

router = APIRouter(tags=["pwa"])


@router.get("/sw.js")
async def service_worker():
    """Serve the PWA service worker from the root scope.

    The SW file lives in /static/ but must be served from a path whose
    directory is an ancestor of the scope it controls (/).  FastAPI's
    StaticFiles mount at /static/ would restrict the SW scope to /static/*,
    so we expose it here at the root with the Service-Worker-Allowed header
    that explicitly grants the / scope.
    """
    sw_path = os.path.join(STATIC_DIR, "sw.js")
    return FileResponse(
        sw_path,
        media_type="application/javascript",
        # no-cache so an updated SW is picked up promptly (browsers also cap SW
        # script caching at 24h, but this revalidates on every load).
        headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"},
    )
