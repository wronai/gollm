# src/gollm/__init__.py
"""
goLLM - Go Learn, Lead, Master!

Intelligent Python code quality guardian with LLM integration,
automated TODO management and CHANGELOG generation.
"""

__version__ = "0.1.0"
__author__ = "goLLM Team"

from .main import GollmCore
from .config.config import GollmConfig
from .validation.validators import CodeValidator

__all__ = ["GollmCore", "GollmConfig", "CodeValidator"]

