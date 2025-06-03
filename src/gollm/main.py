# src/gollm/main.py
import asyncio
import sys
from pathlib import Path
from typing import Optional

from .config.config import GollmConfig
from .llm.orchestrator import LLMOrchestrator
from .logging.log_aggregator import LogAggregator
from .project_management.changelog_manager import ChangelogManager
from .project_management.metrics_tracker import MetricsTracker
from .project_management.todo_manager import TodoManager
from .validation.validators import CodeValidator


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

    async def handle_code_generation(
        self,
        user_request: str,
        context: dict = None,
        max_iterations: int = 3,
        validation_mode: str = "strict",
        skip_validation: bool = False,
        use_streaming: bool = True,
    ) -> dict:
        """Obsługuje generowanie kodu przez LLM

        Args:
            user_request: The user's code generation request
            context: Additional context for generation
            max_iterations: Maximum number of generation iterations
            validation_mode: Validation mode (strict or standard)
            skip_validation: Whether to skip validation
            use_streaming: Whether to use streaming API when available

        Returns:
            LLMResponse with generated code and metadata
        """
        if context is None:
            context = {}

        # Set adapter type in context if specified
        if "adapter_type" in context:
            # Set environment variable to influence adapter selection
            import os

            os.environ["OLLAMA_ADAPTER_TYPE"] = context["adapter_type"]

        # Set streaming flag in environment if specified
        if "use_streaming" in context:
            import os

            os.environ["GOLLM_USE_STREAMING"] = str(context["use_streaming"]).lower()

        # Create a request context with all parameters
        request_context = context.copy()

        # Add parameters to context to ensure they're passed correctly
        request_context["max_iterations"] = max_iterations
        request_context["validation_mode"] = validation_mode
        request_context["skip_validation"] = skip_validation
        request_context["use_streaming"] = use_streaming

        # Call the orchestrator with the user request and enhanced context
        return await self.llm_orchestrator.handle_code_generation_request(
            user_request=user_request, context=request_context
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
