"""
Repository management service.

Handles repository cloning, indexing, and RAG embedding generation.
"""

import os
import logging
import shutil
import uuid
from typing import Dict, Any, Optional
from pathlib import Path

from git import Repo, GitCommandError
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.database import Repository as RepoModel
from coderubric.rag import CodeEmbedder, ChromaVectorStore, CodeChunker

logger = logging.getLogger(__name__)
settings = get_settings()


class RepositoryService:
    """Service for managing code repositories."""
    
    def __init__(self, db: Session):
        self.db = db
        self.embedder = CodeEmbedder(
            api_key=settings.openai_api_key,
            model=settings.embedding_model
        )
        self.vector_store = ChromaVectorStore(
            collection_name="coderubric",
            persist_directory=settings.vector_store_path
        )
    
    async def clone_and_index(
        self,
        repo_url: str,
        branch: str = "main",
        repo_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Clone a repository and index it for RAG.
        
        Args:
            repo_url: Git repository URL
            branch: Branch to clone
            repo_id: Optional repository ID (generated if not provided)
            
        Returns:
            Indexing statistics
        """
        repo_id = repo_id or str(uuid.uuid4())
        
        # Create or update database record
        db_repo = self.db.query(RepoModel).filter(RepoModel.id == repo_id).first()
        if not db_repo:
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            db_repo = RepoModel(
                id=repo_id,
                name=repo_name,
                url=repo_url,
                index_status="indexing"
            )
            self.db.add(db_repo)
        else:
            db_repo.index_status = "indexing"
        
        self.db.commit()
        
        # Build a persistent clone directory
        clone_dir = os.path.join(
            settings.repo_clone_path, f"{repo_id}_{branch}"
        )
        
        try:
            # Clean up any previous partial clone
            if os.path.exists(clone_dir):
                shutil.rmtree(clone_dir, ignore_errors=True)
            
            os.makedirs(clone_dir, exist_ok=True)
            
            # Clone repository with strict error handling
            logger.info(f"Cloning {repo_url} (branch: {branch}) into {clone_dir}")
            try:
                repo = Repo.clone_from(
                    repo_url, clone_dir, branch=branch
                )
            except GitCommandError as git_err:
                raise RuntimeError(
                    f"Git clone failed for {repo_url}: {git_err}"
                ) from git_err
            
            # Verify the clone succeeded and .git directory exists
            if not os.path.isdir(os.path.join(clone_dir, ".git")):
                raise RuntimeError(
                    f"Clone directory {clone_dir} missing .git — clone did not complete"
                )
            
            # Persist the absolute path immediately — clone succeeded
            clone_abs = os.path.abspath(clone_dir)
            db_repo.local_path = clone_abs
            self.db.commit()
            
            # Index repository (embedding step — optional for non-RAG reviews)
            try:
                stats = await self._index_repository(repo, repo_id)
                
                db_repo.index_status = "completed"
                db_repo.chunks_count = stats['chunks_created']
                self.db.commit()
                
                logger.info(f"Indexing complete: {stats}")
                return stats
            except Exception as idx_err:
                # Clone is fine, only embedding failed — keep clone dir
                logger.error(f"Indexing failed (clone preserved): {idx_err}")
                db_repo.index_status = "failed"
                self.db.commit()
                raise
            
        except (RuntimeError, GitCommandError) as clone_err:
            # Clone itself failed — wipe everything
            logger.error(f"Clone failed for repository: {clone_err}")
            db_repo.index_status = "failed"
            db_repo.local_path = None
            self.db.commit()
            
            if os.path.exists(clone_dir):
                shutil.rmtree(clone_dir, ignore_errors=True)
            
            raise
    
    async def _index_repository(
        self,
        repo: Repo,
        repo_id: str
    ) -> Dict[str, Any]:
        """
        Index a cloned repository.
        
        Args:
            repo: GitPython Repo object
            repo_id: Repository identifier
            
        Returns:
            Indexing statistics
        """
        chunker = CodeChunker()
        
        # Collect all code files
        files = {}
        for root, _, filenames in os.walk(repo.working_tree_dir):
            # Skip non-code directories
            if any(skip in root for skip in [
                '.git', 'node_modules', '__pycache__', '.venv', 'venv',
                'dist', 'build', '.idea', '.vscode', 'coverage'
            ]):
                continue
            
            for filename in filenames:
                # Skip binary and non-code files
                ext = Path(filename).suffix.lower()
                if ext in ['.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', 
                          '.woff', '.woff2', '.ttf', '.eot', '.pdf', '.zip',
                          '.tar', '.gz', '.exe', '.dll', '.so', '.dylib']:
                    continue
                
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, repo.working_tree_dir)
                
                try:
                    # Read file content
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Skip very large files (>100KB)
                    if len(content) > 100000:
                        logger.debug(f"Skipping large file: {rel_path}")
                        continue
                    
                    files[rel_path] = content
                    
                except Exception as e:
                    logger.debug(f"Error reading {rel_path}: {e}")
        
        logger.info(f"Collected {len(files)} files for indexing")
        
        # Chunk all files
        all_chunks = []
        for file_path, content in files.items():
            try:
                chunks = chunker.chunk_file(file_path, content)
                all_chunks.extend(chunks)
            except Exception as e:
                logger.warning(f"Error chunking {file_path}: {e}")
        
        logger.info(f"Created {len(all_chunks)} chunks from {len(files)} files")
        
        # Clear existing embeddings for this repo
        try:
            self.vector_store.delete_repo(repo_id)
            logger.info(f"Cleared existing embeddings for {repo_id}")
        except Exception:
            pass  # May not exist
        
        # Embed chunks in batches
        if all_chunks:
            embeddings_data = await self.embedder.embed_chunks(all_chunks)
            self.vector_store.add_embeddings(embeddings_data, repo_id)
            logger.info(f"Added {len(embeddings_data)} embeddings to vector store")
        
        return {
            'repo_id': repo_id,
            'files_indexed': len(files),
            'chunks_created': len(all_chunks),
            'embeddings_stored': len(all_chunks)
        }
    
    def get_repository(self, repo_id: str) -> Optional[RepoModel]:
        """Get repository by ID."""
        return self.db.query(RepoModel).filter(RepoModel.id == repo_id).first()
    
    def list_repositories(self, skip: int = 0, limit: int = 100) -> list:
        """List all repositories."""
        return self.db.query(RepoModel).offset(skip).limit(limit).all()
    
    def delete_repository(self, repo_id: str) -> bool:
        """Delete a repository and its embeddings."""
        db_repo = self.get_repository(repo_id)
        if not db_repo:
            return False
        
        # Delete embeddings
        try:
            self.vector_store.delete_repo(repo_id)
        except Exception as e:
            logger.warning(f"Error deleting embeddings: {e}")
        
        # Delete local files
        if db_repo.local_path and os.path.exists(db_repo.local_path):
            shutil.rmtree(db_repo.local_path, ignore_errors=True)
        
        # Delete database record
        self.db.delete(db_repo)
        self.db.commit()
        
        return True
    
    def get_index_stats(self, repo_id: str) -> Optional[Dict[str, Any]]:
        """Get indexing statistics for a repository."""
        db_repo = self.get_repository(repo_id)
        if not db_repo:
            return None
        
        return {
            'repo_id': repo_id,
            'status': db_repo.index_status,
            'chunks_count': db_repo.chunks_count,
            'indexed_at': db_repo.indexed_at.isoformat() if db_repo.indexed_at else None
        }
