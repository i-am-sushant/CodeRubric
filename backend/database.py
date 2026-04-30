"""
Database configuration and models.
"""

from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, JSON, Float
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

from backend.config import get_settings

settings = get_settings()

# Database engine
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Repository(Base):
    """Repository model."""
    __tablename__ = "repositories"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    url = Column(String)
    local_path = Column(String)
    indexed_at = Column(DateTime, default=datetime.utcnow)
    index_status = Column(String, default="pending")  # pending, indexing, completed, failed
    chunks_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Review(Base):
    """Code review model."""
    __tablename__ = "reviews"
    
    id = Column(String, primary_key=True, index=True)
    repo_id = Column(String, index=True)
    status = Column(String, default="pending")  # pending, running, completed, failed
    target_branch = Column(String)
    source_branch = Column(String)
    use_rag = Column(Integer, default=1)
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    total_issues = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)
    warning_issues = Column(Integer, default=0)
    info_issues = Column(Integer, default=0)
    report_path = Column(String)
    error_message = Column(Text)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class Issue(Base):
    """Review issue model."""
    __tablename__ = "issues"
    
    id = Column(String, primary_key=True, index=True)
    review_id = Column(String, index=True)
    file_path = Column(String, index=True)
    title = Column(String)
    details = Column(Text)
    severity = Column(String)  # critical, warning, info
    line_start = Column(Integer)
    line_end = Column(Integer)
    tags = Column(JSON)
    affected_code = Column(Text)
    proposal = Column(Text)
    score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
