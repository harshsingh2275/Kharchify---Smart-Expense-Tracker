"""Health check endpoint."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health check")
def health_check() -> JSONResponse:
    """Return a simple status response to confirm the app is running."""
    return JSONResponse({"status": "ok"})
