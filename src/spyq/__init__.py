# src/spyq/__init__.py
"""
SPYQ - Smart Python Quality Guardian

Inteligentny system kontroli jakości kodu z integracją LLM,
automatycznym zarządzaniem TODO i CHANGELOG.
"""

__version__ = "0.1.0"
__author__ = "SPYQ Team"

from .main import SpyqCore
from .config.config import SpyqConfig
from .validation.validators import CodeValidator

__all__ = ["SpyqCore", "SpyqConfig", "CodeValidator"]

