"""End-to-end tests for Ollama LLM integration."""
import os
import asyncio
import pytest
from gollm.llm.ollama_adapter import OllamaLLMProvider
from gollm.llm.orchestrator import LLMOrchestrator

# Test configuration
TEST_CONFIG = {
    "model": "codellama:7b",
    "base_url": "http://localhost:11434",
    "timeout": 300,
    "temperature": 0.1,
    "token_limit": 4000
}

@pytest.fixture
def ollama_provider():
    """Fixture providing a configured Ollama provider."""
    return OllamaLLMProvider(TEST_CONFIG)

@pytest.fixture
def llm_orchestrator(ollama_provider):
    """Fixture providing an LLM orchestrator with Ollama provider."""
    return LLMOrchestrator(ollama_provider)

@pytest.mark.asyncio
async def test_ollama_generate_code(ollama_provider):
    """Test generating code with Ollama LLM."""
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
async def test_llm_orchestrator_integration(llm_orchestrator):
    """Test the LLM orchestrator with Ollama backend."""
    task = "Create a simple Flask web server"
    
    result = await llm_orchestrator.process_task(
        task=task,
        context={
            "project_config": {
                "framework": "flask",
                "language": "python"
            }
        }
    )
    
    assert "app = Flask" in result.get("generated_code", "")
    assert "@app.route" in result.get("generated_code", "")

@pytest.mark.asyncio
async def test_ollama_health_check(ollama_provider):
    """Test health check of Ollama service."""
    is_healthy = await ollama_provider.health_check()
    assert is_healthy is True

@pytest.mark.asyncio
async def test_ollama_error_handling(ollama_provider):
    """Test error handling with invalid model."""
    invalid_provider = OllamaLLMProvider({"model": "nonexistent-model-123"})
    response = await invalid_provider.generate_response("Test prompt")
    assert response["success"] is False
    assert "error" in response
