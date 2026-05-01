"""
Standard (non-RAG) code reviewer.

Performs a lightweight LLM-based code review using only the raw diff
and file contents — no ChromaDB or embedding retrieval required.
"""

import logging
from typing import List
from pathlib import Path

from git import Repo

from gito.core import (
    get_target_diff,
    file_lines,
    NoChangesInContextError
)
from gito.report_struct import Report, ReviewTarget
from gito.project_config import ProjectConfig

from .base_reviewer import BaseReviewer

logger = logging.getLogger(__name__)

STANDARD_SYSTEM_CONTEXT = (
    "You are an expert code reviewer. Analyse the diff and full file context "
    "provided below. Report concrete issues — bugs, security flaws, performance "
    "problems, and maintainability concerns. Be concise and actionable."
)


class StandardReviewer(BaseReviewer):
    """Code reviewer that bypasses RAG/ChromaDB entirely."""
    
    async def review(
        self,
        repo: Repo,
        target: ReviewTarget,
        out_folder: str = None,
        **kwargs
    ) -> Report:
        """
        Perform a standard (non-RAG) code review.
        
        Args:
            repo: Git repository
            target: ReviewTarget
            out_folder: Output folder for reports
            
        Returns:
            Report with review results
        """
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
        
        # Process each file without RAG context
        processing_warnings = []
        issues = {}
        
        for patched_file in diff:
            try:
                file_issues = await self._review_file(repo, patched_file, target)
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
        
        report_text = report.render(
            ProjectConfig.load_for_repo(repo), Report.Format.MARKDOWN
        )
        text_report_path = out_folder / "code-review-report.md"
        text_report_path.write_text(report_text, encoding="utf-8")
        
        report.to_cli()
        return report
    
    async def _review_file(self, repo, patched_file, target) -> List[dict]:
        """Review a single file using LLM without any RAG context."""
        import microcore as mc
        from gito.core import _llm_response_validator
        
        config = ProjectConfig.load_for_repo(repo)
        
        diff_content = str(patched_file)
        file_lines_content = file_lines(
            repo,
            patched_file.path,
            max_tokens=config.max_code_tokens - mc.tokenizing.num_tokens_from_string(diff_content),
            use_local_files=True
        )
        
        # Build prompt WITHOUT rag_context — pass empty string
        prompt = mc.prompt(
            config.prompt,
            input=diff_content,
            file_lines=file_lines_content,
            rag_context="",
            **config.prompt_vars
        )
        
        response = await mc.llm(
            prompt,
            parse_json={"validator": _llm_response_validator}
        )
        
        return response if response else []
