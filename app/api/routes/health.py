"""Health check endpoint for Docker."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    """Return a simple status response used by Docker's health check.

    Returns:
        A dict with a "status" key indicating the service is healthy.
    """
    return {"status": "ok"}
