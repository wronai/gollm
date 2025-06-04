"""
Tests for the Ollama adapter implementation.

These tests verify the functionality of the Ollama adapter and its components,
including model management, text generation, and error handling.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientError, ClientResponseError, ClientSession

from gollm.llm.ollama import (
    OllamaAdapter,
    OllamaConfig,
    OllamaLLMProvider,
    ModelManager
)
from gollm.exceptions import (
    ModelNotFoundError,
    ModelOperationError,
    ConfigurationError,
    ValidationError
)

# Test data
TEST_MODEL = "test-model:latest"
TEST_PROMPT = "Hello, how are you?"
TEST_RESPONSE = {"response": "I'm doing well, thank you!", "done": True}
TEST_CHAT_MESSAGES = [
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hi there!"},
    {"role": "user", "content": "How are you?"}
]


@pytest.fixture
def mock_config():
    """Create a mock Ollama config for testing."""
    return OllamaConfig(
        base_url="http://test-ollama:11434",
        model=TEST_MODEL,
        timeout=30
    )


@pytest.fixture
async def mock_adapter(mock_config):
    """Create a mock Ollama adapter for testing."""
    async with OllamaAdapter(config=mock_config) as adapter:
        yield adapter


@pytest.fixture
def mock_session():
    """Create a mock aiohttp ClientSession."""
    with patch('aiohttp.ClientSession') as mock:
        yield mock


@pytest.mark.asyncio
async def test_adapter_initialization(mock_config):
    """Test that the adapter initializes correctly."""
    adapter = OllamaAdapter(config=mock_config)
    assert adapter.config == mock_config
    assert not adapter._initialized
    
    # Test context manager
    async with adapter:
        assert adapter._initialized
        assert adapter.api_client is not None
    
    # Adapter should be closed after context
    assert not adapter._initialized


@pytest.mark.asyncio
async def test_adapter_generate(mock_adapter):
    """Test text generation with the adapter."""
    # Mock the API client
    mock_adapter.api_client.generate = AsyncMock(return_value=TEST_RESPONSE)
    
    # Test generation
    result = await mock_adapter.generate(
        prompt=TEST_PROMPT,
        model=TEST_MODEL
    )
    
    # Verify the result
    assert result == TEST_RESPONSE
    mock_adapter.api_client.generate.assert_awaited_once()
    
    # Verify parameters
    args, kwargs = mock_adapter.api_client.generate.await_args
    assert kwargs['prompt'] == TEST_PROMPT
    assert kwargs['model'] == TEST_MODEL


@pytest.mark.asyncio
async def test_adapter_chat(mock_adapter):
    """Test chat completion with the adapter."""
    # Mock the API client
    mock_response = {"message": {"role": "assistant", "content": "I'm doing well!"}}
    mock_adapter.api_client.chat = AsyncMock(return_value=mock_response)
    
    # Test chat
    result = await mock_adapter.chat(
        messages=TEST_CHAT_MESSAGES,
        model=TEST_MODEL
    )
    
    # Verify the result
    assert result == mock_response
    mock_adapter.api_client.chat.assert_awaited_once()
    
    # Verify parameters
    args, kwargs = mock_adapter.api_client.chat.await_args
    assert kwargs['messages'] == TEST_CHAT_MESSAGES
    assert kwargs['model'] == TEST_MODEL


@pytest.mark.asyncio
async def test_adapter_stream_generate(mock_adapter):
    """Test streaming text generation with the adapter."""
    # Create a mock async generator
    async def mock_stream():
        yield {"response": "Hello", "done": False}
        yield {"response": " there!", "done": True}
    
    # Mock the API client
    mock_adapter.api_client.generate = AsyncMock(return_value=mock_stream())
    
    # Test streaming generation
    chunks = []
    async for chunk in mock_adapter.stream_generate(
        prompt=TEST_PROMPT,
        model=TEST_MODEL
    ):
        chunks.append(chunk)
    
    # Verify the results
    assert len(chunks) == 2
    assert chunks[0]["response"] == "Hello"
    assert chunks[1]["response"] == " there!"
    
    # Verify parameters
    args, kwargs = mock_adapter.api_client.generate.await_args
    assert kwargs['prompt'] == TEST_PROMPT
    assert kwargs['model'] == TEST_MODEL
    assert kwargs['stream'] is True


@pytest.mark.asyncio
async def test_adapter_health_check(mock_adapter):
    """Test health check functionality."""
    # Mock the API client
    mock_adapter.api_client.get_models = AsyncMock(return_value={"models": [{"name": TEST_MODEL}]})
    mock_adapter.model_manager.get_model_info = AsyncMock(return_value={"name": TEST_MODEL})
    
    # Test health check
    health = await mock_adapter.health_check()
    
    # Verify the result
    assert health["status"] == "healthy"
    assert health["service_available"] is True
    assert health["model_available"] is True
    assert health["config"]["model"] == TEST_MODEL


@pytest.mark.asyncio
async def test_provider_initialization(mock_config):
    """Test that the provider initializes correctly."""
    provider = OllamaLLMProvider(config=mock_config.to_dict())
    assert not provider.is_initialized
    
    # Mock the adapter
    mock_adapter = AsyncMock()
    with patch('gollm.llm.ollama.provider.OllamaAdapter', return_value=mock_adapter):
        await provider.initialize()
        assert provider.is_initialized
        
        # Test context manager
        async with provider as p:
            assert p == provider
            assert p.is_initialized
    
    # Provider should be closed after context
    assert not provider.is_initialized


@pytest.mark.asyncio
async def test_provider_generate(mock_config):
    """Test text generation with the provider."""
    provider = OllamaLLMProvider(config=mock_config.to_dict())
    
    # Mock the adapter
    mock_adapter = AsyncMock()
    mock_adapter.generate = AsyncMock(return_value=TEST_RESPONSE)
    provider._adapter = mock_adapter
    provider._initialized = True
    
    # Test generation
    result = await provider.generate(
        prompt=TEST_PROMPT,
        model=TEST_MODEL
    )
    
    # Verify the result
    assert result == TEST_RESPONSE
    mock_adapter.generate.assert_awaited_once()
    
    # Verify parameters
    args, kwargs = mock_adapter.generate.await_args
    assert kwargs['prompt'] == TEST_PROMPT
    assert kwargs['model'] == TEST_MODEL


@pytest.mark.asyncio
async def test_provider_health_check():
    """Test health check with the provider."""
    provider = OllamaLLMProvider()
    
    # Mock the adapter
    mock_adapter = AsyncMock()
    mock_adapter.health_check = AsyncMock(return_value={"status": "healthy"})
    provider._adapter = mock_adapter
    provider._initialized = True
    
    # Test health check
    health = await provider.health_check()
    assert health["status"] == "healthy"
    mock_adapter.health_check.assert_awaited_once()


@pytest.mark.asyncio
async def test_model_manager():
    """Test the model manager functionality."""
    # Create a mock API client
    mock_client = AsyncMock()
    
    # Set up mock responses
    mock_client.get_models = AsyncMock(return_value={
        "models": [{"name": TEST_MODEL, "size": 1000}]
    })
    
    # Initialize the model manager
    manager = ModelManager(mock_client)
    
    # Test listing models
    models = await manager.list_models(refresh=True)
    assert TEST_MODEL in models
    mock_client.get_models.assert_awaited_once()
    
    # Test model exists
    exists = await manager.model_exists(TEST_MODEL)
    assert exists is True
    
    # Test getting model info
    model_info = await manager.get_model_info(TEST_MODEL)
    assert model_info["name"] == TEST_MODEL
    
    # Test pulling a model
    await manager.pull_model(TEST_MODEL)
    mock_client.pull_model.assert_awaited_once_with(TEST_MODEL)
    
    # Test deleting a model
    await manager.delete_model(TEST_MODEL)
    mock_client.delete_model.assert_awaited_once_with(TEST_MODEL)


@pytest.mark.asyncio
async def test_config_validation():
    """Test configuration validation."""
    # Test valid config
    config = OllamaConfig(
        base_url="http://test:11434",
        model=TEST_MODEL,
        timeout=30
    )
    assert config.model == TEST_MODEL
    
    # Test from_dict
    config_dict = config.to_dict()
    config2 = OllamaConfig.from_dict(config_dict)
    assert config2.model == TEST_MODEL
    
    # Test invalid config
    with pytest.raises(ValidationError):
        OllamaConfig(base_url="not-a-url")
    
    with pytest.raises(ValidationError):
        OllamaConfig(model="")


@pytest.mark.asyncio
async def test_error_handling(mock_adapter):
    """Test error handling in the adapter."""
    # Test connection error
    mock_adapter.api_client.get_models = AsyncMock(side_effect=ClientError("Connection error"))
    with pytest.raises(ConnectionError):
        await mock_adapter.initialize()
    
    # Test model not found
    mock_adapter.model_manager.ensure_model = AsyncMock(return_value=False)
    with pytest.raises(ModelNotFoundError):
        await mock_adapter.generate(prompt=TEST_PROMPT, model="nonexistent-model")
    
    # Test generation error
    mock_adapter.api_client.generate = AsyncMock(side_effect=Exception("Generation failed"))
    with pytest.raises(ModelOperationError):
        await mock_adapter.generate(prompt=TEST_PROMPT)
