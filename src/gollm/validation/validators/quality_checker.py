"""Code quality checking module.

This module provides functions to check code quality and identify potential issues.
"""

import logging
import re
from typing import List

logger = logging.getLogger("gollm.validation.code.quality")


def check_code_quality(code: str) -> List[str]:
    """Check for code quality issues.

    Args:
        code: The code to check

    Returns:
        List of quality issues found
    """
    issues = []

    # Check for very long lines
    lines = code.split("\n")
    for i, line in enumerate(lines, 1):
        if len(line) > 100:
            issues.append(f"Line {i} is too long ({len(line)} characters)")

    # Check for very long functions (more than 50 lines)
    function_pattern = r"def\s+\w+\s*\([^)]*\)\s*(?:->\s*[^:]+)?\s*:"
    function_matches = list(re.finditer(function_pattern, code))

    for i, match in enumerate(function_matches):
        start_idx = match.start()
        end_idx = len(code)

        # Find the end of this function (start of next function or end of file)
        if i < len(function_matches) - 1:
            end_idx = function_matches[i + 1].start()

        function_code = code[start_idx:end_idx]
        function_lines = function_code.split("\n")

        if len(function_lines) > 50:
            function_name = re.search(r"def\s+(\w+)", function_code)
            name = function_name.group(1) if function_name else "unknown"
            issues.append(
                f"Function '{name}' is too long ({len(function_lines)} lines)"
            )

    # Check for too many nested levels
    indent_levels = []
    max_indent = 0
    for line in lines:
        if line.strip() and not line.strip().startswith("#"):
            indent = len(line) - len(line.lstrip())
            indent_level = indent // 4  # Assuming 4 spaces per indent level
            indent_levels.append(indent_level)
            max_indent = max(max_indent, indent_level)

    if max_indent > 4:
        issues.append(f"Code has too many nested levels (max indent: {max_indent})")

    # Check for potential bugs
    if re.search(r"except\s*:", code):
        issues.append("Bare 'except:' clause found (should catch specific exceptions)")

    if re.search(r"\bprint\b", code):
        issues.append("Print statements found (consider using logging instead)")

    return issues
