"""
Prompt formatting and processing module for Ollama adapter.

This module handles all prompt-related operations including:
- Formatting prompts for different model types
- Processing and validating prompts
- Handling prompt templates
- Logging prompt details
"""

from .formatter import PromptFormatter
from .logger import PromptLogger

__all__ = ['PromptFormatter', 'PromptLogger']
