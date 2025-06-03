"""Code validation module for ensuring generated content is valid code.

This module provides functions to validate that content is actually code
before saving it to a file, preventing issues where prompts or other
non-code text gets saved as code files.

This file is a thin wrapper that imports and re-exports functions from
the modular validator structure in the validators/ package.
"""

import logging

# Import from refactored modules
from .common import CodeValidationResult
from .validators.code_fixer import attempt_syntax_fix
from .validators.escape_handler import (detect_escape_sequences,
                                        format_code_with_escape_sequences)
from .validators.incomplete_function_detector import (contains_incomplete_functions,
                                                  format_for_completion,
                                                  extract_completed_functions)
from .validators.markdown_cleaner import clean_markdown_artifacts
from .validators.python_validator import is_valid_python
from .validators.quality_checker import check_code_quality
from .validators.text_analyzer import extract_code_blocks, looks_like_prompt
from .validators.validation_coordinator import validate_and_extract_code, check_for_incomplete_functions

logger = logging.getLogger("gollm.validation.code")

# Re-export functions to maintain backward compatibility
__all__ = [
    "CodeValidationResult",
    "validate_and_extract_code",
    "format_code_with_escape_sequences",
    "extract_code_blocks",
    "looks_like_prompt",
    "is_valid_python",
    "attempt_syntax_fix",
    "check_code_quality",
    "detect_escape_sequences",
    "clean_markdown_artifacts",
    "check_for_incomplete_functions",
    "format_for_completion",
    "extract_completed_functions",
]
