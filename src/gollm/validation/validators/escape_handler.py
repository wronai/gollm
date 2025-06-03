"""Escape sequence handling module.

This module provides functions to handle escape sequences in code.
"""

import ast
import codecs
import logging
import re
import traceback

logger = logging.getLogger("gollm.validation.code.escape")


def format_code_with_escape_sequences(code: str) -> str:
    """Format code by properly handling escape sequences.

    Args:
        code: The code string that might contain escape sequences

    Returns:
        Formatted code with properly interpreted escape sequences
    """
    # Check if the code contains escape sequences that need handling
    if (
        "\\n" in code
        or "\\t" in code
        or '\\"' in code
        or "\\'" in code
        or "\\u" in code
        or "\\x" in code
    ):
        logger.info(f"Detected escape sequences in code, attempting to format")

        # Strategy 1: Try codecs.decode with unicode_escape
        try:
            formatted_code = codecs.decode(code, "unicode_escape")
            logger.info(f"Successfully formatted code with codecs.decode")
            return formatted_code
        except Exception as e:
            logger.warning(f"Failed to format with codecs.decode: {str(e)}")

        # Strategy 2: Try ast.literal_eval with escaping
        try:
            escaped_code = code.replace('"', '\\"').replace("'", "\\'")
            code_to_eval = f'"{escaped_code}"'
            formatted_code = ast.literal_eval(code_to_eval)
            logger.info(
                f"Successfully formatted code with ast.literal_eval (escaped quotes)"
            )
            return formatted_code
        except (SyntaxError, ValueError) as e:
            logger.warning(
                f"Failed to format with ast.literal_eval (escaped): {str(e)}"
            )

        # Strategy 3: Try ast.literal_eval with triple quotes
        try:
            code_to_eval = f'"""' + code + '"""'
            formatted_code = ast.literal_eval(code_to_eval)
            logger.info(
                f"Successfully formatted code with ast.literal_eval (triple quotes)"
            )
            return formatted_code
        except (SyntaxError, ValueError) as e:
            logger.warning(
                f"Failed to format with ast.literal_eval (triple quotes): {str(e)}"
            )

        # Strategy 4: Manual replacement of common escape sequences
        try:
            formatted_code = code
            replacements = [
                ("\\n", "\n"),
                ("\\t", "\t"),
                ("\\r", "\r"),
                ('\\"', '"'),
                ("\\'", "'"),
                ("\\\\", "\\"),
                ("\\b", "\b"),
                ("\\f", "\f"),
            ]
            for old, new in replacements:
                formatted_code = formatted_code.replace(old, new)

            # Handle Unicode escapes (\uXXXX)
            unicode_pattern = r"\\u([0-9a-fA-F]{4})"
            while re.search(unicode_pattern, formatted_code):
                match = re.search(unicode_pattern, formatted_code)
                if match:
                    hex_val = match.group(1)
                    unicode_char = chr(int(hex_val, 16))
                    formatted_code = formatted_code.replace(
                        f"\\u{hex_val}", unicode_char
                    )

            # Handle hex escapes (\xXX)
            hex_pattern = r"\\x([0-9a-fA-F]{2})"
            while re.search(hex_pattern, formatted_code):
                match = re.search(hex_pattern, formatted_code)
                if match:
                    hex_val = match.group(1)
                    hex_char = chr(int(hex_val, 16))
                    formatted_code = formatted_code.replace(f"\\x{hex_val}", hex_char)

            logger.info(f"Successfully formatted code with manual replacement")
            return formatted_code
        except Exception as e:
            logger.warning(f"Failed to format with manual replacement: {str(e)}")
            logger.warning(traceback.format_exc())

    # If no escape sequences or all formatting attempts failed, return original
    return code


def detect_escape_sequences(text: str) -> tuple:
    """Detect escape sequences in text.

    Args:
        text: The text to check for escape sequences

    Returns:
        Tuple of (has_escapes, escape_counts) where escape_counts is a dict
    """
    escape_sequences = {
        "\\n": "newline",
        "\\t": "tab",
        "\\r": "carriage return",
        "\\\\": "backslash",
        '\\"': "double quote",
        "\\'": "single quote",
        "\\u": "unicode",
        "\\x": "hex",
    }

    escape_counts = {}
    for escape, name in escape_sequences.items():
        count = text.count(escape)
        if count > 0:
            escape_counts[name] = count

    return bool(escape_counts), escape_counts
