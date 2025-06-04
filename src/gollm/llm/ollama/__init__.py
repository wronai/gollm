"""
Ollama integration for GoLLM.

This package provides integration with Ollama's LLM service, including
configuration management, API communication, and model handling.
"""

from .config import OllamaConfig
from .adapter import OllamaAdapter
from .provider import OllamaLLMProvider
from .models.manager import ModelManager

__all__ = [
    'OllamaConfig',
    'OllamaAdapter',
    'OllamaLLMProvider',
    'ModelManager'
]
