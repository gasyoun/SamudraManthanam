"""Static-file location and mounting.

Extracted from `app.main` by H1927 / Lane D2 so that both the `/static` mount
and the root-scoped `/sw.js` route resolve the directory the same way, from one
definition instead of two.
"""

import mimetypes
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Windows registry has no entry for .mjs; without this, Starlette's StaticFiles
# would serve sqlite3.mjs as application/octet-stream, which Chrome rejects for
# ES module imports in a module worker (silent [object Event] onerror).
#
# Registered at import time, and `app.main` imports this module before mounting
# anything, so the mapping is in place before the first response is served.
mimetypes.add_type('text/javascript', '.mjs')

STATIC_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static"
)


def mount_static(app: FastAPI) -> None:
    """Mount `/static` when the directory exists.

    The existence check is deliberate: the corpus-builder and ingest test
    environments import the app without a built static tree, and a missing
    directory raises inside StaticFiles at mount time.
    """
    if os.path.exists(STATIC_DIR):
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
