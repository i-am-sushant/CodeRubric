"""
Ask questions about code changes endpoint.
Uses gito's answer() function to answer questions about diffs.
"""

import os
import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from git import Repo

from backend.database import get_db, Repository as RepoModel
from backend.schemas import AskRequest, AskResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=AskResponse)
async def ask_question(
    req: AskRequest,
    db: Session = Depends(get_db)
):
    """
    Ask a question about the code changes in a repository.
    Uses gito's core answer() function.
    """
    # Look up repo
    db_repo = db.query(RepoModel).filter(RepoModel.id == req.repo_id).first()
    if not db_repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    if not db_repo.local_path or not os.path.exists(db_repo.local_path):
        raise HTTPException(
            status_code=400,
            detail="Repository not cloned. Add and clone it first."
        )

    try:
        repo = Repo(db_repo.local_path)

        from gito.core import answer as gito_answer

        result = await asyncio.to_thread(
            gito_answer,
            question=req.question,
            repo=repo,
            what=req.source_branch,
            against=req.target_branch,
            filters=req.filters or "",
            use_merge_base=True,
        )

        return AskResponse(
            answer=result or "No answer could be generated for this question.",
            repo_id=req.repo_id,
            question=req.question
        )

    except Exception as e:
        logger.error(f"Ask failed for repo {req.repo_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
