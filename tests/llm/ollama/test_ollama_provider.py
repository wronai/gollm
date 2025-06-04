"""Comprehensive tests for the Ollama LLM Provider."""
import json
import sys
import types
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

# Create mock modules
mock_openai_provider = types.ModuleType('gollm.llm.providers.openai')
mock_openai_provider.OpenAIClient = MockOpenAIClient
mock_openai_provider.OpenAILlmProvider = MockOpenAILlmProvider
sys.modules['gollm.llm.providers.openai'] = mock_openai_provider

# Mock the Ollama API client
class MockOllamaAPIClient:
    pass

# Create mock modules for Ollama provider
mock_ollama = types.ModuleType('gollm.llm.ollama')
mock_ollama.OllamaLLMProvider = type('OllamaLLMProvider', (), {})
mock_ollama.OllamaConfig = type('OllamaConfig', (), {})
mock_ollama.OllamaError = type('OllamaError', (Exception,), {})
sys.modules['gollm.llm.ollama'] = mock_ollama

# Mock the API module
mock_api = types.ModuleType('gollm.llm.ollama.api')
mock_api.OllamaAPIClient = MockOllamaAPIClient
sys.modules['gollm.llm.ollama.api'] = mock_api

# Now import the modules we want to test
with patch.dict('sys.modules', {
    'gollm.llm.providers.openai': mock_openai_provider,
    'gollm.llm.ollama': mock_ollama,
    'gollm.llm.ollama.api': mock_api,
}):
    from gollm.llm.ollama import OllamaConfig
    from gollm.llm.ollama.provider import OllamaLLMProvider
    from gollm.llm.ollama.api.client import OllamaAPIClient

# Test data
TEST_MODEL = "llama2"
TEST_BASE_URL = "http://test-ollama:11434"
TEST_CONFIG = {
    "model": TEST_MODEL,
    "base_url": TEST_BASE_URL,
    "timeout": 30,
    "max_retries": 3,
    "stream": True,
    "temperature": 0.7,
    "max_tokens": 100,
    "top_p": 1.0,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0,
    "stop": None,
    "n": 1,
    "logit_bias": None,
    "user": None
}

# Fixtures
@pytest.fixture
def mock_api_client():
    """Create a mock API client for testing."""
    mock = MagicMock(spec=OllamaAPIClient)
    mock.base_url = TEST_BASE_URL
    mock.timeout = 30
    mock.headers = {}
    mock.session = AsyncMock()
    
    # Mock the generate method
    mock.generate = AsyncMock(return_value={"text": "Generated text"})
    # Mock the stream method
    mock.stream = AsyncMock(return_value=[{"text": "Streamed "}])
    # Mock the health_check method
    mock.health_check = AsyncMock(return_value={"status": "ok"})
    
    return mock

@pytest.fixture
def ollama_provider(mock_api_client):
    """Create an Ollama provider instance with mocked dependencies."""
    with patch('gollm.llm.ollama.provider.OllamaAPIClient', return_value=mock_api_client):
        provider = OllamaLLMProvider(TEST_CONFIG)
        return provider

# Test cases
@pytest.mark.asyncio
async def test_generate_text(ollama_provider, mock_api_client):
    """Test generating text with the Ollama provider."""
    # Test data
    prompt = "Test prompt"
    expected_response = "Generated text"
    
    # Call the method
    response = await ollama_provider.generate(prompt)
    
    # Assertions
    assert response == expected_response
    mock_api_client.generate.assert_called_once_with(
        prompt=prompt,
        model=TEST_MODEL,
        stream=False,
        **{k: v for k, v in TEST_CONFIG.items() 
           if k not in ['model', 'base_url', 'timeout', 'max_retries']}
    )

@pytest.mark.asyncio
async def test_stream_text(ollama_provider, mock_api_client):
    """Test streaming text with the Ollama provider."""
    # Test data
    prompt = "Test streaming prompt"
    expected_chunks = ["Streamed "]
    
    # Call the method
    response = ollama_provider.generate(prompt, stream=True)
    
    # Assertions
    assert list(response) == expected_chunks
    mock_api_client.stream.assert_called_once_with(
        prompt=prompt,
        model=TEST_MODEL,
        **{k: v for k, v in TEST_CONFIG.items() 
           if k not in ['model', 'base_url', 'timeout', 'max_retries']}
    )

@pytest.mark.asyncio
async def test_health_check(ollama_provider, mock_api_client):
    """Test health check functionality."""
    # Call the method
    status = await ollama_provider.health_check()
    
    # Assertions
    assert status == {"status": "ok"}
    mock_api_client.health_check.assert_called_once()

def test_config_initialization():
    """Test that the OllamaConfig is properly initialized."""
    # Test data
    config_data = {
        "model": "llama2",
        "base_url": "http://test:11434",
        "timeout": 30,
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    # Create config
    config = OllamaConfig(**config_data)
    
    # Assertions
    assert config.model == "llama2"
    assert config.base_url == "http://test:11434"
    assert config.timeout == 30
    assert config.max_tokens == 100
    assert config.temperature == 0.7

@pytest.mark.asyncio
async def test_error_handling(ollama_provider, mock_api_client):
    """Test error handling in the Ollama provider."""
    # Setup mock to raise an exception
    mock_api_client.generate.side_effect = Exception("Test error")
    
    # Assert that the exception is properly propagated
    with pytest.raises(Exception, match="Test error"):
        await ollama_provider.generate("test")

@pytest.mark.asyncio
async def test_custom_parameters(ollama_provider, mock_api_client):
    """Test passing custom parameters to the Ollama provider."""
    # Test data
    prompt = "Test prompt"
    custom_params = {
        "temperature": 0.9,
        "max_tokens": 200,
        "custom_param": "value"
    }
    
    # Call the method with custom parameters
    await ollama_provider.generate(prompt, **custom_params)
    
    # Assert that custom parameters are passed through
    mock_api_client.generate.assert_called_once()
    call_kwargs = mock_api_client.generate.call_args[1]
    assert call_kwargs["temperature"] == 0.9
    assert call_kwargs["max_tokens"] == 200
    assert call_kwargs["custom_param"] == "value"
