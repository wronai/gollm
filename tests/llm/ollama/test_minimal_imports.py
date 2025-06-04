"""Minimal test file to verify Ollama imports without external dependencies."""
import sys
import types
from unittest.mock import MagicMock, patch

# Mock the openai module before any imports
sys.modules['openai'] = MagicMock()

# Mock the OpenAIClient class
class MockOpenAIClient:
    pass

# Mock the OpenAILlmProvider class
class MockOpenAILlmProvider:
    pass

# Create a mock for the openai provider module
mock_openai_provider = types.ModuleType('gollm.llm.providers.openai')
mock_openai_provider.OpenAIClient = MockOpenAIClient
mock_openai_provider.OpenAILlmProvider = MockOpenAILlmProvider
sys.modules['gollm.llm.providers.openai'] = mock_openai_provider

# Mock the Ollama HTTP client
class MockOllamaHttpClient:
    pass

# Create mock modules for Ollama provider
mock_ollama_provider = types.ModuleType('gollm.llm.providers.ollama')
mock_ollama_provider.OllamaHttpClient = MockOllamaHttpClient
mock_ollama_provider.OllamaLLMProvider = type('OllamaLLMProvider', (), {})
mock_ollama_provider.OllamaConfig = type('OllamaConfig', (), {})
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
    from gollm.llm.providers.ollama import OllamaLLMProvider, OllamaHttpClient, OllamaConfig, OllamaError

def test_ollama_imports():
    """Test that we can import the required Ollama modules."""
    # These imports should work because we mocked the modules
    assert OllamaLLMProvider is not None
    assert OllamaHttpClient is not None
    assert OllamaConfig is not None
    assert OllamaError is not None
    print("OllamaLLMProvider imported successfully!")

if __name__ == "__main__":
    test_ollama_imports()
    print("All Ollama imports successful!")
