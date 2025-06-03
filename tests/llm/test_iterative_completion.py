"""Tests for the iterative code completion feature."""

import pytest
from unittest.mock import patch, MagicMock

from gollm.llm.orchestrator import LLMOrchestrator, LLMRequest
from gollm.validation.validators.incomplete_function_detector import (
    contains_incomplete_functions,
    format_for_completion,
    extract_completed_functions
)


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = MagicMock()
    config.llm_integration.api_provider = "test"
    config.llm_integration.providers = {"test": {}}
    return config


@pytest.fixture
def mock_code_validator():
    """Create a mock code validator for testing."""
    validator = MagicMock()
    validator.validate.return_value = {
        "code_extracted": True,
        "extracted_code": "def test_function():\n    pass\n",
        "code_quality": {"quality_score": 80},
    }
    validator.validate_file.return_value = {"quality_score": 85}
    return validator


def test_incomplete_function_detection():
    """Test that incomplete functions are properly detected."""
    # Code with incomplete function
    code = """
def complete_function():
    return True

def incomplete_function():
    pass
"""
    
    # Check if incomplete functions are detected
    has_incomplete, incomplete_funcs = contains_incomplete_functions(code)
    
    assert has_incomplete is True
    assert len(incomplete_funcs) == 1
    assert incomplete_funcs[0]["name"] == "incomplete_function"


def test_format_for_completion_output():
    """Test that the format_for_completion function produces correct output."""
    # Code with incomplete function
    code = """
def complete_function():
    return True

def incomplete_function():
    pass
"""
    
    # Get incomplete functions
    has_incomplete, incomplete_funcs = contains_incomplete_functions(code)
    
    # Format for completion
    formatted = format_for_completion(incomplete_funcs, code)
    
    # Check that the formatted code contains the expected markers
    assert "TODO: Implement the incomplete_function function below" in formatted
    assert "The following code contains incomplete functions" in formatted
    assert "def incomplete_function():" in formatted


def test_extract_completed_functions_output():
    """Test that completed functions are correctly extracted and merged."""
    # Original code with incomplete function
    original_code = """
def complete_function():
    return True

def incomplete_function():
    pass
"""
    
    # Completed code from LLM
    completed_code = """
def complete_function():
    return True

def incomplete_function():
    # Implementation added
    data = process_data()
    return data * 2
"""
    
    # Extract and merge completed functions
    merged_code = extract_completed_functions(original_code, completed_code)
    
    # Check that the incomplete function was replaced with the completed version
    assert "pass" not in merged_code
    assert "Implementation added" in merged_code
    assert "process_data()" in merged_code


@patch("gollm.llm.orchestrator.LLMOrchestrator._simulate_llm_call")
async def test_orchestrator_iterative_completion(mock_llm_call, mock_config, mock_code_validator):
    """Test that the orchestrator handles iterative completion correctly."""
    # Create orchestrator with mocked dependencies
    orchestrator = LLMOrchestrator(mock_config, code_validator=mock_code_validator)
    
    # Mock first response with incomplete function
    first_response = """
def complete_function():
    return True

def incomplete_function():
    pass
"""
    
    # Mock second response with completed function
    second_response = """
def complete_function():
    return True

def incomplete_function():
    # Implementation added
    data = process_data()
    return data * 2
"""
    
    # Configure mock to return different responses for each call
    mock_llm_call.side_effect = [first_response, second_response]
    
    # Configure validator to detect incomplete functions in first response
    mock_code_validator.validate.side_effect = [
        # First validation - incomplete function detected
        {
            "code_extracted": True,
            "extracted_code": first_response,
            "code_quality": {"quality_score": 80},
            "has_incomplete_functions": True,
            "incomplete_functions": [{"name": "incomplete_function", "body": "    pass", "signature": "def incomplete_function():"}]
        },
        # Second validation - no incomplete functions
        {
            "code_extracted": True,
            "extracted_code": second_response,
            "code_quality": {"quality_score": 90},
            "has_incomplete_functions": False
        }
    ]
    
    # Create request
    request = LLMRequest(
        user_request="Generate a function",
        context={},
        session_id="test_session",
        max_iterations=2
    )
    
    # Process request
    response = await orchestrator._process_llm_request(request)
    
    # Check that both LLM calls were made
    assert mock_llm_call.call_count == 2
    
    # Check that the final response contains the completed function
    assert "Implementation added" in response.generated_code
    assert "pass" not in response.generated_code
    
    # Check that the quality score was improved
    assert response.quality_score > 80
