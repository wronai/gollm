"""Minimal test file to verify Ollama imports without external dependencies."""
import sys
from unittest.mock import MagicMock

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

# Mock the Ollama client
class MockOllamaHttpClient:
    pass

# Create a mock for the ollama provider module
mock_ollama_provider = type('module', (), {
    'OllamaHttpClient': MockOllamaHttpClient,
    'OllamaLLMProvider': type('OllamaLLMProvider', (), {})
})
sys.modules['gollm.llm.providers.ollama'] = mock_ollama_provider

# Now import the modules we want to test
from gollm.llm.providers.ollama import OllamaLLMProvider

def test_ollama_imports():
    """Test that we can import the required Ollama modules."""
    assert OllamaLLMProvider is not None
    print("OllamaLLMProvider imported successfully!")

if __name__ == "__main__":
    test_ollama_imports()
    print("All Ollama imports successful!")
