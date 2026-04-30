"""
RAG (Retrieval-Augmented Generation) Module for CodeRubric.

Provides context-aware code review capabilities by:
1. Embedding code chunks using OpenAI embeddings
2. Storing in ChromaDB vector database
3. Retrieving semantically similar code for context enrichment
"""

from .embedder import CodeEmbedder
from .vector_store import ChromaVectorStore
from .retriever import ContextRetriever
from .chunker import CodeChunker

__all__ = ["CodeEmbedder", "ChromaVectorStore", "ContextRetriever", "CodeChunker"]
