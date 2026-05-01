"""
Abstract base class for code reviewers.

Defines the interface that all reviewer implementations must follow,
enabling dual-mode review (RAG-enhanced and standard/lightweight).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pathlib import Path

from git import Repo
from gito.report_struct import Report, ReviewTarget


class BaseReviewer(ABC):
    """
    Abstract base class for all code reviewer implementations.
    
    Subclasses must implement the `review` method.
    """
    
    @abstractmethod
    async def review(
        self,
        repo: Repo,
        target: ReviewTarget,
        out_folder: str = None,
        **kwargs
    ) -> Report:
        """
        Perform a code review on the given repository.
        
        Args:
            repo: Git repository
            target: ReviewTarget with branch/PR info
            out_folder: Output folder for reports
            **kwargs: Additional implementation-specific options
            
        Returns:
            Report with review results
        """
        ...
