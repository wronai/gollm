# src/gollm/__init__.py
"""
goLLM - Smart Python Quality Guardian

Inteligentny system kontroli jakości kodu z integracją LLM,
automatycznym zarządzaniem TODO i CHANGELOG.
"""

__version__ = "0.1.0"
__author__ = "goLLM Team"

from .main import GollmCore
from .config.config import GollmConfig
from .validation.validators import CodeValidator

__all__ = ["GollmCore", "GollmConfig", "CodeValidator"]

