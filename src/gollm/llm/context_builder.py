# src/gollm/llm/context_builder.py
import asyncio
from pathlib import Path
from typing import Any, Dict, List

from ..config.aggregator import ProjectConfigAggregator
from ..logging.log_aggregator import LogAggregator
from ..project_management.changelog_manager import ChangelogManager
from ..project_management.todo_manager import TodoManager


class ContextBuilder:
    """Buduje kompletny kontekst dla LLM"""

    def __init__(self, config):
        self.config = config
        self.log_aggregator = LogAggregator(config)
        self.todo_manager = TodoManager(config)
        self.changelog_manager = ChangelogManager(config)
        self.config_aggregator = ProjectConfigAggregator(config.project_root)

    async def build_context(self, base_context: Dict[str, Any]) -> Dict[str, Any]:
        """Buduje pełny kontekst dla LLM"""

        # Zbierz wszystkie informacje równolegle
        context_tasks = [
            self._get_execution_context(),
            self._get_todo_context(base_context),
            self._get_changelog_context(),
            self._get_project_config_context(),
            self._get_recent_changes_context(),
        ]

        execution_ctx, todo_ctx, changelog_ctx, config_ctx, changes_ctx = (
            await asyncio.gather(*context_tasks)
        )

        return {
            "execution_context": execution_ctx,
            "todo_context": todo_ctx,
            "changelog_context": changelog_ctx,
            "project_config": config_ctx,
            "recent_changes": changes_ctx,
            "base_context": base_context,
            "project_root": self.config.project_root,
            "timestamp": asyncio.get_event_loop().time(),
        }

    async def _get_execution_context(self) -> Dict[str, Any]:
        """Pobiera kontekst wykonania"""
        return await asyncio.to_thread(self.log_aggregator.get_latest_execution_context)

    async def _get_todo_context(self, base_context: Dict[str, Any]) -> Dict[str, Any]:
        """Pobiera kontekst TODO"""
        next_task = self.todo_manager.get_next_task()
        stats = self.todo_manager.get_stats()

        return {
            "next_task": next_task,
            "stats": stats,
            "high_priority_count": stats.get("high_priority", 0),
        }

    async def _get_changelog_context(self) -> Dict[str, Any]:
        """Pobiera kontekst CHANGELOG"""
        recent_changes = self.changelog_manager.get_recent_changes_count()

        return {
            "recent_changes_count": recent_changes,
            "changelog_file": str(self.changelog_manager.changelog_file),
        }

    async def _get_project_config_context(self) -> Dict[str, Any]:
        """Pobiera kontekst konfiguracji projektu"""
        return await asyncio.to_thread(self.config_aggregator.get_aggregated_config)

    async def _get_recent_changes_context(self) -> Dict[str, Any]:
        """Pobiera kontekst ostatnich zmian"""
        # Tutaj można dodać integrację z Git
        return {"git_status": "clean", "uncommitted_changes": 0, "last_commit": "N/A"}
