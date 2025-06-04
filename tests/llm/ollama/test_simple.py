"""Simple test file to verify imports."""
import pytest

def test_imports():
    """Test that we can import the required modules."""
    from gollm.llm.ollama import OllamaConfig, OllamaAdapter, OllamaLLMProvider
    assert OllamaConfig is not None
    assert OllamaAdapter is not None
    assert OllamaLLMProvider is not None
