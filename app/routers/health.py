"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health check")
def health_check() -> dict:
    """Return a simple status response to confirm the app is running."""
    return {"status": "ok"}
