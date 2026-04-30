"""
Enhanced core module for CodeRubric with RAG integration.

Extends the original gito core with context-aware capabilities.
"""

from .rag_review import review_with_rag, RAGReviewConfig

__all__ = ["review_with_rag", "RAGReviewConfig"]
