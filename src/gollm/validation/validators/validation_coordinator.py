"""Validation coordinator module.

This module coordinates the validation process for different types of code.
"""

import logging
from typing import Dict, Any, Tuple, List, Optional, Union

from ..common import CodeValidationResult
from .text_analyzer import extract_code_blocks, looks_like_prompt
from .escape_handler import format_code_with_escape_sequences
from .python_validator import is_valid_python
from .code_fixer import attempt_syntax_fix
from .markdown_cleaner import clean_markdown_artifacts

logger = logging.getLogger('gollm.validation.coordinator')


def validate_and_extract_code(content: str, file_extension: str, options: Dict[str, bool] = None) -> Tuple[bool, str, List[str]]:
    """Validate and extract code from content.
    
    Args:
        content: Generated code content
        file_extension: File extension to determine language
        options: Validation options
        
    Returns:
        Tuple of (is_valid, validated_content, issues)
    """
    options = options or {}
    
    # Clean markdown artifacts from the content
    content, was_cleaned = clean_markdown_artifacts(content)
    if was_cleaned:
        logger.info("Cleaned markdown artifacts from the generated code")
        
    # Format content to handle escape sequences before validation
    content = format_code_with_escape_sequences(content)
    
    if file_extension == 'py':
        # For Python, we have specific validation
        # First try the whole content
        validation = is_valid_python(content)
        
        if validation.is_valid:
            return True, content, validation.issues
        
        # When extracting code blocks, also format them
        code_blocks = extract_code_blocks(content)
        best_block = None
        best_validation = None
        
        for block in code_blocks:
            # Format the block to handle escape sequences
            formatted_block = format_code_with_escape_sequences(block)
            block_validation = is_valid_python(formatted_block)
            if block_validation.is_valid:
                if best_block is None or len(formatted_block) > len(best_block):
                    best_block = formatted_block
                    best_validation = block_validation
        
        if best_block:
            return True, best_block, best_validation.issues + ["Code extracted from mixed content"]
        
        # If we have a fixed version and strict_validation is not enabled, use that
        if validation.fixed_code and not options.get('strict_validation', False):
            return True, validation.fixed_code, validation.issues + ["Syntax errors automatically fixed"]
        elif validation.fixed_code and options.get('strict_validation', False):
            logger.info("Not applying automatic fixes due to strict validation mode")
            return False, content, validation.issues + ["Syntax errors found but not fixed (strict mode)"] 
        
        return False, content, validation.issues
    else:
        # For other languages, do basic checks
        if not content or content.isspace():
            return False, content, ["Empty or whitespace-only content"]
        
        # Check if content looks like a prompt
        if looks_like_prompt(content):
            # If allow_prompt_text is enabled, accept the content as-is
            if options.get('allow_prompt_text', False):
                logger.info("Allowing prompt-like content as requested by user options")
                return True, content, ["Prompt-like content allowed by user option"]
                
            # Otherwise, try to extract code blocks
            code_blocks = extract_code_blocks(content)
            if code_blocks:
                return True, code_blocks[0], ["Extracted code from prompt-like text"]
            return False, content, ["Content appears to be a prompt, not code"]
        
        return True, content, []
