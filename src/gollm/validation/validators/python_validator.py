"""Python code validation module.

This module provides functions to validate Python code syntax and structure.
"""

import ast
import tokenize
from io import BytesIO
import logging
from typing import List, Optional

from ..common import CodeValidationResult

logger = logging.getLogger('gollm.validation.code.python')


def is_valid_python(code: str) -> CodeValidationResult:
    """Check if the string is valid Python code.
    
    Args:
        code: The code string to validate
        
    Returns:
        CodeValidationResult with validation status and issues
    """
    from .text_analyzer import looks_like_prompt
    from .code_fixer import attempt_syntax_fix
    from .quality_checker import check_code_quality
    
    issues = []
    
    # Check for empty or whitespace-only content
    if not code or code.isspace():
        issues.append("Empty or whitespace-only content")
        return CodeValidationResult(False, issues)
    
    # Check if it's just a prompt or natural language text
    if looks_like_prompt(code):
        issues.append("Content appears to be a prompt or natural language text, not code")
        return CodeValidationResult(False, issues)
    
    # Try to parse the code with ast
    try:
        ast.parse(code)
    except SyntaxError as e:
        issues.append(f"Syntax error: {str(e)}")
        # Try to fix common syntax issues
        fixed_code = attempt_syntax_fix(code)
        if fixed_code:
            try:
                ast.parse(fixed_code)
                return CodeValidationResult(False, issues, fixed_code)
            except SyntaxError:
                pass
        return CodeValidationResult(False, issues)
    
    # Check for proper tokenization
    try:
        tokens = list(tokenize.tokenize(BytesIO(code.encode('utf-8')).readline))
        # Ensure we have more than just comments, docstrings, or whitespace
        has_code = False
        for token in tokens:
            if token.type in (tokenize.NAME, tokenize.NUMBER, tokenize.OP) and token.string not in ('', '\n'):
                has_code = True
                break
        
        if not has_code:
            issues.append("No actual code found (only comments or docstrings)")
            return CodeValidationResult(False, issues)
    except tokenize.TokenError as e:
        issues.append(f"Tokenization error: {str(e)}")
        return CodeValidationResult(False, issues)
    
    # Check for code quality indicators
    quality_issues = check_code_quality(code)
    if quality_issues:
        issues.extend(quality_issues)
        # Quality issues don't make the code invalid, just problematic
    
    return CodeValidationResult(True, issues)
