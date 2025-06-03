# src/gollm/__init__.py
"""
goLLM - Go Learn, Lead, Master!

Intelligent Python code quality guardian with LLM integration,
automated TODO management and CHANGELOG generation.
"""

__version__ = "0.1.0"
__author__ = "goLLM Team"

from .config.config import GollmConfig
from .main import GollmCore
from .validation.validators import CodeValidator

__all__ = ["GollmCore", "GollmConfig", "CodeValidator"]
