"""
Git integration for goLLM

This module provides Git repository integration including:
- Commit analysis and tracking
- Branch information and history
- File change monitoring
- Git hooks management
"""

from .analyzer import CommitInfo, GitAnalyzer
from .hooks import GitHooks

__all__ = ["GitAnalyzer", "CommitInfo", "GitHooks"]
