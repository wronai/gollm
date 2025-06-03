# src/gollm/main.py
import asyncio
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from .config.config import GollmConfig
from .llm.orchestrator import LLMOrchestrator
from .logging.log_aggregator import LogAggregator
from .project_management.changelog_manager import ChangelogManager
from .project_management.metrics_tracker import MetricsTracker
from .project_management.todo_manager import TodoManager
from .validation.validators import CodeValidator
from .core.session_models import GollmSession
from .llm.orchestrator.models import LLMResponse


class GollmCore:
    def __init__(self, config_path: str = "gollm.json"):
        self.config = GollmConfig.load(config_path)

        # Initialize metrics tracker first
        self.metrics_tracker = MetricsTracker(
            Path(self.config.project_root) / ".gollm" / "metrics.json"
        )

        # Initialize validator with metrics tracking
        self.validator = CodeValidator(self.config)
        self.validator.metrics_tracker = self.metrics_tracker

        # Initialize other components
        self.todo_manager = TodoManager(self.config)
        self.changelog_manager = ChangelogManager(self.config)
        self.llm_orchestrator = LLMOrchestrator(
            config=self.config,
            code_validator=self.validator,
            todo_manager=self.todo_manager,
        )
        self.log_aggregator = LogAggregator(self.config)

    def validate_file(self, file_path: str) -> dict:
        """Waliduje pojedynczy plik"""
        return self.validator.validate_file(file_path)

    def validate_project(self, staged_only: bool = False) -> dict:
        """Waliduje cały projekt
        
        Args:
            staged_only: If True, only validate files staged in git
            
        Returns:
            Dictionary with validation results
        """
        return self.validator.validate_project(staged_only=staged_only)

    async def handle_code_generation_request(
        self,
        gollm_session: GollmSession,
        cli_provided_context: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """Obsługuje generowanie kodu przez LLM przy użyciu sesji.

        Args:
            gollm_session: The GoLLM session object containing all context.
            cli_provided_context: Dodatkowe parametry z CLI, które mogą nadpisać te z sesji.

        Returns:
            LLMResponse with generated code and metadata, including the updated session.
        """
        # # Logic for setting adapter_type and use_streaming from context might need to be re-evaluated
        # # if these are now primarily managed via GollmSession.cli_context.
        # # For now, we assume the orchestrator handles merging/prioritizing these from the session.
        # if cli_provided_context:
        #     if "adapter_type" in cli_provided_context:
        #         import os
        #         os.environ["OLLAMA_ADAPTER_TYPE"] = cli_provided_context["adapter_type"]
        #     if "use_streaming" in cli_provided_context:
        #         import os
        #         os.environ["GOLLM_USE_STREAMING"] = str(cli_provided_context["use_streaming"]).lower()

        return await self.llm_orchestrator.handle_code_generation_request(
            gollm_session=gollm_session,
            cli_provided_context=cli_provided_context
        )



    def get_next_task(self) -> dict:
        """Pobiera następne zadanie z TODO"""
        return self.todo_manager.get_next_task()

    def record_change(self, change_type: str, details: dict):
        """Zapisuje zmianę do CHANGELOG"""
        self.changelog_manager.record_change(change_type, details)

    def get_code_metrics(self) -> dict:
        """Retrieve code quality metrics for the project.

        Returns:
            A dictionary containing code quality metrics
        """
        # Get the latest metrics from the metrics tracker
        metrics = self.metrics_tracker.get_metrics(period="week")

        # If we have metrics, return the most recent one
        if metrics and len(metrics) > 0:
            return metrics[-1]

        # If no metrics are available, return a default structure
        return {
            "overall_score": 0,
            "complexity": 0,
            "maintainability": 0,
            "documentation": 0,
            "test_coverage": 0,
            "issues": [],
        }
