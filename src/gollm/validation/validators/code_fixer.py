"""Code fixing module for validation.

This module provides functions to attempt to fix common syntax issues in code.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger('gollm.validation.code.fixer')


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
    
    # Fix 4: Try to fix missing colons after control statements
    control_stmt_pattern = r'^(\s*)(if|elif|else|for|while|def|class|with|try|except|finally)\s+([^:]+)\s*$'
    fixed_lines = []
    for line in fixed_code.split('\n'):
        match = re.match(control_stmt_pattern, line)
        if match and not line.strip().endswith(':'):
            fixed_lines.append(f"{line}:")
        else:
            fixed_lines.append(line)
    fixed_code = '\n'.join(fixed_lines)
    
    # Fix 5: Try to fix common typos in keywords
    typo_fixes = [
        (r'\bimpotr\b', 'import'),
        (r'\bfrom\s+([a-zA-Z0-9_.]+)\s+improt\b', r'from \1 import'),
        (r'\bdefine\b', 'def'),
        (r'\bfunction\b', 'def'),
        (r'\breturn\s+([^\n;]+);', r'return \1'),  # Remove semicolons after return
        (r'\bpirnt\b', 'print'),
    ]
    
    for pattern, replacement in typo_fixes:
        fixed_code = re.sub(pattern, replacement, fixed_code)
    
    # Only return the fixed code if it's different from the original
    if fixed_code != code:
        return fixed_code
    
    return None
