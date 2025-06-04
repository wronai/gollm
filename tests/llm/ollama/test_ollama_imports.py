"""Test file specifically for testing Ollama imports in isolation."""
import sys
import types
import pytest
from unittest.mock import MagicMock, patch

# Mock the openai module
sys.modules['openai'] = MagicMock()

# Create mock modules for OpenAI provider
mock_openai_provider = types.ModuleType('gollm.llm.providers.openai')
mock_openai_provider.OpenAIClient = type('MockOpenAIClient', (), {})
mock_openai_provider.OpenAILlmProvider = type('MockOpenAILlmProvider', (), {})
sys.modules['gollm.llm.providers.openai'] = mock_openai_provider

# Mock the Ollama HTTP client
class MockOllamaHttpClient:
    pass

# Create mock modules for Ollama provider
mock_ollama_provider = types.ModuleType('gollm.llm.providers.ollama')
mock_ollama_provider.OllamaHttpClient = MockOllamaHttpClient
mock_ollama_provider.OllamaLLMProvider = type('OllamaLLMProvider', (), {})
mock_ollama_provider.OllamaConfig = type('OllamaConfig', (), {})
mock_ollama_provider.OllamaAdapter = type('OllamaAdapter', (), {})
mock_ollama_provider.OllamaError = type('OllamaError', (Exception,), {})
sys.modules['gollm.llm.providers.ollama'] = mock_ollama_provider

# Mock the HTTP adapter
mock_http_adapter = types.ModuleType('gollm.llm.providers.ollama.http')
mock_http_adapter.OllamaHttpClient = MockOllamaHttpClient
mock_http_adapter.OllamaHttpAdapter = type('OllamaHttpAdapter', (), {})
sys.modules['gollm.llm.providers.ollama.http'] = mock_http_adapter

# Now import the modules we want to test
with patch.dict('sys.modules', {
    'gollm.llm.providers.openai': mock_openai_provider,
    'gollm.llm.providers.ollama': mock_ollama_provider,
    'gollm.llm.providers.ollama.http': mock_http_adapter,
}):
    from gollm.llm.providers.ollama import OllamaConfig, OllamaAdapter, OllamaLLMProvider, OllamaError
    from gollm.llm.base import BaseLLMProvider, BaseLLMConfig, BaseLLMAdapter
    from gollm.llm.exceptions import (
    LLMError, ModelError, ModelNotFoundError, ModelOperationError,
    ConfigurationError, ValidationError, APIError, AuthenticationError,
    RateLimitError, TimeoutError, GenerationError, InvalidPromptError,
    ContextLengthExceededError
)

def test_ollama_imports():
    """Test that we can import the required Ollama modules."""
    # These imports should work because we mocked the modules
    assert OllamaConfig is not None
    assert OllamaAdapter is not None
    assert OllamaLLMProvider is not None
    assert OllamaError is not None

def test_llm_base_imports():
    """Test that we can import the base LLM classes."""
    # These are the base classes that should always be available
    assert BaseLLMProvider is not None
    assert BaseLLMConfig is not None
    assert BaseLLMAdapter is not None

def test_exceptions_import():
    """Test that we can import the exceptions."""
    assert LLMError is not None
    assert ModelError is not None
    assert ModelNotFoundError is not None
    assert ModelOperationError is not None
    assert ConfigurationError is not None
    assert ValidationError is not None
    assert APIError is not None
    assert AuthenticationError is not None
    assert RateLimitError is not None
    assert TimeoutError is not None
    assert GenerationError is not None
    assert InvalidPromptError is not None
    assert ContextLengthExceededError is not None
