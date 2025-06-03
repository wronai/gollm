"""Markdown code block cleaner module.

This module provides functions to clean markdown artifacts from generated code.
"""

import logging
import re
from typing import Tuple

logger = logging.getLogger("gollm.validation.code.markdown")

# Common language identifiers that might appear at the start of files
LANGUAGE_IDENTIFIERS = [
    "python",
    "py",
    "javascript",
    "js",
    "typescript",
    "ts",
    "java",
    "c",
    "cpp",
    "csharp",
    "cs",
    "go",
    "rust",
    "ruby",
    "php",
    "html",
    "css",
    "bash",
    "shell",
    "sql",
    "json",
    "xml",
    "yaml",
    "markdown",
    "md",
]


def clean_markdown_artifacts(code: str) -> Tuple[str, bool]:
    """Clean markdown artifacts from generated code.

    Args:
        code: The code string to clean

    Returns:
        Tuple of (cleaned_code, was_modified)
    """
    was_modified = False
    cleaned_code = code

    # Check for single language identifier at the beginning of the file
    lines = code.split("\n")
    if lines and lines[0].strip().lower() in LANGUAGE_IDENTIFIERS:
        logger.info(
            f"Removing language identifier '{lines[0].strip()}' from the beginning of the file"
        )
        cleaned_code = "\n".join(lines[1:])
        was_modified = True

    # Check for incomplete markdown code block markers
    if cleaned_code.startswith("```"):
        # Find the end of the first line
        first_line_end = cleaned_code.find("\n")
        if first_line_end > 0:
            # Remove the first line if it's just a markdown start marker
            first_line = cleaned_code[:first_line_end].strip()
            if (
                first_line.startswith("```") and len(first_line) <= 20
            ):  # Reasonable length for a language identifier
                logger.info(
                    f"Removing markdown code block start marker '{first_line}' from the beginning of the file"
                )
                cleaned_code = cleaned_code[first_line_end + 1 :]
                was_modified = True

    # Remove trailing markdown code block end marker if present
    if cleaned_code.strip().endswith("```"):
        last_marker_pos = cleaned_code.rstrip().rfind("```")
        if last_marker_pos > 0:
            # Check if there's only whitespace or a newline before the marker on that line
            prev_newline = cleaned_code.rfind("\n", 0, last_marker_pos)
            if (
                prev_newline == -1
                or cleaned_code[prev_newline + 1 : last_marker_pos].isspace()
            ):
                logger.info(
                    "Removing markdown code block end marker from the end of the file"
                )
                cleaned_code = cleaned_code[:last_marker_pos].rstrip()
                was_modified = True

    return cleaned_code, was_modified
