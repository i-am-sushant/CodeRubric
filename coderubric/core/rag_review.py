"""
RAG-enhanced code review implementation.

Integrates the RAG pipeline with the original gito review flow
to provide context-aware code analysis.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any
from pathlib import Path

from git import Repo
from unidiff import PatchedFile

# Import original gito components
from gito.core import (
    get_target_diff,
    is_binary_file,
    read_file,
    file_lines,
    NoChangesInContextError
)
from gito.report_struct import Report, ReviewTarget
from gito.project_config import ProjectConfig

# Import RAG components
from ..rag import CodeEmbedder, ChromaVectorStore, ContextRetriever

logger = logging.getLogger(__name__)


@dataclass
class RAGReviewConfig:
    """Configuration for RAG-enhanced code review."""
    enabled: bool = True
    embedding_model: str = "all-MiniLM-L6-v2"
    vector_store_path: str = field(default_factory=lambda: os.path.join(
        os.path.expanduser("~"), ".coderubric", "chroma_db"
    ))
    n_context_results: int = 5
    max_contexts_per_file: int = 3
    index_repo_before_review: bool = True
    clear_existing_index: bool = False


class RAGCodeReviewer:
    """Code reviewer with RAG context awareness."""
    
    def __init__(self, config: RAGReviewConfig = None):
        """
        Initialize the RAG-enhanced reviewer.
        
        Args:
            config: RAGReviewConfig instance
        """
        self.config = config or RAGReviewConfig()
        
        if self.config.enabled:
            self._init_rag_components()
        else:
            self.embedder = None
            self.vector_store = None
            self.retriever = None
    
    def _init_rag_components(self):
        """Initialize RAG components."""
        self.embedder = CodeEmbedder(
            model=self.config.embedding_model
        )
        
        self.vector_store = ChromaVectorStore(
            collection_name="coderubric",
            persist_directory=self.config.vector_store_path
        )
        
        self.retriever = ContextRetriever(
            embedder=self.embedder,
            vector_store=self.vector_store
        )
        
        logger.info("RAG components initialized")
    
    async def index_repository(
        self,
        repo: Repo,
        repo_id: str = None
    ) -> Dict[str, Any]:
        """
        Index a repository for RAG.
        
        Args:
            repo: Git repository
            repo_id: Repository identifier (defaults to repo name)
            
        Returns:
            Indexing statistics
        """
        if not self.config.enabled:
            logger.warning("RAG is disabled, skipping indexing")
            return {}
        
        repo_id = repo_id or self._get_repo_id(repo)
        
        # Collect all non-binary files
        files = {}
        for root, _, filenames in os.walk(repo.working_tree_dir):
            # Skip common non-code directories
            if any(skip in root for skip in ['.git', 'node_modules', '__pycache__', '.venv', 'venv']):
                continue
            
            for filename in filenames:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, repo.working_tree_dir)
                
                # Skip binary and large files
                try:
                    if is_binary_file(repo, rel_path):
                        continue
                    
                    content = read_file(repo, rel_path, use_local_files=True)
                    if len(content) < 10000:  # Skip very large files
                        files[rel_path] = content
                except Exception as e:
                    logger.debug(f"Skipping {rel_path}: {e}")
        
        logger.info(f"Collected {len(files)} files for indexing")
        
        # Index via retriever
        stats = await self.retriever.index_repository(repo_id, files)
        return stats
    
    async def review(
        self,
        repo: Repo,
        target: ReviewTarget,
        out_folder: str = None,
        use_rag: bool = True
    ) -> Report:
        """
        Perform RAG-enhanced code review.
        
        Args:
            repo: Git repository
            target: ReviewTarget
            out_folder: Output folder for reports
            use_rag: Whether to use RAG context
            
        Returns:
            Report with review results
        """
        repo_id = self._get_repo_id(repo)
        
        # Index repository if needed
        if use_rag and self.config.enabled and self.config.index_repo_before_review:
            logger.info("Indexing repository for RAG...")
            index_stats = await self.index_repository(repo, repo_id)
            logger.info(f"Indexing complete: {index_stats}")
        
        # Get diff
        try:
            diff = get_target_diff(
                repo=repo,
                config=ProjectConfig.load_for_repo(repo),
                what=target.what,
                against=target.against,
                filters=target.filters,
                use_merge_base=target.use_merge_base,
                pr=target.pull_request_id
            )
        except NoChangesInContextError:
            logger.error("No changes to review")
            raise
        
        # Process each file with RAG context
        processing_warnings = []
        issues = {}
        
        for patched_file in diff:
            try:
                file_issues = await self._review_file_with_rag(
                    repo=repo,
                    patched_file=patched_file,
                    repo_id=repo_id if use_rag else None,
                    target=target
                )
                
                if file_issues:
                    issues[patched_file.path] = file_issues
                    
            except Exception as e:
                logger.error(f"Error reviewing {patched_file.path}: {e}")
                processing_warnings.append({
                    'message': f"Failed to review {patched_file.path}: {e}",
                    'file': patched_file.path
                })
        
        # Create report
        report = Report(
            target=target,
            number_of_processed_files=len(diff),
            processing_warnings=processing_warnings
        )
        report.register_issues(issues)
        
        # Save report
        out_folder = Path(out_folder or repo.working_tree_dir)
        out_folder.mkdir(parents=True, exist_ok=True)
        
        from gito.constants import JSON_REPORT_FILE_NAME
        report.save(file_name=out_folder / JSON_REPORT_FILE_NAME)
        
        # Generate markdown report
        report_text = report.render(ProjectConfig.load_for_repo(repo), Report.Format.MARKDOWN)
        text_report_path = out_folder / "code-review-report.md"
        text_report_path.write_text(report_text, encoding="utf-8")
        
        report.to_cli()
        
        return report
    
    async def _review_file_with_rag(
        self,
        repo: Repo,
        patched_file: PatchedFile,
        repo_id: str,
        target: ReviewTarget
    ) -> List[dict]:
        """
        Review a single file with RAG context.
        
        Args:
            repo: Git repository
            patched_file: Patched file from diff
            repo_id: Repository identifier
            target: ReviewTarget
            
        Returns:
            List of issue dicts
        """
        import microcore as mc
        from gito.core import _llm_response_validator
        from gito.project_config import ProjectConfig
        
        config = ProjectConfig.load_for_repo(repo)
        
        # Prepare input
        diff_content = str(patched_file)
        file_lines_content = file_lines(
            repo,
            patched_file.path,
            max_tokens=config.max_code_tokens - mc.tokenizing.num_tokens_from_string(diff_content),
            use_local_files=True
        )
        
        # Retrieve RAG context if enabled
        rag_context = ""
        if repo_id and self.retriever:
            try:
                contexts = await self.retriever.retrieve_for_diff(
                    diff_content=diff_content,
                    repo_id=repo_id,
                    n_results=self.config.n_context_results
                )
                rag_context = self.retriever.format_context_for_prompt(
                    contexts,
                    max_contexts=self.config.max_contexts_per_file
                )
                logger.info(f"Retrieved {len(contexts)} context items for {patched_file.path}")
            except Exception as e:
                logger.warning(f"Failed to retrieve RAG context: {e}")
        
        # Build enhanced prompt
        prompt = mc.prompt(
            config.prompt,
            input=diff_content,
            file_lines=file_lines_content,
            rag_context=rag_context,
            **config.prompt_vars
        )
        
        # Call LLM
        response = await mc.llm(
            prompt,
            parse_json={"validator": _llm_response_validator}
        )
        
        return response if response else []
    
    def _get_repo_id(self, repo: Repo) -> str:
        """Generate a unique ID for a repository."""
        try:
            # Use remote URL or local path
            if repo.remotes:
                remote_url = repo.remotes.origin.url
                # Extract repo name from URL
                if '/' in remote_url:
                    return remote_url.split('/')[-1].replace('.git', '')
            return Path(repo.working_tree_dir).name
        except:
            return Path(repo.working_tree_dir).name


async def review_with_rag(
    repo: Repo,
    target: ReviewTarget,
    out_folder: str = None,
    config: RAGReviewConfig = None
) -> Report:
    """
    Convenience function for RAG-enhanced review.
    
    Args:
        repo: Git repository
        target: ReviewTarget
        out_folder: Output folder
        config: RAGReviewConfig (uses defaults if not provided)
        
    Returns:
            Review report
    """
    reviewer = RAGCodeReviewer(config)
    return await reviewer.review(repo, target, out_folder, use_rag=True)
