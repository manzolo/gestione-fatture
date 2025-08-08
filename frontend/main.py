import os
import requests
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles # Import StaticFiles
from typing import Dict, Any

app = FastAPI()

templates = Jinja2Templates(directory="templates") 

# --- Mount the static files directory ---
# This tells FastAPI to serve files from the "static" directory
# under the URL path "/static".
app.mount("/static", StaticFiles(directory="static"), name="static")

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Retrieve the external port from Docker Compose (or where you define it)
    # Ensure FRONTEND_PORT is set in your docker-compose.yml for this service
    frontend_port = os.getenv("FRONTEND_PORT", str(request.url.port)) # Fallback to request.url.port if not defined
    frontend_host = os.getenv("FRONTEND_HOST", request.url.hostname)

    # Construct the full base URL for the frontend
    base_url_for_frontend = f"http://{frontend_host}:{frontend_port}"

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "error_message": None, "base_url": base_url_for_frontend}
    )