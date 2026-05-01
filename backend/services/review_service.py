"""
Code review service.

Orchestrates RAG-enhanced code reviews with progress tracking.
"""

import os
import logging
import uuid
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable, Awaitable, Union
from pathlib import Path

from git import Repo
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.database import Review, Issue, Repository as RepoModel
from backend.schemas import ReviewCreate, ReviewProgress
from coderubric.core.rag_review import RAGCodeReviewer, RAGReviewConfig
from coderubric.core.standard_reviewer import StandardReviewer
from gito.report_struct import ReviewTarget
from gito.constants import REFS_VALUE_ALL

logger = logging.getLogger(__name__)
settings = get_settings()


class ReviewService:
    """Service for managing code reviews."""
    
    def __init__(self, db: Session):
        self.db = db
        self.rag_config = RAGReviewConfig(
            enabled=True,
            embedding_model=settings.embedding_model,
            vector_store_path=settings.vector_store_path,
            n_context_results=settings.n_context_results,
            max_contexts_per_file=settings.max_contexts_per_file
        )
    
    async def run_review_for_id(
        self,
        review_id: str,
        review_data: ReviewCreate,
        progress_callback: Optional[Callable[[ReviewProgress], Union[None, Awaitable[None]]]] = None
    ) -> Review:
        """
        Run a code review for an existing review record.
        
        Args:
            review_id: ID of the pre-created review record
            review_data: Review configuration
            progress_callback: Optional callback for progress updates
            
        Returns:
            Completed review record
        """
        db_review = self.db.query(Review).filter(Review.id == review_id).first()
        if not db_review:
            raise ValueError(f"Review {review_id} not found")
        
        db_review.status = "running"
        self.db.commit()
        
        try:
            # Get repository
            from backend.services.repo_service import RepositoryService
            repo_service = RepositoryService(self.db)
            db_repo = repo_service.get_repository(review_data.repo_id)
            
            if not db_repo:
                raise ValueError(f"Repository {review_data.repo_id} not found")
            
            if not db_repo.local_path or not os.path.exists(db_repo.local_path):
                raise ValueError(f"Repository not cloned or path missing: {db_repo.local_path}")
            
            # Open git repository
            repo = Repo(db_repo.local_path)
            
            # Create review target
            if review_data.review_all:
                what = REFS_VALUE_ALL
                use_merge_base = False
            else:
                what = review_data.source_branch
                use_merge_base = True
            
            target = ReviewTarget(
                git_platform_type=None,
                repo_url=db_repo.url,
                pull_request_id=None,
                what=what,
                against=review_data.target_branch,
                filters=review_data.filters or "",
                use_merge_base=use_merge_base,
                commit_sha=repo.head.commit.hexsha,
                active_branch=review_data.source_branch
            )
            
            # Initialize reviewer — dual-mode selection
            if review_data.use_rag:
                reviewer = RAGCodeReviewer(self.rag_config)
            else:
                reviewer = StandardReviewer()
            
            # Run review
            logger.info(f"Starting review {review_id} for repo {review_data.repo_id}")
            
            # Set up progress tracking
            total_files = 0
            processed = 0
            
            async def custom_progress_callback(current_file: str):
                nonlocal processed
                processed += 1
                if progress_callback:
                    progress = ReviewProgress(
                        processed_files=processed,
                        total_files=total_files,
                        percent_complete=(processed / max(total_files, 1)) * 100,
                        current_file=current_file,
                        status="running"
                    )
                    result = progress_callback(progress)
                    if asyncio.iscoroutine(result):
                        await result
            
            # Estimate total files from diff
            from gito.core import get_target_diff, NoChangesInContextError
            from gito.project_config import ProjectConfig
            
            try:
                cfg = ProjectConfig.load_for_repo(repo)
                diff = get_target_diff(
                    repo=repo,
                    config=cfg,
                    what=target.what,
                    against=target.against,
                    filters=target.filters,
                    use_merge_base=target.use_merge_base,
                    pr=target.pull_request_id
                )
                total_files = len(diff)
                db_review.total_files = total_files
                self.db.commit()
            except NoChangesInContextError:
                # No changes found — complete the review with 0 issues
                db_review.status = "completed"
                db_review.total_files = 0
                db_review.processed_files = 0
                db_review.total_issues = 0
                db_review.completed_at = datetime.utcnow()
                db_review.error_message = "No code changes found between the specified branches."
                self.db.commit()
                logger.info(f"Review {review_id}: no changes to review")
                return db_review
            
            # Perform review
            report = await reviewer.review(
                repo=repo,
                target=target,
                out_folder=Path(settings.vector_store_path).parent / "reports" / review_id,
                use_rag=review_data.use_rag
            )
            
            # Process results
            db_review.processed_files = report.number_of_processed_files
            db_review.total_issues = report.total_issues
            
            # Count issues by severity
            critical = 0
            warning = 0
            info = 0
            
            for issue in report.plain_issues:
                # Determine severity from tags or details
                severity = "warning"  # default
                if issue.tags:
                    tags_lower = [t.lower() for t in issue.tags]
                    if any(t in ['critical', 'error', 'security', 'vulnerability'] for t in tags_lower):
                        severity = "critical"
                    elif any(t in ['info', 'suggestion', 'style'] for t in tags_lower):
                        severity = "info"
                    elif 'warning' in tags_lower:
                        severity = "warning"
                
                # Create issue record
                db_issue = Issue(
                    id=str(uuid.uuid4()),
                    review_id=review_id,
                    file_path=issue.file,
                    title=issue.title,
                    details=issue.details,
                    severity=severity,
                    line_start=issue.affected_lines[0].start_line if issue.affected_lines else None,
                    line_end=issue.affected_lines[0].end_line if issue.affected_lines else None,
                    tags=issue.tags,
                    affected_code=issue.affected_lines[0].affected_code if issue.affected_lines else None,
                    proposal=issue.affected_lines[0].proposal if issue.affected_lines else None
                )
                self.db.add(db_issue)
                
                # Count by severity
                if severity == "critical":
                    critical += 1
                elif severity == "warning":
                    warning += 1
                else:
                    info += 1
            
            db_review.critical_issues = critical
            db_review.warning_issues = warning
            db_review.info_issues = info
            db_review.status = "completed"
            db_review.completed_at = datetime.utcnow()
            
            # Save report path
            report_path = Path(settings.vector_store_path).parent / "reports" / review_id
            db_review.report_path = str(report_path)
            
            self.db.commit()
            
            if progress_callback:
                result = progress_callback(ReviewProgress(
                    processed_files=db_review.processed_files,
                    total_files=db_review.total_files,
                    percent_complete=100,
                    current_file=None,
                    status="completed"
                ))
                if asyncio.iscoroutine(result):
                    await result
            
            logger.info(f"Review {review_id} completed: {db_review.total_issues} issues found")
            return db_review
            
        except Exception as e:
            logger.error(f"Review {review_id} failed: {e}")
            db_review.status = "failed"
            db_review.error_message = str(e)
            db_review.completed_at = datetime.utcnow()
            self.db.commit()
            
            if progress_callback:
                result = progress_callback(ReviewProgress(
                    processed_files=db_review.processed_files or 0,
                    total_files=db_review.total_files or 0,
                    percent_complete=0,
                    current_file=None,
                    status="failed"
                ))
                if asyncio.iscoroutine(result):
                    await result
            
            raise
    
    def get_review(self, review_id: str) -> Optional[Review]:
        """Get review by ID."""
        return self.db.query(Review).filter(Review.id == review_id).first()
    
    def list_reviews(
        self,
        repo_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Review]:
        """List reviews with optional filtering."""
        query = self.db.query(Review)
        if repo_id:
            query = query.filter(Review.repo_id == repo_id)
        return query.order_by(Review.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_review_issues(self, review_id: str) -> List[Issue]:
        """Get all issues for a review."""
        return self.db.query(Issue).filter(Issue.review_id == review_id).all()
    
    def get_report(self, review_id: str) -> Optional[Dict[str, Any]]:
        """Get full report for a review."""
        review = self.get_review(review_id)
        if not review or not review.report_path:
            return None
        
        # Try to load the JSON report
        report_file = Path(review.report_path) / "code-review-report.json"
        if report_file.exists():
            with open(report_file, 'r') as f:
                return json.load(f)
        
        return None
    
    def delete_review(self, review_id: str) -> bool:
        """Delete a review and its issues."""
        review = self.get_review(review_id)
        if not review:
            return False
        
        # Delete issues
        self.db.query(Issue).filter(Issue.review_id == review_id).delete()
        
        # Delete review
        self.db.delete(review)
        self.db.commit()
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall statistics."""
        total_repos = self.db.query(RepoModel).count()
        total_reviews = self.db.query(Review).count()
        total_issues = self.db.query(Issue).count()
        
        avg_issues = 0
        if total_reviews > 0:
            avg_issues = total_issues / total_reviews
        
        # Reviews in last 7 days
        from datetime import timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        reviews_7d = self.db.query(Review).filter(Review.created_at >= seven_days_ago).count()
        reviews_30d = self.db.query(Review).filter(Review.created_at >= thirty_days_ago).count()
        
        return {
            'total_repositories': total_repos,
            'total_reviews': total_reviews,
            'total_issues_found': total_issues,
            'average_issues_per_review': round(avg_issues, 2),
            'reviews_last_7_days': reviews_7d,
            'reviews_last_30_days': reviews_30d
        }
