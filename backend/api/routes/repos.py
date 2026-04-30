"""
Repository management endpoints.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas import (
    RepositoryResponse,
    RepositoryList,
    IndexRequest,
    IndexResponse
)
from backend.services.repo_service import RepositoryService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=RepositoryList)
async def list_repositories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all repositories."""
    service = RepositoryService(db)
    repos = service.list_repositories(skip=skip, limit=limit)
    return RepositoryList(
        repositories=[RepositoryResponse.model_validate(r) for r in repos],
        total=len(repos)
    )


@router.get("/{repo_id}", response_model=RepositoryResponse)
async def get_repository(repo_id: str, db: Session = Depends(get_db)):
    """Get a specific repository."""
    service = RepositoryService(db)
    repo = service.get_repository(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return RepositoryResponse.model_validate(repo)


@router.post("/", response_model=IndexResponse)
async def create_repository(
    index_req: IndexRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Clone and index a new repository.
    
    This operation runs in the background. Use the returned repo_id
    to check indexing status.
    """
    from backend.database import SessionLocal, Repository as RepoModel
    
    try:
        # Generate repo ID from URL
        repo_id = index_req.repo_url.split('/')[-1].replace('.git', '')
        repo_name = repo_id  # use repo name from URL
        
        # Create repo record upfront so status polling works immediately
        existing = db.query(RepoModel).filter(RepoModel.id == repo_id).first()
        if not existing:
            db_repo = RepoModel(
                id=repo_id,
                name=repo_name,
                url=index_req.repo_url,
                index_status="indexing"
            )
            db.add(db_repo)
            db.commit()
        else:
            existing.index_status = "indexing"
            db.commit()
        
        # Start background indexing with its own session
        async def bg_clone_and_index():
            bg_db = SessionLocal()
            try:
                bg_service = RepositoryService(bg_db)
                await bg_service.clone_and_index(
                    repo_url=index_req.repo_url,
                    branch=index_req.branch,
                    repo_id=repo_id
                )
            except Exception as e:
                logger.error(f"Background indexing failed for {repo_id}: {e}")
            finally:
                bg_db.close()
        
        background_tasks.add_task(bg_clone_and_index)
        
        return IndexResponse(
            repo_id=repo_id,
            status="indexing",
            chunks_created=0,
            files_indexed=0,
            message="Indexing started in background"
        )
        
    except Exception as e:
        logger.error(f"Error starting index: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{repo_id}/index", response_model=IndexResponse)
async def index_repository(
    repo_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Re-index an existing repository."""
    from backend.database import SessionLocal
    
    service = RepositoryService(db)
    repo = service.get_repository(repo_id)
    
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    repo_url = repo.url  # capture before session closes
    
    try:
        # Start background indexing with its own session
        async def bg_reindex():
            bg_db = SessionLocal()
            try:
                bg_service = RepositoryService(bg_db)
                await bg_service.clone_and_index(
                    repo_url=repo_url,
                    branch="main",
                    repo_id=repo_id
                )
            except Exception as e:
                logger.error(f"Background re-indexing failed for {repo_id}: {e}")
            finally:
                bg_db.close()
        
        background_tasks.add_task(bg_reindex)
        
        return IndexResponse(
            repo_id=repo_id,
            status="indexing",
            chunks_created=0,
            files_indexed=0,
            message="Re-indexing started in background"
        )
        
    except Exception as e:
        logger.error(f"Error starting re-index: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{repo_id}/status")
async def get_index_status(repo_id: str, db: Session = Depends(get_db)):
    """Get indexing status for a repository."""
    service = RepositoryService(db)
    status = service.get_index_stats(repo_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    return status


@router.delete("/{repo_id}")
async def delete_repository(repo_id: str, db: Session = Depends(get_db)):
    """Delete a repository and its index."""
    service = RepositoryService(db)
    deleted = service.delete_repository(repo_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    return {"message": "Repository deleted successfully"}
