"""
Pytest configuration and shared fixtures for goLLM tests
"""

import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Generator

import pytest

# Default test configuration
LLM_MODEL = os.getenv("GOLLM_MODEL", "tinyllama:latest")
LLM_TEST_TIMEOUT = int(os.getenv("GOLLM_TEST_TIMEOUT", "30"))  # seconds


def llm_test(timeout: int = LLM_TEST_TIMEOUT):
    """Decorator to mark tests as LLM tests with a configurable timeout.
    
    Args:
        timeout: Timeout in seconds for the test
    """
    def decorator(test_func):
        test_func._llm_test = True
        test_func._llm_timeout = timeout
        return test_func
    return decorator


@pytest.fixture
def temp_project() -> Generator[Path, None, None]:
    """Create a temporary project directory for testing."""
    temp_dir = tempfile.mkdtemp()
    try:
        yield Path(temp_dir)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def llm_model() -> str:
    """Fixture to get the LLM model to use for tests."""
    return LLM_MODEL

@pytest.fixture(autouse=True)
def llm_test_timeout(request):
    """Automatically add timeout to LLM tests."""
    # Skip if not an LLM test or no timeout needed
    if not hasattr(request.node.function, '_llm_test'):
        return
    
    timeout = getattr(request.node.function, '_llm_timeout', LLM_TEST_TIMEOUT)
    start_time = time.time()
    
    def timeout_check():
        if time.time() - start_time > timeout:
            raise TimeoutError(f"Test exceeded timeout of {timeout} seconds")
    
    # Add a finalizer to check the timeout
    request.addfinalizer(timeout_check)

@pytest.fixture
def sample_python_code():
    """Sample Python code for testing"""
    return '''
def sample_function(param1, param2):
    """
    Sample function for testing.
    
    Args:
        param1: First parameter
        param2: Second parameter
        
    Returns:
        Combined result
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Processing parameters")
    
    return param1 + param2

class SampleClass:
    """Sample class for testing"""
    
    def __init__(self, value):
        self.value = value
    
    def get_value(self):
        """Returns the stored value"""
        return self.value
'''


@pytest.fixture
def bad_python_code():
    """Bad Python code with violations for testing"""
    return """
def bad_function(a, b, c, d, e, f):  # Too many parameters
    print("This is bad")  # Print statement
    # No docstring
    if a > 0:
        if b > 0:
            if c > 0:  # High complexity
                return a + b + c + d + e + f
    return 0
"""
