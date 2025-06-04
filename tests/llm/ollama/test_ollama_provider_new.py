"""Comprehensive tests for the Ollama LLM Provider."""
import json
import sys
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Mock the openai module before any imports
sys.modules['openai'] = MagicMock()

# Mock the aiohttp module
sys.modules['aiohttp'] = MagicMock()

# Mock the OpenAIClient import
class MockOpenAIClient:
    pass

# Mock the OpenAILlmProvider class
class MockOpenAILlmProvider:
    pass

# Create a mock for the openai provider module
mock_openai_provider = type('module', (), {
    'OpenAIClient': MockOpenAIClient,
    'OpenAILlmProvider': MockOpenAILlmProvider
})
sys.modules['gollm.llm.providers.openai'] = mock_openai_provider

# Test data
TEST_MODEL = "llama2"
TEST_PROMPT = "Test prompt"
TEST_RESPONSE = "Test response"
TEST_CONFIG = {
    "model": TEST_MODEL,
    "base_url": "http://localhost:11434",
    "timeout": 30,
    "temperature": 0.7,
    "max_tokens": 100,
    "api_type": "chat",
    "interactive": True
}

# Mock the OllamaAdapter class
class MockOllamaAdapter:
    def __init__(self, config):
        self.config = config
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
        
    async def is_available(self):
        return True
        
    async def list_models(self):
        return ["llama2", "codellama:7b"]
        
    async def generate_code(self, prompt, context=None):
        return {"response": TEST_RESPONSE}
        
    async def health_check(self):
        return {
            "status": True,
            "model_available": True,
            "error": None,
            "config": {
                "base_url": "http://localhost:11434",
                "model": "llama2",
                "timeout": 30
            },
            "details": {
                "service": {"available": True, "response_time_ms": 10.5},
                "model": {"available": True, "name": "llama2"}
            }
        }

@pytest.fixture
def mock_ollama_adapter():
    with patch('gollm.llm.ollama_adapter.OllamaAdapter') as mock:
        adapter = MockOllamaAdapter({})
        mock.return_value = adapter
        yield adapter

@pytest.fixture
async def ollama_provider(mock_ollama_adapter):
    """Create an Ollama provider instance with mocked dependencies."""
    from gollm.llm.ollama_adapter import OllamaLLMProvider
    
    # Create the provider with test config
    provider = OllamaLLMProvider(TEST_CONFIG)
    
    # Set up the mock methods
    mock_ollama_adapter.generate_code = AsyncMock(return_value={"response": TEST_RESPONSE})
    mock_ollama_adapter.health_check = AsyncMock(return_value={
        "status": True,
        "model_available": True,
        "error": None,
        "config": {
            "base_url": "http://localhost:11434",
            "model": "llama2",
            "timeout": 30
        },
        "details": {
            "service": {"available": True, "response_time_ms": 10.5},
            "model": {"available": True, "name": "llama2"}
        }
    })
    
    return provider, mock_ollama_adapter

@pytest.mark.asyncio
async def test_generate_response(ollama_provider):
    """Test generating a response with the Ollama provider."""
    provider, mock_adapter = ollama_provider
    
    # Call the method
    response = await provider.generate_response(TEST_PROMPT)
    
    # Assertions
    assert response["response"] == TEST_RESPONSE
    mock_adapter.generate_code.assert_awaited_once_with(
        prompt=TEST_PROMPT,
        context=None
    )

@pytest.mark.asyncio
async def test_health_check(ollama_provider):
    """Test the health check functionality."""
    provider, mock_adapter = ollama_provider
    
    # Call the method
    health = await provider.health_check()
    
    # Assertions
    assert health["status"] is True
    assert health["model_available"] is True
    mock_adapter.health_check.assert_awaited_once()

@pytest.mark.asyncio
async def test_error_handling(ollama_provider):
    """Test error handling in the Ollama provider."""
    provider, mock_adapter = ollama_provider
    
    # Set up the mock to raise an exception
    mock_adapter.generate_code.side_effect = Exception("API Error")
    
    # Test that the exception is properly propagated
    with pytest.raises(Exception) as exc_info:
        await provider.generate_response(TEST_PROMPT)
    
    assert "API Error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_custom_parameters(ollama_provider):
    """Test passing custom parameters to the Ollama provider."""
    provider, mock_adapter = ollama_provider
    
    # Custom context
    context = {"system_prompt": "You are a helpful assistant"}
    
    # Call the method with custom context
    await provider.generate_response(TEST_PROMPT, context=context)
    
    # Assertions
    mock_adapter.generate_code.assert_awaited_once_with(
        prompt=TEST_PROMPT,
        context=context
    )
