"""
Pytest configuration and shared fixtures for goLLM tests
"""

import pytest
import tempfile
import shutil
from pathlib import Path

@pytest.fixture
def temp_project():
    """Create a temporary project directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

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
    return '''
def bad_function(a, b, c, d, e, f):  # Too many parameters
    print("This is bad")  # Print statement
    # No docstring
    if a > 0:
        if b > 0:
            if c > 0:  # High complexity
                return a + b + c + d + e + f
    return 0
'''