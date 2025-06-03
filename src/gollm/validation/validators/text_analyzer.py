"""Text analysis module for code validation.

This module provides functions to analyze text and determine if it's code or natural language.
"""

import logging
import re
from typing import List

logger = logging.getLogger("gollm.validation.code.text")


def looks_like_prompt(text: str) -> bool:
    """Check if the text looks like a prompt rather than code.

    Args:
        text: The text to check

    Returns:
        True if the text appears to be a prompt
    """
    # Count lines that look like natural language vs code
    lines = text.strip().split("\n")
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
        if (
            line.startswith(
                (
                    "def ",
                    "class ",
                    "import ",
                    "from ",
                    "if ",
                    "for ",
                    "while ",
                    "@",
                    "#",
                )
            )
            or re.match(r"^[a-zA-Z0-9_]+\s*[=:]", line)
            or line.endswith((":",))
            or "->" in line
            or '"""' in line
            or "'''" in line
        ):
            code_indicators += 1
        # Text indicators
        elif (
            line.endswith((".", "?", "!"))
            or len(line.split()) > 10
            or re.search(r"[^\w\s]", line[0])
            if line
            else False
        ):  # Starts with punctuation
            text_indicators += 1

    # Check for common prompt phrases
    prompt_phrases = [
        "create a",
        "write a",
        "implement",
        "design",
        "develop",
        "please",
        "could you",
        "I need",
        "I want",
        "generate",
    ]

    for phrase in prompt_phrases:
        if phrase in text.lower():
            text_indicators += 1

    # If the first line is a question or instruction, it's likely a prompt
    first_line = lines[0].lower().strip()
    if first_line.endswith("?") or first_line.startswith(
        ("write", "create", "implement", "design")
    ):
        text_indicators += 2

    # Calculate ratio - if more text indicators than code, it's probably a prompt
    return text_indicators > code_indicators


def extract_code_blocks(text: str) -> List[str]:
    """Extract code blocks from text that might contain markdown or explanations.

    Args:
        text: Text that might contain code blocks

    Returns:
        List of extracted code blocks
    """
    # Look for markdown code blocks
    code_blocks = []

    # Pattern for ```language\n...code...\n``` style blocks
    pattern = r"```(?:\w*)?\n(.+?)\n```"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        code_blocks.extend(matches)

    # If no markdown blocks found, check for indented blocks (4+ spaces or tabs)
    if not code_blocks:
        lines = text.split("\n")
        current_block = []
        in_block = False

        for line in lines:
            if line.startswith(("    ", "\t")) and line.strip():
                # This line is indented, consider it part of a code block
                if not in_block:
                    in_block = True
                current_block.append(line)
            elif not line.strip() and in_block:
                # Empty line within a block, keep it
                current_block.append(line)
            elif in_block:
                # End of the current block
                if current_block:
                    code_blocks.append("\n".join(current_block))
                current_block = []
                in_block = False

        # Don't forget the last block if we're still in one
        if current_block and in_block:
            code_blocks.append("\n".join(current_block))

    return code_blocks
