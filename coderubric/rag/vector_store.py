"""
Vector store implementation using ChromaDB.

Stores and retrieves code embeddings for semantic search.
"""

import os
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path

import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class ChromaVectorStore:
    """ChromaDB-based vector store for code embeddings."""
    
    def __init__(
        self,
        collection_name: str = "coderubric",
        persist_directory: str = None,
        host: str = None,
        port: int = 8000,
        use_local: bool = True
    ):
        """
        Initialize ChromaDB vector store.
        
        Args:
            collection_name: Name of the collection to use
            persist_directory: Directory to persist data (for local mode)
            host: ChromaDB server host (for client-server mode)
            port: ChromaDB server port
            use_local: If True, use embedded ChromaDB; if False, connect to server
        """
        self.collection_name = collection_name
        self.use_local = use_local
        
        if use_local:
            # Use embedded ChromaDB with persistence
            persist_dir = persist_directory or os.path.join(
                os.path.expanduser("~"), ".coderubric", "chroma_db"
            )
            Path(persist_dir).mkdir(parents=True, exist_ok=True)
            
            self.client = chromadb.PersistentClient(
                path=persist_dir,
                settings=Settings(
                    anonymized_telemetry=False
                )
            )
            logger.info(f"Initialized local ChromaDB at {persist_dir}")
        else:
            # Connect to ChromaDB server
            self.client = chromadb.HttpClient(
                host=host or "localhost",
                port=port,
                settings=Settings(
                    anonymized_telemetry=False
                )
            )
            logger.info(f"Connected to ChromaDB server at {host}:{port}")
        
        # Get or create collection
        self.collection = self._get_or_create_collection()
    
    def _get_or_create_collection(self):
        """Get existing collection or create new one."""
        collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={
                "description": "CodeRubric code embeddings for RAG",
                "hnsw:space": "cosine"  # Use cosine similarity for embeddings
            }
        )
        logger.info(f"Using collection: {self.collection_name}")
        return collection
    
    def add_embeddings(
        self,
        embeddings_data: List[Dict[str, Any]],
        repo_id: str = "default"
    ) -> None:
        """
        Add embeddings to the vector store.
        
        Args:
            embeddings_data: List of dicts with 'id', 'embedding', and 'chunk' keys
            repo_id: Repository identifier for namespacing
        """
        if not embeddings_data:
            logger.warning("No embeddings to add")
            return
        
        ids = []
        embeddings = []
        metadatas = []
        documents = []
        
        for item in embeddings_data:
            chunk = item['chunk']
            # Prefix ID with repo_id for namespace isolation
            chunk_id = f"{repo_id}:{item['id']}"
            
            ids.append(chunk_id)
            embeddings.append(item['embedding'])
            documents.append(chunk['content'])
            
            metadata = {
                'repo_id': repo_id,
                'file_path': chunk['file_path'],
                'start_line': chunk['start_line'],
                'end_line': chunk['end_line'],
                'chunk_type': chunk.get('chunk_type') or 'chunk',
                'name': chunk.get('name') or '',
                'language': chunk.get('language') or '',
            }
            metadatas.append(metadata)
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
        
        logger.info(f"Added {len(embeddings_data)} embeddings to collection")
    
    def query(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        repo_id: Optional[str] = None,
        filter_dict: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Query the vector store for similar embeddings.
        
        Args:
            query_embedding: Query vector
            n_results: Number of results to return
            repo_id: Filter by repository ID
            filter_dict: Additional metadata filters
            
        Returns:
            List of result dictionaries with metadata and scores
        """
        where_clause = filter_dict or {}
        if repo_id:
            where_clause['repo_id'] = repo_id
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause if where_clause else None,
            include=["metadatas", "documents", "distances"]
        )
        
        # Format results
        formatted_results = []
        if results['ids'] and results['ids'][0]:
            for i, (doc_id, metadata, document, distance) in enumerate(zip(
                results['ids'][0],
                results['metadatas'][0],
                results['documents'][0],
                results['distances'][0]
            )):
                formatted_results.append({
                    'id': doc_id,
                    'content': document,
                    'metadata': metadata,
                    'score': 1 - distance,  # Convert distance to similarity score
                    'rank': i + 1
                })
        
        return formatted_results
    
    def delete_repo(self, repo_id: str) -> None:
        """
        Delete all embeddings for a specific repository.
        
        Args:
            repo_id: Repository identifier
        """
        try:
            self.collection.delete(where={'repo_id': repo_id})
            logger.info(f"Deleted all embeddings for repo: {repo_id}")
        except Exception as e:
            logger.error(f"Error deleting repo embeddings: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        count = self.collection.count()
        return {
            'collection_name': self.collection_name,
            'total_embeddings': count
        }
    
    def peek(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Peek at some embeddings in the collection."""
        results = self.collection.peek(limit=limit)
        
        formatted = []
        if results['ids']:
            for doc_id, metadata, document in zip(
                results['ids'],
                results['metadatas'],
                results['documents']
            ):
                formatted.append({
                    'id': doc_id,
                    'content': document[:200] + '...' if len(document) > 200 else document,
                    'metadata': metadata
                })
        
        return formatted
    
    def clear(self) -> None:
        """Clear all embeddings from the collection."""
        self.client.delete_collection(name=self.collection_name)
        self.collection = self._get_or_create_collection()
        logger.warning("Cleared all embeddings from collection")
