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
def llm_orchestrator(mocker, temp_project_dir):
    """Fixture providing an LLM orchestrator with a mocked Ollama provider."""
    # Create a simple config for testing
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
    
    # Create a mock LLM provider
    class MockLLMProvider:
        def __init__(self, config):
            self.config = config
            
        async def generate_response(self, prompt, context=None):
            from gollm.llm.response_validator import LLMResponse
            return LLMResponse(
                success=True,
                generated_code="""from flask import Flask\napp = Flask(__name__)\n\n@app.route('/')\ndef home():\n    return 'Hello, World!'\n\nif __name__ == '__main__':\n    app.run(debug=True)""",
                metadata={"model": "codellama:7b", "tokens_used": 128}
            )
            
        async def is_available(self):
            return True
    
    # Create the orchestrator with the config
    orchestrator = LLMOrchestrator(config=config)
    
    # Create and set the mock provider
    mock_provider = MockLLMProvider(config)
    orchestrator.llm_provider = mock_provider
    
    # Mock the context builder with an async function
    async def mock_build_context(context):
        return {
            "execution_context": {"recent_changes": [], "current_file": "test.py"},
            "todo_context": {"todos": [], "pending_tasks": 0},
            "changelog_context": {"latest_version": "0.1.0"},
            "project_config": {"language": "python", "framework": "flask"},
            "recent_changes": []
        }
    
    # Create a mock context builder with the async function
    mock_context_builder = mocker.MagicMock()
    mock_context_builder.build_context.side_effect = mock_build_context
    orchestrator.context_builder = mock_context_builder
    
    # Create empty TODO and CHANGELOG files
    os.makedirs(temp_project_dir, exist_ok=True)
    for filename in ["TODO.md", "CHANGELOG.md"]:
        with open(os.path.join(temp_project_dir, filename), 'w') as f:
            f.write("# " + filename + "\n\n")
    
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
async def test_llm_orchestrator_integration(llm_orchestrator, mocker):
    """Test the LLM orchestrator with Ollama backend."""
    from gollm.llm.orchestrator import LLMResponse
    from gollm.llm.ollama_adapter import OllamaLLMProvider
    
    # Create a mock response
    mock_code = """from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run(debug=True)"""
    
    # Create a proper LLMResponse object
    mock_llm_response = LLMResponse(
        generated_code=mock_code,
        explanation="Created a simple Flask web server with a single route.",
        validation_result={
            "code_extracted": True,
            "extracted_code": mock_code,
            "syntax_valid": True,
            "violations": [],
            "explanation": "Code is valid and follows all rules"
        },
        iterations_used=1,
        quality_score=95
    )
    
    # Create a mock LLM response string that matches what the LLM would return
    mock_llm_output = f"""```python
{mock_code}
```

Explanation: Created a simple Flask web server with a single route."""
    
    # Patch the Ollama provider to return our mock response
    with mocker.patch('gollm.llm.ollama_adapter.OllamaLLMProvider.generate_response', 
                     return_value=mock_llm_output):
        # Patch the context builder
        mock_context = {
            "execution_context": {"recent_changes": [], "current_file": "test.py"},
            "todo_context": {"todos": [], "pending_tasks": 0},
            "changelog_context": {"latest_version": "0.1.0"},
            "project_config": {"language": "python", "framework": "flask"},
            "recent_changes": []
        }
        
        with mocker.patch('gollm.llm.orchestrator.ContextBuilder.build_context', 
                         return_value=mock_context):
            # Patch the response validator
            mock_validation_result = {
                "code_extracted": True,
                "extracted_code": mock_code,
                "syntax_valid": True,
                "violations": [],
                "explanation": "Code is valid and follows all rules"
            }
            
            with mocker.patch('gollm.llm.response_validator.ResponseValidator.validate_response',
                            return_value=mock_validation_result):
                # Mock the code validator
                with mocker.patch('gollm.validation.validators.CodeValidator.validate_file',
                                return_value={"success": True, "violations": []}):
                    # Test data
                    user_request = "Create a simple Flask web server"
                    
                    # Call the method under test
                    response = await llm_orchestrator.handle_code_generation_request(
                        user_request=user_request,
                        context={"project_config": {"framework": "flask", "language": "python"}}
                    )
                    
                    # Verify the response
                    assert response is not None
                    assert response.generated_code is not None
                    assert isinstance(response.generated_code, str)
                    assert "flask" in response.generated_code.lower()
                    assert "@app.route" in response.generated_code
                    assert "app = Flask" in response.generated_code

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
