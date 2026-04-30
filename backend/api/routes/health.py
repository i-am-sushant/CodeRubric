"""
Health check endpoints.
"""

from datetime import datetime
from fastapi import APIRouter

from backend.config import get_settings
from backend.schemas import HealthCheck

router = APIRouter()
settings = get_settings()


@router.get("/")
async def health_check():
    """Basic health check."""
    return HealthCheck(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow(),
        components={
            "api": "up",
            "database": "up",  # Could add actual DB check
        }
    )


@router.get("/ready")
async def readiness_check():
    """Readiness probe for Kubernetes."""
    return {"status": "ready"}


@router.get("/live")
async def liveness_check():
    """Liveness probe for Kubernetes."""
    return {"status": "alive"}
