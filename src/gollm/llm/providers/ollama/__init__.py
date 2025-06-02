"""
Ollama LLM Provider for goLLM.

This package provides integration with Ollama's local LLM service.
"""

from .config import OllamaConfig
from .adapter import OllamaAdapter
from .provider import OllamaLLMProvider

__all__ = ['OllamaConfig', 'OllamaAdapter', 'OllamaLLMProvider']
