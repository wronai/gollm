"""Tests for the incomplete function detector module."""

import pytest
from gollm.validation.validators.incomplete_function_detector import (
    contains_incomplete_functions,
    format_for_completion,
    extract_completed_functions,
    _contains_placeholder_comments
)


def test_empty_code():
    """Test that empty code returns no incomplete functions."""
    code = ""
    has_incomplete, incomplete_funcs = contains_incomplete_functions(code)
    assert not has_incomplete
    assert len(incomplete_funcs) == 0


def test_complete_function():
    """Test that a complete function is not detected as incomplete."""
    code = """
def add(a, b):
    'Add two numbers.'
    return a + b
"""
    has_incomplete, incomplete_funcs = contains_incomplete_functions(code)
    assert not has_incomplete
    assert len(incomplete_funcs) == 0


def test_pass_function():
    """Test that a function with only 'pass' is detected as incomplete."""
    code = """
def process_data(data):
    'Process the data.'
    pass
"""
    has_incomplete, incomplete_funcs = contains_incomplete_functions(code)
    assert has_incomplete
    assert len(incomplete_funcs) == 1
    assert incomplete_funcs[0]["name"] == "process_data"


def test_ellipsis_function():
    """Test that a function with ellipsis is detected as incomplete."""
    code = """
def calculate_total(items):
    'Calculate the total of all items.'
    ...
"""
    has_incomplete, incomplete_funcs = contains_incomplete_functions(code)
    assert has_incomplete
    assert len(incomplete_funcs) == 1
    assert incomplete_funcs[0]["name"] == "calculate_total"


def test_todo_comment_function():
    """Test that a function with TODO comments is detected as incomplete."""
    code = """
def validate_user(user_id):
    'Validate the user ID.'
    # TODO: Implement validation logic
    return True
"""
    has_incomplete, incomplete_funcs = contains_incomplete_functions(code)
    assert has_incomplete
    assert len(incomplete_funcs) == 1
    assert incomplete_funcs[0]["name"] == "validate_user"


def test_multiple_incomplete_functions():
    """Test detection of multiple incomplete functions."""
    code = """
def function1():
    pass

def function2():
    'This is complete.'
    return True

def function3():
    # TODO: Implement this
    return None
"""
    has_incomplete, incomplete_funcs = contains_incomplete_functions(code)
    assert has_incomplete
    assert len(incomplete_funcs) == 2
    function_names = [func["name"] for func in incomplete_funcs]
    assert "function1" in function_names
    assert "function3" in function_names
    assert "function2" not in function_names


def test_format_for_completion():
    """Test formatting code with incomplete functions for LLM completion."""
    code = """
def complete_function():
    return True

def incomplete_function():
    pass
"""
    has_incomplete, incomplete_funcs = contains_incomplete_functions(code)
    formatted_code = format_for_completion(incomplete_funcs, code)
    
    assert "TODO: Implement the incomplete_function function below" in formatted_code
    assert "The following code contains incomplete functions" in formatted_code


def test_extract_completed_functions():
    """Test extracting and merging completed functions."""
    original_code = """
def function1():
    return True

def incomplete_function():
    pass
"""
    
    completed_code = """
def function1():
    return True

def incomplete_function():
    # This function has been completed
    result = process_data()
    return result * 2
"""
    
    merged_code = extract_completed_functions(original_code, completed_code)
    
    # Check that the pass statement was replaced with the implementation
    assert "pass" not in merged_code
    # Check that the function now contains the implementation
    assert "result = process_data()" in merged_code
    assert "return result * 2" in merged_code
