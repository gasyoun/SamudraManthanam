from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.routers import sources, search, morph, corpus_sync, health, reader, identity, corrections, ai, admin
from app.settings import settings
from app.state_db import get_state_db, init_state_db
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.STATE_DB_PATH:
        db = await get_state_db()
        await init_state_db(db)
        await db.close()
    yield

app = FastAPI(title="Samudra Manthanam API", lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

# Configure CORS
origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
if not origins or settings.APP_ENV == "development":
    origins = ["*"]

allow_credentials = False
if origins != ["*"]:
    allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sources.router)
app.include_router(search.router)
app.include_router(morph.router)
app.include_router(corpus_sync.router)
app.include_router(health.router)
app.include_router(reader.router)
app.include_router(identity.router)
app.include_router(corrections.router)
app.include_router(ai.router)
app.include_router(admin.router)

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/robots.txt")
async def robots():
    content = "User-agent: *\nDisallow: /api/\nAllow: /\nSitemap: /sitemap.xml"
    from fastapi.responses import Response
    return Response(content=content, media_type="text/plain")

@app.get("/sitemap.xml")
async def sitemap():
    content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>/</loc><priority>1.0</priority></url>
  <url><loc>/api/health</loc><priority>0.1</priority></url>
</urlset>"""
    from fastapi.responses import Response
    return Response(content=content, media_type="application/xml")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
