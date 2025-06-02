"""End-to-end tests for Ollama LLM integration."""
import os
import pytest
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from dataclasses import asdict

# Import the config dataclasses
from gollm.config.config import GollmConfig, ValidationRules, ProjectManagement, LLMIntegration

# Add the parent directory to the Python path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import shutil
import os

# Test configuration
TEST_CONFIG = GollmConfig(
    project_root=os.getcwd(),
    validation_rules=ValidationRules(
        max_function_lines=50,
        max_file_lines=1000,
        max_function_params=5,
        max_cyclomatic_complexity=10,
        forbid_print_statements=True,
        forbid_global_variables=True,
        require_docstrings=True,
        naming_convention="snake_case"
    ),
    project_management=ProjectManagement(
        todo_file="TODO.md",
        changelog_file="CHANGELOG.md"
    ),
    llm_integration=LLMIntegration(
        model_name="codellama:7b",
        max_iterations=3,
        token_limit=4000,
        api_provider="ollama",
        providers={
            "ollama": {
                "base_url": "http://localhost:11434",
                "model": "codellama:7b",
                "temperature": 0.1,
                "token_limit": 4000,
                "timeout": 300
            }
        }
    )
)

from gollm.llm.ollama_adapter import OllamaLLMProvider
from gollm.llm.orchestrator import LLMOrchestrator

@pytest.fixture(scope="module")
def temp_project_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp(prefix="gollm_test_")
    yield temp_dir
    # Cleanup after tests
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def ollama_provider():
    """Fixture providing a configured Ollama provider."""
    # Create a copy of the config to avoid modifying the original
    config = GollmConfig(**asdict(TEST_CONFIG))
    return OllamaLLMProvider(config)

@pytest.fixture
def llm_orchestrator(ollama_provider, temp_project_dir):
    """Fixture providing an LLM orchestrator with Ollama provider."""
    # Create a proper config object using the dataclasses
    validation_rules = ValidationRules(
        max_function_lines=50,
        max_file_lines=1000,
        max_function_params=5,
        max_cyclomatic_complexity=10,
        forbid_print_statements=True,
        forbid_global_variables=True,
        require_docstrings=True,
        naming_convention="snake_case"
    )
    
    project_management = ProjectManagement(
        todo_file=str(Path(temp_project_dir) / "TODO.md"),
        changelog_file=str(Path(temp_project_dir) / "CHANGELOG.md")
    )
    
    llm_integration = LLMIntegration(
        model_name="codellama:7b",
        max_iterations=3,
        token_limit=4000,
        api_provider="ollama",
        providers={
            "ollama": {
                "base_url": "http://localhost:11434",
                "model": "codellama:7b",
                "temperature": 0.1,
                "token_limit": 4000,
                "timeout": 300
            }
        }
    )
    
    # Create the main config
    config = GollmConfig(
        project_root=temp_project_dir,
        validation_rules=validation_rules,
        project_management=project_management,
        llm_integration=llm_integration
    )
    
    # Add the llm_provider as an attribute to the config
    config.llm_provider = ollama_provider
    
    # Create empty TODO and CHANGELOG files
    os.makedirs(temp_project_dir, exist_ok=True)
    for filename in ["TODO.md", "CHANGELOG.md"]:
        with open(os.path.join(temp_project_dir, filename), 'w') as f:
            f.write("# " + filename + "\n\n")
    
    # Create the orchestrator with the config
    orchestrator = LLMOrchestrator(config=config)
    
    # Add the provider to the orchestrator for testing
    orchestrator.llm_provider = ollama_provider
    
    return orchestrator

@pytest.mark.asyncio
async def test_ollama_generate_code(ollama_provider, mocker):
    """Test generating code with Ollama LLM."""
    # Mock the adapter's generate_response method
    mock_response = {
        "success": True,
        "generated_code": """
        import math
        
        def factorial(n):
            '''Calculate factorial of a number.'''
            if n < 0:
                raise ValueError("Factorial is not defined for negative numbers")
            return 1 if n == 0 else n * factorial(n - 1)
        """,
        "metadata": {
            "model": "codellama:7b",
            "tokens_used": 42
        }
    }
    
    # Mock the adapter's generate_code method
    mocker.patch.object(ollama_provider.adapter, 'generate_code', 
                       return_value=mock_response)
    
    prompt = "Write a Python function that calculates factorial"
    
    response = await ollama_provider.generate_response(
        prompt=prompt,
        context={
            "project_config": {
                "validation_rules": {
                    "required_imports": ["math"],
                    "required_functions": ["factorial"]
                }
            }
        }
    )
    
    assert response["success"] is True
    assert "def factorial" in response.get("generated_code", "")

@pytest.mark.asyncio
async def test_llm_orchestrator_integration(llm_orchestrator, mocker, temp_project_dir):
    """Test the LLM orchestrator with Ollama backend."""
    # Create a proper config object for the test
    class TestConfig:
        def __init__(self, config_dict):
            for key, value in config_dict.items():
                if isinstance(value, dict):
                    setattr(self, key, TestConfig(value))
                else:
                    setattr(self, key, value)
    
    config = {
        "project_root": temp_project_dir,
        "project_management": {
            "todo_file": os.path.join(temp_project_dir, "TODO.md"),
            "changelog_file": os.path.join(temp_project_dir, "CHANGELOG.md")
        },
        "model": "codellama:7b",
        "base_url": "http://localhost:11434",
        "timeout": 300,
        "temperature": 0.1,
        "token_limit": 4000
    }
    
    config_obj = TestConfig(config)
    
    # Mock the context builder to return a simple context
    mock_context = {
        "execution_context": {"recent_changes": [], "current_file": "test.py"},
        "todo_context": {"todos": [], "pending_tasks": 0},
        "changelog_context": {"latest_version": "0.1.0"},
        "project_config": {"language": "python", "framework": "flask"},
        "recent_changes": []
    }
    
    # Mock the LLM provider's generate_response
    mock_response = {
        "success": True,
        "generated_code": """
        from flask import Flask
        app = Flask(__name__)
        
        @app.route('/')
        def home():
            return 'Hello, World!'
            
        if __name__ == '__main__':
            app.run(debug=True)
        """,
        "metadata": {
            "model": "codellama:7b",
            "tokens_used": 128
        }
    }
    
    # Update the orchestrator's config
    llm_orchestrator.llm_provider.config = config_obj
    
    # Mock the methods
    mocker.patch.object(llm_orchestrator.llm_provider, 'generate_response', 
                       return_value=mock_response)
    mocker.patch.object(llm_orchestrator.context_builder, 'build_context',
                       return_value=mock_context)
    
    user_request = "Create a simple Flask web server"
    
    # Create a request context
    request = {
        "user_request": user_request,
        "context": {
            "project_config": {
                "framework": "flask",
                "language": "python"
            }
        },
        "session_id": "test_session_123"
    }
    
    # Call the handle_code_generation_request method and capture the response
    response = await llm_orchestrator.handle_code_generation_request(
        user_request=user_request,
        context=request["context"]
    )
    
    # Verify the response contains the expected keys
    assert response is not None
    assert response.get("success") is True
    assert "generated_code" in response
    assert "flask" in response["generated_code"].lower()
    assert "@app.route" in response["generated_code"]
    assert "app = Flask" in response["generated_code"]

@pytest.mark.asyncio
async def test_ollama_health_check(ollama_provider, mocker):
    """Test health check of Ollama service."""
    # Mock the health check to avoid actual network calls in tests
    mocker.patch.object(ollama_provider.adapter, 'is_available', return_value=True)
    is_healthy = await ollama_provider.health_check()
    assert is_healthy is True

@pytest.mark.asyncio
async def test_ollama_error_handling(mocker):
    """Test error handling with invalid model."""
    # Mock the adapter to simulate an error
    mock_adapter = mocker.MagicMock()
    mock_adapter.generate_response.side_effect = Exception("Model not found")
    
    # Create a provider with a mock adapter
    provider = OllamaLLMProvider({"model": "nonexistent-model-123"})
    provider.adapter = mock_adapter
    
    response = await provider.generate_response("Test prompt")
    assert response["success"] is False
    assert "error" in response
