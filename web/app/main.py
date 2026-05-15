from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.routers import sources, search, morph, corpus_sync
import os

app = FastAPI(title="Samudra Manthanam API")
templates = Jinja2Templates(directory="templates")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # cannot combine wildcard origin with credentials; tighten with ALLOWED_ORIGINS in Phase 1
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sources.router)
app.include_router(search.router)
app.include_router(morph.router)
app.include_router(corpus_sync.router)

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
