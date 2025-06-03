"""Common validation classes and utilities.

This module provides common classes and utilities used across validation modules.
"""

from typing import List, Optional


class CodeValidationResult:
    """Result of code validation."""
    
    def __init__(self, is_valid: bool, issues: List[str] = None, 
                 fixed_code: Optional[str] = None):
        self.is_valid = is_valid
        self.issues = issues or []
        self.fixed_code = fixed_code
    
    def __bool__(self):
        return self.is_valid
