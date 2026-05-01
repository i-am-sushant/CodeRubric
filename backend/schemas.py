"""
Pydantic schemas for API request/response models.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


# Repository Schemas
class RepositoryBase(BaseModel):
    name: str
    url: Optional[str] = None
    local_path: Optional[str] = None


class RepositoryCreate(RepositoryBase):
    id: str


class RepositoryResponse(RepositoryBase):
    id: str
    indexed_at: Optional[datetime] = None
    index_status: str = "pending"
    chunks_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class RepositoryList(BaseModel):
    repositories: List[RepositoryResponse]
    total: int


class IndexRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = "main"


class IndexResponse(BaseModel):
    repo_id: str
    status: str
    chunks_created: int
    files_indexed: int
    message: str


# Review Schemas
class ReviewBase(BaseModel):
    repo_id: str
    target_branch: Optional[str] = "main"
    source_branch: Optional[str] = "HEAD"
    use_rag: bool = True
    filters: Optional[str] = ""
    review_all: bool = False


class ReviewCreate(ReviewBase):
    pass


class ReviewProgress(BaseModel):
    processed_files: int
    total_files: int
    percent_complete: float
    current_file: Optional[str] = None
    status: str


class ReviewResponse(ReviewBase):
    id: str
    status: str
    total_files: int = 0
    processed_files: int = 0
    total_issues: int = 0
    critical_issues: int = 0
    warning_issues: int = 0
    info_issues: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    progress: Optional[ReviewProgress] = None
    
    class Config:
        from_attributes = True


class ReviewList(BaseModel):
    reviews: List[ReviewResponse]
    total: int


# Issue Schemas
class IssueBase(BaseModel):
    file_path: str
    title: str
    details: Optional[str] = None
    severity: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    tags: List[str] = []
    affected_code: Optional[str] = None
    proposal: Optional[str] = None


class IssueResponse(IssueBase):
    id: str
    review_id: str
    score: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class IssueList(BaseModel):
    issues: List[IssueResponse]
    total: int


# Report Schemas
class ReportSummary(BaseModel):
    total_issues: int
    critical_count: int
    warning_count: int
    info_count: int
    files_reviewed: int
    summary_text: Optional[str] = None


class ReportDetail(BaseModel):
    review_id: str
    summary: ReportSummary
    issues: List[IssueResponse]
    markdown_content: Optional[str] = None


# Ask about code changes
class AskRequest(BaseModel):
    repo_id: str
    question: str
    source_branch: Optional[str] = "HEAD"
    target_branch: Optional[str] = "main"
    filters: Optional[str] = ""


class AskResponse(BaseModel):
    answer: str
    repo_id: str
    question: str


# Quick Review (clone + review in one step)
class QuickReviewRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = "main"
    source_branch: Optional[str] = "HEAD"
    target_branch: Optional[str] = "main"
    use_rag: bool = False
    filters: Optional[str] = ""
    review_all: bool = False


# Settings
class LLMSettingsResponse(BaseModel):
    llm_api_type: str
    model: str
    has_api_key: bool
    embedding_model: str
    vector_store_path: str

    class Config:
        from_attributes = True


class LLMSettingsUpdate(BaseModel):
    llm_api_key: Optional[str] = None
    llm_api_type: Optional[str] = None
    model: Optional[str] = None


# WebSocket Messages
class WebSocketMessage(BaseModel):
    type: str  # progress, complete, error
    data: Dict[str, Any]


# Health Check
class HealthCheck(BaseModel):
    status: str
    version: str
    timestamp: datetime
    components: Dict[str, str] = {}


# Stats
class StatsResponse(BaseModel):
    total_repositories: int
    total_reviews: int
    total_issues_found: int
    average_issues_per_review: float
    reviews_last_7_days: int
    reviews_last_30_days: int
