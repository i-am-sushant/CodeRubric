"""
Code review endpoints.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas import (
    ReviewCreate,
    ReviewResponse,
    ReviewList,
    IssueResponse,
    IssueList,
    ReviewProgress
)
from backend.services.review_service import ReviewService
from backend.api.ws import send_progress_update

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=ReviewList)
async def list_reviews(
    repo_id: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all reviews with optional filtering."""
    service = ReviewService(db)
    reviews = service.list_reviews(repo_id=repo_id, skip=skip, limit=limit)
    return ReviewList(
        reviews=[ReviewResponse.model_validate(r) for r in reviews],
        total=len(reviews)
    )


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(review_id: str, db: Session = Depends(get_db)):
    """Get a specific review."""
    service = ReviewService(db)
    review = service.get_review(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return ReviewResponse.model_validate(review)


@router.post("/", response_model=ReviewResponse)
async def create_review(
    review_data: ReviewCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create and start a new code review.
    
    The review runs in the background. Use the returned review_id
    to check status and get results.
    """
    from backend.database import Review as ReviewModel, SessionLocal
    from datetime import datetime
    import uuid
    
    try:
        # Create the review record upfront so we can return its ID
        review_id = str(uuid.uuid4())
        db_review = ReviewModel(
            id=review_id,
            repo_id=review_data.repo_id,
            status="pending",
            target_branch=review_data.target_branch,
            source_branch=review_data.source_branch,
            use_rag=1 if review_data.use_rag else 0,
            started_at=datetime.utcnow()
        )
        db.add(db_review)
        db.commit()
        db.refresh(db_review)
        
        # Background task uses its own session to avoid lifetime issues
        async def run_review():
            bg_db = SessionLocal()
            try:
                bg_service = ReviewService(bg_db)
                
                async def progress_callback(progress: ReviewProgress):
                    await send_progress_update(review_id, progress.model_dump())
                
                await bg_service.run_review_for_id(
                    review_id=review_id,
                    review_data=review_data,
                    progress_callback=progress_callback
                )
                
                await send_progress_update(review_id, {
                    "status": "completed",
                    "percent_complete": 100
                })
            except Exception as e:
                logger.error(f"Background review {review_id} failed: {e}")
                await send_progress_update(review_id, {
                    "status": "failed",
                    "error": str(e)
                })
            finally:
                bg_db.close()
        
        background_tasks.add_task(run_review)
        
        return ReviewResponse.model_validate(db_review)
        
    except Exception as e:
        logger.error(f"Error creating review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{review_id}/issues", response_model=IssueList)
async def get_review_issues(
    review_id: str,
    severity: str = None,
    db: Session = Depends(get_db)
):
    """Get all issues for a review."""
    service = ReviewService(db)
    review = service.get_review(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    issues = service.get_review_issues(review_id)
    
    # Filter by severity if provided
    if severity:
        issues = [i for i in issues if i.severity == severity]
    
    return IssueList(
        issues=[IssueResponse.model_validate(i) for i in issues],
        total=len(issues)
    )


@router.get("/{review_id}/report")
async def get_review_report(review_id: str, db: Session = Depends(get_db)):
    """Get the full report for a review."""
    service = ReviewService(db)
    report = service.get_report(review_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return report


@router.delete("/{review_id}")
async def delete_review(review_id: str, db: Session = Depends(get_db)):
    """Delete a review and its issues."""
    service = ReviewService(db)
    deleted = service.delete_review(review_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Review not found")
    
    return {"message": "Review deleted successfully"}


@router.post("/{review_id}/rerun", response_model=ReviewResponse)
async def rerun_review(
    review_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Re-run an existing review."""
    from backend.database import Review as ReviewModel, SessionLocal
    from datetime import datetime
    import uuid
    
    service = ReviewService(db)
    old_review = service.get_review(review_id)
    
    if not old_review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Create new review with same settings
    review_data = ReviewCreate(
        repo_id=old_review.repo_id,
        target_branch=old_review.target_branch,
        source_branch=old_review.source_branch,
        use_rag=bool(old_review.use_rag)
    )
    
    # Create new review record upfront
    new_review_id = str(uuid.uuid4())
    db_review = ReviewModel(
        id=new_review_id,
        repo_id=review_data.repo_id,
        status="pending",
        target_branch=review_data.target_branch,
        source_branch=review_data.source_branch,
        use_rag=1 if review_data.use_rag else 0,
        started_at=datetime.utcnow()
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    
    # Start new review in background with its own session
    async def run_review():
        bg_db = SessionLocal()
        try:
            bg_service = ReviewService(bg_db)
            await bg_service.run_review_for_id(
                review_id=new_review_id,
                review_data=review_data
            )
        except Exception as e:
            logger.error(f"Rerun review {new_review_id} failed: {e}")
        finally:
            bg_db.close()
    
    background_tasks.add_task(run_review)
    
    return ReviewResponse.model_validate(db_review)
