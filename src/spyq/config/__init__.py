"""
Configuration management for SPYQ

This module handles all configuration-related functionality including:
- Loading and parsing spyq.json files
- Aggregating configurations from various tools (flake8, black, mypy)
- Managing validation rules and project settings
"""

from .config import SpyqConfig, ValidationRules, ProjectManagement, LLMIntegration
from .aggregator import ProjectConfigAggregator
from .parsers import (
    SpyqConfigParser,
    Flake8Parser,
    PyprojectParser,
    MypyParser
)

__all__ = [
    "SpyqConfig",
    "ValidationRules", 
    "ProjectManagement",
    "LLMIntegration",
    "ProjectConfigAggregator",
    "SpyqConfigParser",
    "Flake8Parser",
    "PyprojectParser",
    "MypyParser"
]



