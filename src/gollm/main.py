
# src/gollm/main.py
import sys
import asyncio
from pathlib import Path
from typing import Optional

from .config.config import GollmConfig
from .validation.validators import CodeValidator
from .project_management.todo_manager import TodoManager
from .project_management.changelog_manager import ChangelogManager
from .llm.orchestrator import LLMOrchestrator
from .logging.log_aggregator import LogAggregator

class GollmCore:
    def __init__(self, config_path: str = "gollm.json"):
        self.config = GollmConfig.load(config_path)
        self.validator = CodeValidator(self.config)
        self.todo_manager = TodoManager(self.config)
        self.changelog_manager = ChangelogManager(self.config)
        self.llm_orchestrator = LLMOrchestrator(self.config)
        self.log_aggregator = LogAggregator(self.config)
    
    def validate_file(self, file_path: str) -> dict:
        """Waliduje pojedynczy plik"""
        return self.validator.validate_file(file_path)
    
    def validate_project(self) -> dict:
        """Waliduje cały projekt"""
        return self.validator.validate_project()
    
    async def handle_code_generation(self, user_request: str, context: dict = None) -> dict:
        """Obsługuje generowanie kodu przez LLM"""
        if context is None:
            context = {}
        
        return await self.llm_orchestrator.handle_code_generation_request(
            user_request, context
        )
    
    def get_next_task(self) -> dict:
        """Pobiera następne zadanie z TODO"""
        return self.todo_manager.get_next_task()
    
    def record_change(self, change_type: str, details: dict):
        """Zapisuje zmianę do CHANGELOG"""
        return self.changelog_manager.record_change(change_type, details)

