"""
Code validation module for ensuring generated content is valid code.

This module provides functions to validate that content is actually code
before saving it to a file, preventing issues where prompts or other
non-code text gets saved as code files.
"""

import ast
import re
import tokenize
from io import BytesIO, StringIO
import logging
from typing import Dict, Any, Tuple, List, Optional, Union

logger = logging.getLogger('gollm.validation.code')

class CodeValidationResult:
    """Result of code validation."""
    
    def __init__(self, is_valid: bool, issues: List[str] = None, 
                 fixed_code: Optional[str] = None):
        self.is_valid = is_valid
        self.issues = issues or []
        self.fixed_code = fixed_code
    
    def __bool__(self):
        return self.is_valid

def is_valid_python(code: str) -> CodeValidationResult:
    """Check if the string is valid Python code.
    
    Args:
        code: The code string to validate
        
    Returns:
        CodeValidationResult with validation status and issues
    """
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

def looks_like_prompt(text: str) -> bool:
    """Check if the text looks like a prompt rather than code.
    
    Args:
        text: The text to check
        
    Returns:
        True if the text appears to be a prompt
    """
    # Count lines that look like natural language vs code
    lines = text.strip().split('\n')
    if not lines:
        return True
    
    # Skip potential docstring at the beginning
    start_idx = 0
    if lines[0].startswith('"""') or lines[0].startswith("'''"):
        for i, line in enumerate(lines[1:], 1):
            if '"""' in line or "'''" in line:
                start_idx = i + 1
                break
    
    code_indicators = 0
    text_indicators = 0
    
    for line in lines[start_idx:]:
        line = line.strip()
        if not line:
            continue
            
        # Code indicators
        if (line.startswith(('def ', 'class ', 'import ', 'from ', 'if ', 'for ', 'while ', '@', '#')) or
            re.match(r'^[a-zA-Z0-9_]+\s*[=:]', line) or
            line.endswith((':',)) or
            '->' in line or
            '"""' in line or
            "'''" in line):
            code_indicators += 1
        # Text indicators
        elif (line.endswith(('.', '?', '!')) or
              len(line.split()) > 10 or
              re.search(r'[^\w\s]', line[0]) if line else False):  # Starts with punctuation
            text_indicators += 1
    
    # Check for common prompt phrases
    prompt_phrases = ['create a', 'write a', 'implement', 'design', 'develop', 
                      'please', 'could you', 'I need', 'I want', 'generate']
    
    for phrase in prompt_phrases:
        if phrase in text.lower():
            text_indicators += 1
    
    # If the first line is a question or instruction, it's likely a prompt
    first_line = lines[0].lower().strip()
    if first_line.endswith('?') or first_line.startswith(('write', 'create', 'implement', 'design')):
        text_indicators += 2
    
    # Calculate ratio - if more text indicators than code, it's probably a prompt
    return text_indicators > code_indicators

def attempt_syntax_fix(code: str) -> Optional[str]:
    """Attempt to fix common syntax issues in the code.
    
    Args:
        code: The code with syntax errors
        
    Returns:
        Fixed code if possible, None otherwise
    """
    fixed_code = code
    
    # Fix 1: Try to fix unterminated strings
    string_fixes = [
        (r'("(?:[^"\\]|\\.)*$)', r'\1"'),  # Fix unterminated double quotes
        (r"('(?:[^'\\]|\\.)*$)", r"\1'"),  # Fix unterminated single quotes
        (r'("""(?:[^"\\]|\\.)*$)', r'\1"""'),  # Fix unterminated triple double quotes
        (r"('''(?:[^'\\]|\\.)*$)", r"\1'''"),  # Fix unterminated triple single quotes
    ]
    
    for pattern, replacement in string_fixes:
        fixed_code = re.sub(pattern, replacement, fixed_code, flags=re.MULTILINE)
    
    # Fix 2: Try to fix missing closing parentheses/brackets/braces
    opening_to_closing = {'(': ')', '[': ']', '{': '}'}
    counts = {k: 0 for k in opening_to_closing.keys()}
    
    for char in fixed_code:
        if char in counts:
            counts[char] += 1
        elif char in opening_to_closing.values():
            opening = {v: k for k, v in opening_to_closing.items()}[char]
            counts[opening] -= 1
    
    # Add missing closing characters
    for char, count in counts.items():
        if count > 0:
            fixed_code += opening_to_closing[char] * count
    
    # Fix 3: Try to fix indentation issues
    lines = fixed_code.split('\n')
    if any(line.startswith(' ') for line in lines):
        # There's some indentation, so we assume it's intentional
        pass
    else:
        # Check if there are lines that should be indented
        for i, line in enumerate(lines):
            if i > 0 and lines[i-1].strip().endswith(':'):
                lines[i] = '    ' + line
        fixed_code = '\n'.join(lines)
    
    # Check if our fixes worked
    try:
        ast.parse(fixed_code)
        return fixed_code
    except SyntaxError:
        return None

def check_code_quality(code: str) -> List[str]:
    """Check for code quality issues.
    
    Args:
        code: The code to check
        
    Returns:
        List of quality issues found
    """
    issues = []
    
    # Check for TODO comments
    if re.search(r'#\s*TODO', code):
        issues.append("Contains TODO comments")
    
    # Check for very long lines
    for line in code.split('\n'):
        if len(line) > 100:
            issues.append("Contains very long lines (>100 characters)")
            break
    
    # Check for commented-out code blocks
    commented_lines = 0
    code_lines = 0
    for line in code.split('\n'):
        stripped = line.strip()
        if stripped.startswith('#') and len(stripped) > 2:
            commented_lines += 1
        elif stripped and not stripped.startswith('#'):
            code_lines += 1
    
    if commented_lines > code_lines * 0.3 and commented_lines > 3:
        issues.append("Contains significant commented-out code")
    
    return issues

def extract_code_blocks(text: str) -> List[str]:
    """Extract code blocks from text that might contain markdown or explanations.
    
    Args:
        text: Text that might contain code blocks
        
    Returns:
        List of extracted code blocks
    """
    # Extract markdown code blocks
    markdown_blocks = re.findall(r'```(?:python)?\n(.*?)\n```', text, re.DOTALL)
    
    # If no markdown blocks found, try to extract based on indentation
    if not markdown_blocks:
        lines = text.split('\n')
        current_block = []
        blocks = []
        in_block = False
        
        for line in lines:
            if line.strip().startswith('def ') or line.strip().startswith('class '):
                if current_block:
                    blocks.append('\n'.join(current_block))
                    current_block = []
                in_block = True
            
            if in_block:
                current_block.append(line)
        
        if current_block:
            blocks.append('\n'.join(current_block))
        
        return blocks if blocks else [text]
    
    return markdown_blocks

def validate_and_extract_code(content: str, file_extension: str, options: Dict[str, bool] = None) -> Tuple[bool, str, List[str]]:
    """Validate content as code and extract valid code if possible.
    
    Args:
        content: The content to validate
        file_extension: The file extension (e.g., 'py', 'js')
        options: Dictionary of validation options:
            - strict_validation: If True, don't attempt to fix syntax errors
            - allow_prompt_text: If True, don't reject prompt-like content
            - skip_validation: If True, skip validation entirely
        
    Returns:
        Tuple of (is_valid, best_code, issues)
    """
    # Set default options if none provided
    if options is None:
        options = {
            'strict_validation': False,
            'allow_prompt_text': False,
            'skip_validation': False
        }
    
    # If validation is disabled, return content as-is
    if options.get('skip_validation', False):
        logger.warning("Code validation is disabled - returning content without validation")
        return True, content, []
    if file_extension == 'py':
        # For Python, we have specific validation
        # First try the whole content
        validation = is_valid_python(content)
        
        # If allow_prompt_text is enabled and the only issue is prompt-like content, ignore it
        if options.get('allow_prompt_text', False) and not validation.is_valid:
            if len(validation.issues) == 1 and "prompt" in validation.issues[0].lower():
                logger.info("Allowing prompt-like content as requested by user options")
                return True, content, ["Prompt-like content allowed by user option"]
        
        if validation.is_valid:
            return True, content, validation.issues
        
        # If not valid, try to extract code blocks
        code_blocks = extract_code_blocks(content)
        best_block = None
        best_validation = None
        
        for block in code_blocks:
            block_validation = is_valid_python(block)
            if block_validation.is_valid:
                if best_block is None or len(block) > len(best_block):
                    best_block = block
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
