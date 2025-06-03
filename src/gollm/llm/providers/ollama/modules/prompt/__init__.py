"""
Prompt formatting and processing module for Ollama adapter.

This module handles all prompt-related operations including:
- Formatting prompts for different model types
- Processing and validating prompts
- Handling prompt templates
- Logging prompt details
- Specialized code generation prompts
"""

from .formatter import PromptFormatter
from .logger import PromptLogger
from .code_formatter import CodePromptFormatter

__all__ = ['PromptFormatter', 'PromptLogger', 'CodePromptFormatter']
