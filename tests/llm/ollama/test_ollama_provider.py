"""Comprehensive tests for the Ollama LLM Provider."""
import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from typing import Dict, Any, Optional, Type, Union, AsyncGenerator, List

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.insert(0, project_root)

# Create mock modules
mock_openai = MagicMock()
sys.modules['openai'] = mock_openai

# Create a mock for the OllamaAdapter first
class MockOllamaAdapter:
    """Mock implementation of OllamaAdapter for testing."""
    
    # Class attributes required by BaseLLMAdapter
    provider = "ollama"
    config_class = None  # Will be set after MockConfig is defined
    
    @property
    def name(self) -> str:
        """Get the name of the provider."""
        return self.provider
    
    @property
    def is_initialized(self) -> bool:
        """Check if the provider is initialized."""
        return getattr(self, '_initialized', False)
    
    @classmethod
    def get_default_config(cls) -> 'MockConfig':
        """Get the default configuration for this adapter."""
        return cls.config_class()
    
    @classmethod
    def get_provider(cls, config: Optional[Dict[str, Any]] = None) -> 'MockOllamaAdapter':
        """Get a provider instance with the given config."""
        return cls(config=config)
    
    @property
    def config_class(self) -> Type['MockConfig']:
        """Get the configuration class for this adapter."""
        return MockConfig
    
    def __init__(self, config: Optional[Union[Dict[str, Any], 'MockConfig']] = None):
        """Initialize the mock adapter."""
        if config is None:
            config = self.get_default_config()
        elif isinstance(config, dict):
            config = self.config_class.from_dict(config)
            
        self.config = config
        self._initialized = False
        
        # Mock required methods
        self.generate = AsyncMock(return_value={"text": "Generated text"})
        self.chat = AsyncMock(return_value={"response": "Chat response"})
        self.stream_generate = AsyncMock()
        self.health_check = AsyncMock(return_value={"status": "ok"})
        self.list_models = AsyncMock(return_value=["llama2", "mistral"])
        self.is_available = AsyncMock(return_value=True)
        self.close = AsyncMock()
        
        # Setup default stream response
        async def mock_stream():
            yield {"text": "Streamed "}
        
        self.stream_generate.return_value = mock_stream()
    
    async def initialize(self) -> None:
        """Initialize the provider."""
        self._initialized = True
    
    async def close(self) -> None:
        """Close the provider and release resources."""
        self._initialized = False

# Now patch the OllamaAdapter before importing the provider
with patch.dict('sys.modules', {
    'openai': mock_openai,
}), patch('gollm.llm.ollama.provider.OllamaAdapter', MockOllamaAdapter):
    from gollm.llm.ollama import OllamaConfig, OllamaLLMProvider

# Create a mock config class for testing
class MockConfig:
    def __init__(self, **kwargs):
        self.base_url = "http://localhost:11434"
        self.model = "llama2"
        self.timeout = 60
        self.max_tokens = 100
        self.temperature = 0.7
        self.top_p = 1.0
        self.frequency_penalty = 0.0
        self.presence_penalty = 0.0
        self.stop = None
        self.n = 1
        self.logit_bias = None
        self.user = None
        self.additional_params = {}
        self.__dict__.update(kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary."""
        return {k: v for k, v in self.__dict__.items() 
                if not k.startswith('_') and v is not None}
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'MockConfig':
        """Create a configuration from a dictionary."""
        return cls(**config_dict)

# Set the config_class for MockOllamaAdapter
MockOllamaAdapter.config_class = MockConfig

# Create a mock for the OllamaAdapter
class MockOllamaAdapter:
    """Mock implementation of OllamaAdapter for testing."""
    
    # Class attributes required by BaseLLMAdapter
    provider = "ollama"
    config_class = MockConfig
    
    @property
    def name(self) -> str:
        """Get the name of the provider."""
        return self.provider
    
    @property
    def is_initialized(self) -> bool:
        """Check if the provider is initialized."""
        return getattr(self, '_initialized', False)
    
    @classmethod
    def get_default_config(cls) -> MockConfig:
        """Get the default configuration for this adapter."""
        return cls.config_class()
    
    @classmethod
    def get_provider(cls, config: Optional[Dict[str, Any]] = None) -> 'MockOllamaAdapter':
        """Get a provider instance with the given config."""
        return cls(config=config)
    
    @property
    def config_class(self) -> Type[MockConfig]:
        """Get the configuration class for this adapter."""
        return MockConfig
    
    def __init__(self, config: Optional[Union[Dict[str, Any], MockConfig]] = None):
        """Initialize the mock adapter."""
        if config is None:
            config = self.get_default_config()
        elif isinstance(config, dict):
            config = self.config_class.from_dict(config)
            
        self.config = config
        self._initialized = False
        
        # Mock required methods
        self.generate = AsyncMock(return_value={"text": "Generated text"})
        self.chat = AsyncMock(return_value={"response": "Chat response"})
        self.stream_generate = AsyncMock()
        self.health_check = AsyncMock(return_value={"status": "ok"})
        self.list_models = AsyncMock(return_value=["llama2", "mistral"])
        self.is_available = AsyncMock(return_value=True)
        self.close = AsyncMock()
        
        # Setup default stream response
        async def mock_stream():
            yield {"text": "Streamed "}
        
        self.stream_generate.return_value = mock_stream()
    
    async def initialize(self) -> None:
        """Initialize the provider."""
        self._initialized = True
    
    async def close(self) -> None:
        """Close the provider and release resources."""
        self._initialized = False
    
    # Implement abstract methods from BaseLLMAdapter
    @property
    def provider(self) -> str:
        """Get the provider name."""
        return self.__class__.provider
    
    def get_provider_instance(self, config: Optional[Dict[str, Any]] = None) -> 'MockOllamaAdapter':
        """Get a provider instance with the given config."""
        return self.__class__(config=config)

# Patch the OllamaAdapter in the provider module
patch('gollm.llm.ollama.provider.OllamaAdapter', MockOllamaAdapter).start()

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
def mock_ollama_adapter():
    """Create a mock Ollama adapter for testing."""
    mock = MockOllamaAdapter()
    return mock

@pytest.fixture
async def ollama_provider():
    """Create and initialize an Ollama provider instance with mocked dependencies."""
    provider = OllamaLLMProvider(TEST_CONFIG)
    # The provider should already be using the mocked adapter
    await provider.initialize()
    return provider

# Test cases
@pytest.mark.asyncio
async def test_generate_text(ollama_provider):
    """Test generating text with the Ollama provider."""
    prompt = "Test prompt"
    result = await ollama_provider.generate(prompt)
    
    # Check that the adapter's generate method was called with the correct parameters
    ollama_provider._adapter.generate.assert_awaited_once_with(
        prompt=prompt,
        model=TEST_MODEL,
        temperature=0.7,
        max_tokens=100,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        stop=None,
        n=1,
        logit_bias=None,
        user=None
    )
    
    # Check that the result is as expected
    assert result == "Generated text"

@pytest.mark.asyncio
async def test_generate_stream(ollama_provider):
    """Test streaming text with the Ollama provider."""
    # Setup the mock to return an async generator
    async def mock_generator():
        yield "Streamed "
    
    ollama_provider._adapter.generate_stream.return_value = mock_generator()
    
    prompt = "Test prompt"
    stream = await ollama_provider.generate(prompt, stream=True)
    
    # Collect all chunks from the async generator
    chunks = []
    async for chunk in stream:
        chunks.append(chunk)
    
    # Check that the adapter's generate_stream method was called with the correct parameters
    ollama_provider._adapter.generate_stream.assert_awaited_once_with(
        prompt=prompt,
        model=TEST_MODEL,
        temperature=0.7,
        max_tokens=100,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        stop=None,
        n=1,
        logit_bias=None,
        user=None
    )
    
    # Check that the chunks are as expected
    assert chunks == ["Streamed "]

@pytest.mark.asyncio
async def test_health_check(ollama_provider):
    """Test health check with the Ollama provider."""
    result = await ollama_provider.health_check()
    
    # Check that the health check was called
    ollama_provider._adapter.health_check.assert_awaited_once()
    
    # Check that the result is as expected
    assert result == {"status": "ok"}

@pytest.mark.asyncio
async def test_error_handling(ollama_provider):
    """Test error handling with the Ollama provider."""
    # Set up the mock to raise an exception
    error_message = "Test error"
    ollama_provider._adapter.generate.side_effect = Exception(error_message)
    
    # Test that the exception is propagated
    with pytest.raises(Exception) as exc_info:
        await ollama_provider.generate("Test prompt")
    
    assert str(exc_info.value) == error_message

@pytest.mark.asyncio
async def test_custom_parameters(ollama_provider):
    """Test custom parameters with the Ollama provider."""
    custom_params = {
        "temperature": 0.9,
        "max_tokens": 200,
        "top_p": 0.9,
        "frequency_penalty": 0.5,
        "presence_penalty": 0.5,
        "stop": ["\n"],
        "n": 2,
        "logit_bias": {"50256": -100},
        "user": "test-user"
    }
    
    # Test with custom parameters
    await ollama_provider.generate("Test prompt", **custom_params)
    
    # Check that the adapter's generate method was called with the custom parameters
    ollama_provider._adapter.generate.assert_awaited_once()
    call_kwargs = ollama_provider._adapter.generate.await_args[1]
    
    # Check that the custom parameters were passed through
    for key, value in custom_params.items():
        assert call_kwargs[key] == value, f"Parameter {key} was not set correctly"
    
    # Verify the prompt was passed correctly
    assert call_kwargs["prompt"] == "Test prompt"

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
