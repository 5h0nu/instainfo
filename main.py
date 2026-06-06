import os
import json
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Local imports
from scraper import get_instagram_profile
from ping_service import start_ping_loop

# Define base directory for locating HTML templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    Launches the keep-alive auto-ping thread.
    """
    # Start the background auto-ping thread
    start_ping_loop()
    yield

# Initialize FastAPI
app = FastAPI(
    title="InstaScope API",
    description="API to scrape public Instagram profile details.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def render_playground():
    """
    Serves the beautiful glassmorphism frontend dashboard playground.
    """
    template_path = os.path.join(BASE_DIR, "templates", "index.html")
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Frontend Template Not Found</h1><p>Ensure templates/index.html exists.</p>", 
            status_code=404
        )

@app.get("/api/health")
async def health_check():
    """
    Simple health check endpoint.
    """
    return {
        "status": "healthy",
        "message": "InstaScope API is running successfully.",
        "uptime_keeper": "active"
    }

@app.get("/api/instagram/profile")
async def get_profile(
    username: str = Query(..., description="The Instagram username to fetch profile details for")
):
    """
    API endpoint to fetch Instagram profile details.
    Uses custom json.dumps with ensure_ascii=True and returns a raw Response.
    This guarantees 100% compatibility with all FastAPI/Starlette versions and prevents
    decoding corruption in older client platforms (like bot.business).
    """
    proxy = os.environ.get("PROXY_URL")
    result = get_instagram_profile(username, proxy=proxy)
    
    # Manually serialize JSON with ASCII escaping enabled
    json_content = json.dumps(result, ensure_ascii=True)
    
    if result.get("success"):
        return Response(
            content=json_content,
            status_code=200,
            media_type="application/json"
        )
    else:
        status_code = result.get("status_code", 400)
        return Response(
            content=json_content,
            status_code=status_code,
            media_type="application/json"
        )
