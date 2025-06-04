"""Comprehensive tests for the Ollama LLM Provider."""
import json
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Mock the openai module before any imports
sys.modules['openai'] = MagicMock()

# Mock the OpenAIClient class
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

from gollm.llm.providers.ollama import (
    OllamaLLMProvider,
    OllamaConfig,
    OllamaHttpClient,
    OllamaHttpAdapter
)

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
}

@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client for testing."""
    with patch('gollm.llm.providers.ollama.http.client.OllamaHttpClient') as mock:
        yield mock

@pytest.fixture
def mock_http_adapter():
    """Create a mock HTTP adapter for testing."""
    with patch('gollm.llm.providers.ollama.http.adapter.OllamaHttpAdapter') as mock:
        yield mock

@pytest.fixture
async def ollama_provider(mock_http_client, mock_http_adapter):
    """Create an Ollama provider instance with mocked dependencies."""
    # Configure the mocks
    mock_client_instance = AsyncMock(spec=OllamaHttpClient)
    mock_adapter_instance = MagicMock(spec=OllamaHttpAdapter)
    
    # Set up the mock methods
    mock_client_instance.generate = AsyncMock(return_value={"response": TEST_RESPONSE})
    mock_client_instance.stream = AsyncMock(return_value=[
        {"response": "Test"},
        {"response": " response"}
    ])
    mock_client_instance.health_check = AsyncMock(return_value={"status": "ok"})
    
    mock_http_client.return_value = mock_client_instance
    mock_http_adapter.return_value = mock_adapter_instance
    
    # Create the provider with test config
    provider = OllamaLLMProvider(TEST_CONFIG)
    
    return provider, mock_client_instance, mock_adapter_instance

@pytest.mark.asyncio
async def test_generate_text(ollama_provider):
    """Test generating text with the Ollama provider."""
    provider, mock_client, _ = ollama_provider
    
    # Call the method
    response = await provider.generate(TEST_PROMPT)
    
    # Assertions
    assert response == TEST_RESPONSE
    mock_client.generate.assert_awaited_once_with(
        prompt=TEST_PROMPT,
        model=TEST_MODEL,
        temperature=TEST_CONFIG["temperature"],
        max_tokens=TEST_CONFIG["max_tokens"]
    )

@pytest.mark.asyncio
async def test_stream_text(ollama_provider):
    """Test streaming text with the Ollama provider."""
    provider, mock_client, _ = ollama_provider
    
    # Call the method and collect chunks
    chunks = []
    async for chunk in provider.stream(TEST_PROMPT):
        chunks.append(chunk)
    
    # Assertions
    assert "".join(chunks) == "Test response"
    mock_client.stream.assert_awaited_once_with(
        prompt=TEST_PROMPT,
        model=TEST_MODEL,
        temperature=TEST_CONFIG["temperature"],
        max_tokens=TEST_CONFIG["max_tokens"]
    )

@pytest.mark.asyncio
async def test_health_check(ollama_provider):
    """Test health check functionality."""
    provider, mock_client, _ = ollama_provider
    
    # Configure the mock
    mock_client.health_check.return_value = {"status": "ok"}
    
    # Call the method under test
    result = await provider.health_check()
    
    # Assertions
    assert result == {"status": "ok"}
    mock_client.health_check.assert_awaited_once()

def test_config_initialization():
    """Test that the OllamaConfig is properly initialized."""
    config = OllamaConfig.from_dict(TEST_CONFIG)
    
    # Assertions
    assert config.model == TEST_CONFIG["model"]
    assert config.base_url == TEST_CONFIG["base_url"]
    assert config.timeout == TEST_CONFIG["timeout"]
    assert config.temperature == TEST_CONFIG["temperature"]
    assert config.max_tokens == TEST_CONFIG["max_tokens"]

@pytest.mark.asyncio
async def test_error_handling(ollama_provider):
    """Test error handling in the Ollama provider."""
    provider, mock_client, _ = ollama_provider
    
    # Set up the mock to raise an exception
    mock_client.generate.side_effect = Exception("API Error")
    
    # Test that the exception is properly propagated
    with pytest.raises(Exception) as exc_info:
        await provider.generate(TEST_PROMPT)
    
    assert "API Error" in str(exc_info.value)
    mock_client.generate.assert_awaited_once()

@pytest.mark.asyncio
async def test_custom_parameters(ollama_provider):
    """Test passing custom parameters to the Ollama provider."""
    provider, mock_client, _ = ollama_provider
    
    # Custom parameters
    custom_params = {
        "temperature": 0.9,
        "max_tokens": 200,
        "top_p": 0.9,
        "top_k": 50
    }
    
    # Call the method with custom parameters
    await provider.generate(TEST_PROMPT, **custom_params)
    
    # Assertions
    mock_client.generate.assert_awaited_once_with(
        prompt=TEST_PROMPT,
        model=TEST_MODEL,
        **custom_params
    )
