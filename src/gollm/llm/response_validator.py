# src/gollm/llm/response_validator.py
import ast
import re
from typing import Any, Dict, List, Optional


class ResponseValidator:
    """Waliduje odpowiedzi z LLM"""

    def __init__(self, config):
        self.config = config

    async def validate_response(self, llm_output: str) -> Dict[str, Any]:
        """Waliduje odpowiedź z LLM"""

        validation_result = {
            "raw_output": llm_output,
            "code_extracted": False,
            "extracted_code": "",
            "explanation": "",
            "code_blocks_found": 0,
            "syntax_valid": False,
            "error_message": None,
        }

        # Extract code blocks from the LLM output
        code_blocks = self._extract_code_blocks(llm_output)
        validation_result["code_blocks_found"] = len(code_blocks)

        if code_blocks:
            # Use the first code block for now
            # TODO: Consider combining code blocks or selecting the best one
            extracted_code = code_blocks[0]
            validation_result["extracted_code"] = extracted_code
            validation_result["code_extracted"] = True

            # Validate Python syntax if the code looks like Python
            if self._looks_like_python(extracted_code):
                syntax_result = self._validate_syntax(extracted_code)
                validation_result.update(syntax_result)
            else:
                # If it doesn't look like Python, we'll assume it's valid for now
                validation_result["syntax_valid"] = True

        # Extract explanation (text outside of code blocks)
        # TODO: Implement better explanation extraction

        return validation_result

    def _extract_code_blocks(self, text: str) -> List[str]:
        """Wyodrębnia bloki kodu z odpowiedzi LLM"""
        import logging

        logger = logging.getLogger("gollm.validator")
        logger.info(f"===== CODE EXTRACTION STARTED =====")

        # Log the input text for debugging
        logger.info(f"Extracting code blocks from text of length {len(text)}")
        logger.debug(f"Text first 200 chars: {text[:200]}...")
        logger.debug(f"Text last 200 chars: {text[-200:] if len(text) > 200 else text}")

        # First try the step-by-step extraction approach
        logger.info("Trying step-by-step extraction approach")
        step_by_step_blocks = self._extract_code_step_by_step(text)
        if step_by_step_blocks:
            logger.info(
                f"Found {len(step_by_step_blocks)} code blocks using step-by-step approach"
            )
            for i, block in enumerate(step_by_step_blocks):
                logger.info(f"Step-by-step block {i+1} length: {len(block)}")
                logger.debug(
                    f"Step-by-step block {i+1} first 100 chars: {block[:100]}..."
                )
            return step_by_step_blocks

        # If step-by-step failed, try to extract markdown code blocks with various formats
        # This handles both ```python and ``` formats, with optional language specifier
        logger.info("Trying markdown pattern extraction")
        code_blocks = re.findall(r"```(?:\w*)?\n(.+?)(?:\n```|$)", text, re.DOTALL)

        # Log how many blocks were found
        logger.info(f"Found {len(code_blocks)} code blocks using markdown pattern")

        # Log each code block found for debugging
        for i, block in enumerate(code_blocks):
            logger.info(f"Code block {i+1} length: {len(block)}")
            logger.debug(f"Code block {i+1} first 100 chars: {block[:100]}...")
            logger.debug(
                f"Code block {i+1} last 100 chars: {block[-100:] if len(block) > 100 else block}"
            )

        # If we found code blocks, clean them up
        if code_blocks:
            # Clean up each code block
            cleaned_blocks = []
            for block in code_blocks:
                # Remove trailing whitespace and ensure it ends with a newline
                cleaned = block.rstrip() + "\n"
                # Apply escape sequence formatting
                cleaned = self._format_code_with_escape_sequences(cleaned)
                cleaned_blocks.append(cleaned)
            return cleaned_blocks

        # If no code blocks found with markdown, try to extract code directly
        logger.info(
            "No markdown code blocks found, trying to extract Python code directly"
        )

        # Check if the text looks like Python code
        if self._looks_like_python(text):
            logger.info("Text appears to be Python code, using as-is")
            # Clean the text to make it more likely to be valid Python
            cleaned_text = self._clean_text_for_python(text)
            if cleaned_text:
                return [cleaned_text]

        # As a last resort, try to find Python-like patterns in the text
        logger.info("Attempting to find Python-like patterns in text")

        # Look for common Python patterns like class/def declarations
        python_patterns = re.findall(
            r"(?:class|def)\s+\w+\s*\([^)]*\):\s*(?:\n\s+.+)+", text, re.DOTALL
        )
        if python_patterns:
            logger.info(f"Found {len(python_patterns)} Python-like patterns")
            return python_patterns

        # If all else fails, log the issue and return an empty list
        logger.warning(f"Could not extract any code blocks from text: {text[:100]}...")
        return []

    def _extract_code_step_by_step(self, text: str) -> List[str]:
        """Extract code blocks using a step-by-step approach that separates text from code.

        This method tries multiple strategies to identify code sections:
        1. Look for sections separated by numbered steps or headings
        2. Identify code-like sections based on indentation and Python syntax
        3. Extract sections between explanatory text
        """
        import logging

        logger = logging.getLogger("gollm.validator")

        # If the text is empty or too short, return empty list
        if not text or len(text) < 10:
            logger.warning("Text is too short for step-by-step extraction")
            return []

        # Strategy 1: Split by numbered steps or headings
        logger.info("Trying to split by numbered steps or headings")
        step_patterns = [
            r"\n\s*\d+\.\s+",  # Numbered steps like "1. Step one"
            r"\n\s*Step\s+\d+[:\s]",  # "Step 1: Do something"
            r"\n\s*#+\s+",  # Markdown headings like "# Step 1"
            r"\n\s*---+\s*\n",  # Horizontal rules as section separators
        ]

        sections = []
        for pattern in step_patterns:
            if re.search(pattern, text):
                logger.info(f"Found step pattern: {pattern}")
                # Split the text by the pattern
                parts = re.split(pattern, text)
                if len(parts) > 1:
                    # First part is usually introduction, skip it if it doesn't look like code
                    if self._looks_like_python(parts[0]):
                        sections.append(parts[0])

                    # Add the rest of the parts
                    sections.extend(parts[1:])
                    logger.info(f"Split text into {len(sections)} sections")
                    break

        # If we couldn't split by steps, try to use the whole text
        if not sections:
            sections = [text]

        # Strategy 2: Extract code-like sections from each part
        logger.info("Extracting code-like sections from each part")
        code_blocks = []
        for i, section in enumerate(sections):
            logger.info(
                f"Processing section {i+1}/{len(sections)}, length: {len(section)}"
            )

            # Skip very short sections
            if len(section) < 10:
                continue

            # Extract code-like parts from this section
            code_parts = self._extract_code_from_section(section)
            if code_parts:
                logger.info(f"Found {len(code_parts)} code parts in section {i+1}")
                code_blocks.extend(code_parts)

        # Clean up the code blocks
        cleaned_blocks = []
        for block in code_blocks:
            # Skip very short blocks that are likely not code
            if len(block) < 10:
                continue

            # Clean up the block
            cleaned = block.rstrip() + "\n"
            # Apply escape sequence formatting
            cleaned = self._format_code_with_escape_sequences(cleaned)
            cleaned_blocks.append(cleaned)

        return cleaned_blocks

    def _extract_code_from_section(self, section: str) -> List[str]:
        """Extract code-like parts from a section of text."""
        import logging

        logger = logging.getLogger("gollm.validator")

        # Check for code blocks first
        code_blocks = re.findall(r"```(?:\w*)?\n(.+?)(?:\n```|$)", section, re.DOTALL)
        if code_blocks:
            logger.info(f"Found {len(code_blocks)} markdown code blocks in section")
            return code_blocks

        # If no code blocks, check if the entire section looks like Python code
        if self._looks_like_python(section):
            logger.info("Entire section looks like Python code")
            return [section]

        # Try to extract code-like parts based on indentation patterns
        lines = section.split("\n")
        code_parts = []
        current_part = []
        in_code_block = False

        for line in lines:
            # Check if this line starts a code-like section
            if not in_code_block and (
                re.match(r"^\s{4,}\S", line)  # Indented by 4+ spaces
                or re.match(
                    r"^\s*(?:def|class|import|from|if|for|while|with)\b", line
                )  # Python keywords
            ):
                in_code_block = True
                current_part = [line]
            # Continue an existing code block
            elif in_code_block:
                # If we hit an empty line or a line that looks like text, end the code block
                if not line.strip() or (
                    not re.match(r"^\s+\S", line)  # Not indented
                    and not re.match(
                        r"^\s*(?:def|class|import|from|if|for|while|with|return|else|elif)\b",
                        line,
                    )  # Not a Python keyword
                ):
                    # End the code block if it's not just a blank line in the middle of code
                    if len(current_part) > 1:
                        code_parts.append("\n".join(current_part))
                    current_part = []
                    in_code_block = False
                else:
                    current_part.append(line)

        # Add the last code block if there is one
        if current_part:
            code_parts.append("\n".join(current_part))

        logger.info(
            f"Extracted {len(code_parts)} code-like parts based on indentation and keywords"
        )
        return code_parts

    def _looks_like_python(self, code: str) -> bool:
        """Sprawdza czy kod wygląda jak Python"""
        import logging

        logger = logging.getLogger(__name__)

        if not code or not code.strip():
            logger.warning("Empty code provided to _looks_like_python")
            return False

        # More comprehensive list of Python keywords and patterns
        python_keywords = [
            "def ",
            "class ",
            "import ",
            "from ",
            "if ",
            "for ",
            "while ",
            "return ",
            "with ",
            "try:",
            "except:",
            "finally:",
            "as ",
            "in ",
            "is ",
            "not ",
            "and ",
            "or ",
            "print(",
            "self.",
            "__init__",
            "lambda ",
            "async ",
            "await ",
            "yield ",
            # Common Python patterns
            " = ",
            "==",
            "!=",
            ">=",
            "<=",
            "+=",
            "-=",
            "*=",
            "/=",
            # Common Python libraries
            "import os",
            "import sys",
            "import re",
            "import json",
            "import time",
            "import numpy",
            "import pandas",
            "import matplotlib",
            "import requests",
        ]

        # Check for Python keywords
        has_keywords = any(keyword in code for keyword in python_keywords)

        # Check for Python indentation patterns (spaces at beginning of lines)
        indentation_pattern = re.search(r"\n\s{2,}\S", code)
        has_indentation = bool(indentation_pattern)

        # Check for Python docstrings
        docstring_pattern = re.search(r'""".*?"""', code, re.DOTALL)
        has_docstring = bool(docstring_pattern)

        # Check for Python function or class definitions
        definition_pattern = re.search(r"(def|class)\s+\w+\s*\(", code)
        has_definition = bool(definition_pattern)

        # Log the detection results
        if has_keywords or has_indentation or has_docstring or has_definition:
            logger.debug(
                f"Code looks like Python: keywords={has_keywords}, indentation={has_indentation}, docstring={has_docstring}, definition={has_definition}"
            )
            return True
        else:
            logger.debug("Code does not appear to be Python")
            return False

    def _clean_text_for_python(self, text: str) -> str:
        """Clean text to make it more likely to be valid Python code."""
        # Remove common prefixes that might appear before code
        prefixes_to_remove = [
            "Here's the solution:",
            "Here is the code:",
            "Here's the code:",
            "Here's the implementation:",
            "Here is the implementation:",
            "Here's how you can implement this:",
            "Here's how to implement this:",
            "Here's the Python code:",
            "Here is the Python code:",
        ]

        cleaned_text = text
        for prefix in prefixes_to_remove:
            if cleaned_text.startswith(prefix):
                cleaned_text = cleaned_text[len(prefix) :].lstrip()
                break

        # Ensure the text ends with a newline
        if cleaned_text and not cleaned_text.endswith("\n"):
            cleaned_text += "\n"

        return cleaned_text

    def validate_python_code(self, code: str) -> Dict[str, Any]:
        """Validate Python code syntax and structure.

        Args:
            code: The Python code to validate

        Returns:
            Dictionary with validation results
        """
        import logging

        logger = logging.getLogger("gollm.validator")

        logger.info(f"===== VALIDATING PYTHON CODE =====")
        logger.info(f"Code length: {len(code)}")
        logger.debug(f"Code first 200 chars: {code[:200]}...")

        if not code or not code.strip():
            logger.warning("Empty code provided for validation")
            return {
                "syntax_valid": False,
                "error_message": "Empty code",
                "error_type": "EmptyCode",
                "error_line": 0,
                "error_col": 0,
            }

        # Validate syntax using ast.parse
        syntax_result = self._validate_syntax(code)

        # Log the validation result
        if syntax_result["syntax_valid"]:
            logger.info("Python code syntax is valid")
        else:
            logger.warning(
                f"Python code syntax is invalid: {syntax_result['error_message']}"
            )
            logger.debug(
                f"Error at line {syntax_result['error_line']}, col {syntax_result['error_col']}"
            )

        return syntax_result

    def _validate_syntax(self, code: str) -> Dict[str, Any]:
        """Validate Python code syntax using ast.parse.

        Args:
            code: The Python code to validate

        Returns:
            Dictionary with validation results
        """
        import logging

        logger = logging.getLogger("gollm.validator")

        result = {
            "syntax_valid": False,
            "error_message": None,
            "error_type": None,
            "error_line": 0,
            "error_col": 0,
            "error_context": None,
        }

        try:
            # Try to parse the code with ast
            ast.parse(code)
            result["syntax_valid"] = True
            logger.info("Code syntax is valid")
            return result

        except SyntaxError as e:
            # Get detailed error information
            error_line = e.lineno if hasattr(e, "lineno") else 0
            error_col = e.offset if hasattr(e, "offset") else 0
            error_msg = str(e)

            # Get context around the error
            if error_line > 0 and code:
                lines = code.split("\n")
                if error_line <= len(lines):
                    context_start = max(0, error_line - 3)
                    context_end = min(len(lines), error_line + 2)
                    context_lines = lines[context_start:context_end]
                    error_context = "\n".join(
                        [
                            f"{i+context_start+1}: {line}"
                            for i, line in enumerate(context_lines)
                        ]
                    )

                    # Add a marker pointing to the error column
                    if error_col > 0 and error_line - 1 < len(lines):
                        marker = " " * (error_col - 1) + "^"
                        error_context += f"\n{marker}"
                else:
                    error_context = "<Context not available>"
            else:
                error_context = "<Context not available>"

            # Log detailed error information
            logger.warning(
                f"SyntaxError: {error_msg} at line {error_line}, col {error_col}"
            )
            logger.debug(f"Error context:\n{error_context}")

            # Update the result dictionary
            result.update(
                {
                    "syntax_valid": False,
                    "error_message": error_msg,
                    "error_type": "SyntaxError",
                    "error_line": error_line,
                    "error_col": error_col,
                    "error_context": error_context,
                }
            )

            return result

        except Exception as e:
            # Handle other parsing errors
            logger.warning(f"Unexpected error validating code: {str(e)}")

            result.update(
                {
                    "syntax_valid": False,
                    "error_message": str(e),
                    "error_type": type(e).__name__,
                }
            )

            return result

    def _format_code_with_escape_sequences(self, code: str) -> str:
        """
        Format code by properly handling escape sequences like \n and \t.
        This is needed when the LLM response contains literal escape sequences
        that should be interpreted as actual newlines and tabs.
        """
        import logging
        import re

        logger = logging.getLogger("gollm.validator")

        if not code:
            return code

        logger.info("Formatting code with escape sequences")

        # Check if the code contains escape sequences
        if (
            "\\n" in code
            or "\\t" in code
            or '\\"' in code
            or "\\'" in code
            or "\\u" in code
            or "\\x" in code
        ):
            logger.info("Found escape sequences in code, processing them")

            # Strategy 1: Use codecs.decode with unicode_escape
            try:
                import codecs

                formatted_code = codecs.decode(code, "unicode_escape")
                logger.info("Successfully formatted code using codecs.decode")
                return formatted_code
            except Exception as e:
                logger.warning(f"Failed to format code with codecs.decode: {e}")

            # Strategy 2: Try ast.literal_eval with proper escaping
            try:
                import ast

                # Prepare the code for literal_eval by ensuring it's properly quoted
                # and escape any existing quotes
                escaped_code = code.replace('"', '\\"').replace("'", "\\'")
                code_to_eval = f'"{escaped_code}"'

                # Use ast.literal_eval to safely evaluate the string
                formatted_code = ast.literal_eval(code_to_eval)
                logger.info(
                    "Successfully formatted code using ast.literal_eval with escaping"
                )
                return formatted_code
            except (SyntaxError, ValueError) as e:
                logger.warning(f"Failed to format code with ast.literal_eval: {e}")

            # Strategy 3: Try with triple quotes to handle multiline strings
            try:
                import ast

                code_to_eval = f'"""' + code + '"""'
                formatted_code = ast.literal_eval(code_to_eval)
                logger.info(
                    "Successfully formatted code using ast.literal_eval with triple quotes"
                )
                return formatted_code
            except (SyntaxError, ValueError) as e:
                logger.warning(f"Failed to format code with triple quotes: {e}")

            # Strategy 4: Manually replace common escape sequences
            try:
                formatted_code = code
                # Handle common escape sequences
                replacements = [
                    ("\\n", "\n"),  # Newline
                    ("\\t", "\t"),  # Tab
                    ("\\r", "\r"),  # Carriage return
                    ('\\"', '"'),  # Double quote
                    ("\\'", "'"),  # Single quote
                    ("\\\\", "\\"),  # Backslash
                    ("\\b", "\b"),  # Backspace
                    ("\\f", "\f"),  # Form feed
                ]

                for old, new in replacements:
                    formatted_code = formatted_code.replace(old, new)

                # Handle Unicode escapes like \u00A9 (copyright symbol)
                unicode_escapes = re.findall(r"\\u([0-9a-fA-F]{4})", formatted_code)
                for escape in unicode_escapes:
                    try:
                        char = chr(int(escape, 16))
                        formatted_code = formatted_code.replace(f"\\u{escape}", char)
                    except:
                        pass

                # Handle hex escapes like \x41 (A)
                hex_escapes = re.findall(r"\\x([0-9a-fA-F]{2})", formatted_code)
                for escape in hex_escapes:
                    try:
                        char = chr(int(escape, 16))
                        formatted_code = formatted_code.replace(f"\\x{escape}", char)
                    except:
                        pass

                logger.info(
                    "Formatted code using enhanced manual escape sequence replacement"
                )
                return formatted_code
            except Exception as e:
                logger.warning(f"Failed during manual escape sequence replacement: {e}")
                # If all else fails, return the original code
                return code

        # No escape sequences found, return as is
        return code
