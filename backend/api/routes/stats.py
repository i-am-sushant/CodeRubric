"""
Statistics endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas import StatsResponse
from backend.services.review_service import ReviewService

router = APIRouter()


@router.get("/", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    """Get overall statistics."""
    service = ReviewService(db)
    stats = service.get_stats()
    return StatsResponse(**stats)
