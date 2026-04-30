"""
Backend configuration settings.
"""

import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # App
    app_name: str = "CodeRubric API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/coderubric"
    )
    
    # Redis (for background tasks)
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # OpenAI (only needed if using OpenAI for LLM reviews)
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    
    # RAG
    vector_store_path: str = os.getenv(
        "VECTOR_STORE_PATH",
        os.path.join(os.path.expanduser("~"), ".coderubric", "chroma_db")
    )
    n_context_results: int = 5
    max_contexts_per_file: int = 3
    
    # LLM
    llm_api_key: str = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    llm_api_type: str = os.getenv("LLM_API_TYPE", "openai")
    model: str = os.getenv("MODEL", "gpt-4o-mini")
    
    # Frontend URL (for CORS)
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
