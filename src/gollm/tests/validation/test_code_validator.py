"""Tests for the code validation module."""

import os
import tempfile
import unittest
from pathlib import Path

from gollm.validation.code_validator import (attempt_syntax_fix,
                                             extract_code_blocks,
                                             is_valid_python,
                                             looks_like_prompt,
                                             validate_and_extract_code)


class TestCodeValidator(unittest.TestCase):
    """Test cases for the code validator module."""

    def test_valid_python_code(self):
        """Test validation of valid Python code."""
        code = """
def hello_world():
    print("Hello, World!")
    
if __name__ == "__main__":
    hello_world()
"""
        result = is_valid_python(code)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.issues), 0)

    def test_invalid_python_code(self):
        """Test validation of invalid Python code."""
        code = """
def hello_world():
    print("Hello, World!
    
if __name__ == "__main__":
    hello_world()
"""
        result = is_valid_python(code)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("Syntax error" in issue for issue in result.issues))

    def test_prompt_detection(self):
        """Test detection of prompts vs code."""
        # Test prompt-like text
        prompt = (
            "Create a Python class for a user with name, email, and password fields."
        )
        self.assertTrue(looks_like_prompt(prompt))

        # Test code
        code = """
class User:
    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password
"""
        self.assertFalse(looks_like_prompt(code))

        # Test mixed content
        mixed = """
Create a Python class for a user with name, email, and password fields.

Here's the implementation:

```python
class User:
    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password
```
"""
        self.assertTrue(looks_like_prompt(mixed))

    def test_code_extraction(self):
        """Test extraction of code blocks from text."""
        mixed = """
Create a Python class for a user with name, email, and password fields.

Here's the implementation:

```python
class User:
    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password
```
"""
        blocks = extract_code_blocks(mixed)
        self.assertEqual(len(blocks), 1)
        self.assertIn("class User:", blocks[0])

    def test_syntax_fix(self):
        """Test fixing of common syntax errors."""
        # Test unterminated string
        code_with_error = """
def hello():
    print("Hello, World!
"""
        fixed_code = attempt_syntax_fix(code_with_error)
        self.assertIsNotNone(fixed_code)
        result = is_valid_python(fixed_code)
        self.assertTrue(result.is_valid)

        # Test missing closing parenthesis
        code_with_error = """
def hello():
    print("Hello, World!"
"""
        fixed_code = attempt_syntax_fix(code_with_error)
        self.assertIsNotNone(fixed_code)
        result = is_valid_python(fixed_code)
        self.assertTrue(result.is_valid)

    def test_validate_and_extract_code(self):
        """Test the main validate_and_extract_code function."""
        # Test with valid code
        valid_code = """
def hello_world():
    print("Hello, World!")
"""
        is_valid, validated_code, issues = validate_and_extract_code(valid_code, "py")
        self.assertTrue(is_valid)
        self.assertEqual(validated_code, valid_code)
        self.assertEqual(len(issues), 0)

        # Test with prompt-like text containing code blocks
        prompt_with_code = """
Create a function that prints "Hello, World!".

Here's the implementation:

```python
def hello_world():
    print("Hello, World!")
```
"""
        is_valid, validated_code, issues = validate_and_extract_code(
            prompt_with_code, "py"
        )
        self.assertTrue(is_valid)
        self.assertIn("def hello_world():", validated_code)
        self.assertTrue(any("Extracted code from prompt" in issue for issue in issues))

        # Test with pure prompt, no code
        pure_prompt = "Create a function that prints Hello, World!"
        is_valid, validated_code, issues = validate_and_extract_code(pure_prompt, "py")
        self.assertFalse(is_valid)
        self.assertTrue(any("prompt, not code" in issue for issue in issues))

        # Test with code containing syntax errors
        code_with_error = """
def hello_world():
    print("Hello, World!
"""
        is_valid, validated_code, issues = validate_and_extract_code(
            code_with_error, "py"
        )
        self.assertTrue(is_valid)  # Should be valid because we fixed it
        self.assertNotEqual(
            validated_code, code_with_error
        )  # Should be different after fixing
        self.assertTrue(any("Syntax error" in issue for issue in issues))

    def test_real_world_example(self):
        """Test with the real-world example from the user."""
        problematic_content = """Stwórz klasę użytkownika"""

        is_valid, validated_code, issues = validate_and_extract_code(
            problematic_content, "py"
        )
        self.assertFalse(is_valid)
        self.assertTrue(any("prompt" in issue.lower() for issue in issues))


if __name__ == "__main__":
    unittest.main()
