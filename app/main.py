"""Main FastAPI application entry point."""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.exceptions import register_exception_handlers
from app.logging_config import setup_logging
from app.routers import auth, health, categories, expenses, summary

logger = logging.getLogger(__name__)

STATIC_DIR = settings.base_dir / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks before the app begins serving requests."""
    setup_logging()
    logger.info("Starting Kharchify Expense Tracker API")
    init_db(settings.database_path)
    yield


app = FastAPI(
    title="Expense Tracker API",
    version="1.0.0",
    description="A multi-user expense tracking API built with FastAPI and SQLite.",
    lifespan=lifespan,
)

register_exception_handlers(app)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log each incoming request with method, path, status, and duration."""
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = round((time.monotonic() - start) * 1000)
    logger.info("%s %s -> %s (%d ms)", request.method, request.url.path, response.status_code, duration_ms)
    return response


# API routers
app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(expenses.router, prefix="/api")
app.include_router(summary.router, prefix="/api")

# Serve static assets
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
def index():
    """Serve the login/register page."""
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/dashboard", include_in_schema=False)
def dashboard():
    """Serve the dashboard page."""
    return FileResponse(str(STATIC_DIR / "dashboard.html"))
