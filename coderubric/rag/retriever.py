"""
Context retriever for RAG-enhanced code review.

Retrieves semantically similar code to provide context for review.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .embedder import CodeEmbedder
from .vector_store import ChromaVectorStore

logger = logging.getLogger(__name__)


@dataclass
class RetrievedContext:
    """Represents a retrieved code snippet with context."""
    content: str
    file_path: str
    start_line: int
    end_line: int
    chunk_type: str
    name: Optional[str]
    language: str
    similarity_score: float
    rank: int
    
    def to_prompt_context(self) -> str:
        """Format for inclusion in LLM prompt."""
        lines = [
            f"### Related Code (from {self.file_path}, lines {self.start_line}-{self.end_line})",
            f"**Type:** {self.chunk_type} | **Name:** {self.name or 'N/A'} | **Relevance:** {self.similarity_score:.2f}",
            "```",
            self.content,
            "```",
            ""
        ]
        return "\n".join(lines)


class ContextRetriever:
    """Retrieves relevant code context for enhanced code review."""
    
    def __init__(
        self,
        embedder: CodeEmbedder,
        vector_store: ChromaVectorStore
    ):
        """
        Initialize the context retriever.
        
        Args:
            embedder: CodeEmbedder instance
            vector_store: ChromaVectorStore instance
        """
        self.embedder = embedder
        self.vector_store = vector_store
    
    async def retrieve_for_diff(
        self,
        diff_content: str,
        repo_id: str,
        n_results: int = 5
    ) -> List[RetrievedContext]:
        """
        Retrieve context for a code diff.
        
        Args:
            diff_content: The diff to find context for
            repo_id: Repository identifier
            n_results: Number of context items to retrieve
            
        Returns:
            List of RetrievedContext objects
        """
        # Embed the diff content
        query_embedding = await self.embedder.embed_text(diff_content)
        
        # Query the vector store
        results = self.vector_store.query(
            query_embedding=query_embedding,
            n_results=n_results,
            repo_id=repo_id
        )
        
        # Convert to RetrievedContext objects
        contexts = []
        for result in results:
            metadata = result['metadata']
            context = RetrievedContext(
                content=result['content'],
                file_path=metadata['file_path'],
                start_line=metadata['start_line'],
                end_line=metadata['end_line'],
                chunk_type=metadata['chunk_type'],
                name=metadata.get('name'),
                language=metadata.get('language', ''),
                similarity_score=result['score'],
                rank=result['rank']
            )
            contexts.append(context)
        
        logger.info(f"Retrieved {len(contexts)} context items for diff")
        return contexts
    
    async def retrieve_for_file(
        self,
        file_content: str,
        file_path: str,
        repo_id: str,
        n_results: int = 5
    ) -> List[RetrievedContext]:
        """
        Retrieve context for a specific file.
        
        Args:
            file_content: Content of the file
            file_path: Path to the file
            repo_id: Repository identifier
            n_results: Number of context items
            
        Returns:
            List of RetrievedContext objects
        """
        # Create a query from file content (first 1000 chars for efficiency)
        query = f"File: {file_path}\n\n{file_content[:1000]}"
        
        query_embedding = await self.embedder.embed_text(query)
        
        # Exclude the file itself from results
        results = self.vector_store.query(
            query_embedding=query_embedding,
            n_results=n_results + 5,  # Request extra to filter out same file
            repo_id=repo_id
        )
        
        # Filter out results from the same file
        filtered_results = [
            r for r in results 
            if r['metadata']['file_path'] != file_path
        ][:n_results]
        
        contexts = []
        for result in filtered_results:
            metadata = result['metadata']
            context = RetrievedContext(
                content=result['content'],
                file_path=metadata['file_path'],
                start_line=metadata['start_line'],
                end_line=metadata['end_line'],
                chunk_type=metadata['chunk_type'],
                name=metadata.get('name'),
                language=metadata.get('language', ''),
                similarity_score=result['score'],
                rank=len(contexts) + 1
            )
            contexts.append(context)
        
        logger.info(f"Retrieved {len(contexts)} context items for file: {file_path}")
        return contexts
    
    async def retrieve_for_issue(
        self,
        issue_description: str,
        affected_code: str,
        repo_id: str,
        n_results: int = 3
    ) -> List[RetrievedContext]:
        """
        Retrieve context to help understand/fix a specific issue.
        
        Args:
            issue_description: Description of the issue
            affected_code: The code affected by the issue
            repo_id: Repository identifier
            n_results: Number of context items
            
        Returns:
            List of RetrievedContext objects
        """
        # Combine issue description with affected code for query
        query = f"Issue: {issue_description}\n\nCode:\n{affected_code[:500]}"
        
        query_embedding = await self.embedder.embed_text(query)
        
        results = self.vector_store.query(
            query_embedding=query_embedding,
            n_results=n_results,
            repo_id=repo_id
        )
        
        contexts = []
        for result in results:
            metadata = result['metadata']
            context = RetrievedContext(
                content=result['content'],
                file_path=metadata['file_path'],
                start_line=metadata['start_line'],
                end_line=metadata['end_line'],
                chunk_type=metadata['chunk_type'],
                name=metadata.get('name'),
                language=metadata.get('language', ''),
                similarity_score=result['score'],
                rank=len(contexts) + 1
            )
            contexts.append(context)
        
        return contexts
    
    def format_context_for_prompt(
        self,
        contexts: List[RetrievedContext],
        max_contexts: int = 3
    ) -> str:
        """
        Format retrieved contexts for inclusion in LLM prompt.
        
        Args:
            contexts: List of RetrievedContext
            max_contexts: Maximum number of contexts to include
            
        Returns:
            Formatted context string
        """
        if not contexts:
            return ""
        
        limited_contexts = contexts[:max_contexts]
        
        sections = [
            "## Additional Context from Repository",
            "The following similar code patterns were found in the repository for reference:",
            ""
        ]
        
        for context in limited_contexts:
            sections.append(context.to_prompt_context())
        
        return "\n".join(sections)
    
    async def index_repository(
        self,
        repo_id: str,
        files: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Index a repository for RAG.
        
        Args:
            repo_id: Repository identifier
            files: Dict mapping file paths to file content
            
        Returns:
            Statistics about the indexing operation
        """
        from .chunker import CodeChunker
        
        chunker = CodeChunker()
        all_chunks = []
        
        logger.info(f"Indexing repository: {repo_id}")
        
        # Chunk all files
        for file_path, content in files.items():
            try:
                chunks = chunker.chunk_file(file_path, content)
                all_chunks.extend(chunks)
                logger.debug(f"Chunked {file_path} into {len(chunks)} chunks")
            except Exception as e:
                logger.warning(f"Error chunking {file_path}: {e}")
        
        logger.info(f"Created {len(all_chunks)} chunks from {len(files)} files")
        
        # Embed chunks
        embeddings_data = await self.embedder.embed_chunks(all_chunks)
        
        # Clear existing repo data and add new
        try:
            self.vector_store.delete_repo(repo_id)
        except Exception:
            pass  # May not exist yet
        
        self.vector_store.add_embeddings(embeddings_data, repo_id)
        
        stats = {
            'repo_id': repo_id,
            'files_indexed': len(files),
            'chunks_created': len(all_chunks),
            'embeddings_stored': len(embeddings_data)
        }
        
        logger.info(f"Indexing complete: {stats}")
        return stats
