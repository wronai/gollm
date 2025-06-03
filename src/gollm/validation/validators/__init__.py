"""Validation submodules package for code validation.

This package provides validators for code quality and correctness.
"""

from ..common import Violation
from .ast_validator import ASTValidator
from .code_fixer import attempt_syntax_fix
from .code_validator import CodeValidator
from .escape_handler import (detect_escape_sequences,
                             format_code_with_escape_sequences)
from .python_validator import is_valid_python
from .quality_checker import check_code_quality
from .text_analyzer import extract_code_blocks, looks_like_prompt
from .validation_coordinator import validate_and_extract_code

__all__ = [
    "CodeValidator",
    "ASTValidator",
    "Violation",
    "is_valid_python",
    "extract_code_blocks",
    "looks_like_prompt",
    "validate_and_extract_code",
    "attempt_syntax_fix",
    "check_code_quality",
    "format_code_with_escape_sequences",
    "detect_escape_sequences",
]
