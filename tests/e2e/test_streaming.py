"""End-to-end tests for streaming functionality with the Ollama modular adapter."""

import asyncio
import os
import pytest
from typing import Dict, Any

from gollm.main import GollmCore
from gollm.llm.providers.ollama.provider import OllamaLLMProvider
from gollm.llm.providers.ollama.factory import AdapterType


@pytest.mark.asyncio
async def test_streaming_generation():
    """Test that streaming generation works with the modular adapter."""
    # Set environment variables to ensure modular adapter is used
    os.environ["OLLAMA_ADAPTER_TYPE"] = "modular"
    os.environ["GOLLM_USE_STREAMING"] = "true"
    
    # Initialize GollmCore
    gollm = GollmCore()
    
    # Create a simple request
    request = "Write a function to calculate factorial in Python"
    context = {
        'adapter_type': 'modular',
        'use_streaming': True,
        'max_iterations': 1,  # Use just one iteration for testing
    }
    
    # Generate code with streaming
    result = await gollm.handle_code_generation(
        request, 
        context=context,
        use_streaming=True
    )
    
    # Check that we got a valid response
    assert result is not None
    assert 'generated_code' in result
    assert len(result['generated_code']) > 0
    
    # Check that the code contains a factorial function
    assert 'def factorial' in result['generated_code']
    

@pytest.mark.asyncio
async def test_provider_streaming_method():
    """Test the streaming method in OllamaLLMProvider directly."""
    # Set environment variables
    os.environ["OLLAMA_ADAPTER_TYPE"] = "modular"
    
    # Create provider config
    config = {
        'base_url': 'http://localhost:11434',
        'model': 'mistral:latest',
        'adapter_type': 'modular',
        'timeout': 60
    }
    
    # Create provider
    provider = OllamaLLMProvider(config)
    
    # Test with async context manager
    async with provider:
        # Check that the adapter is modular
        assert provider.adapter_type == 'modular'
        
        # Simple prompt
        prompt = "Write a Python function to calculate the factorial of a number."
        
        # Test streaming generation
        full_text = ""
        async for chunk, metadata in provider.generate_response_stream(prompt):
            assert isinstance(chunk, str)
            assert isinstance(metadata, dict)
            full_text += chunk
        
        # Check that we got a valid response
        assert len(full_text) > 0
        assert 'def factorial' in full_text


@pytest.mark.asyncio
async def test_fallback_to_non_streaming():
    """Test that the provider falls back to non-streaming if streaming fails."""
    # Set environment variables
    os.environ["OLLAMA_ADAPTER_TYPE"] = "http"  # Use HTTP adapter which doesn't support streaming
    
    # Create provider config
    config = {
        'base_url': 'http://localhost:11434',
        'model': 'mistral:latest',
        'adapter_type': 'http',
        'timeout': 60
    }
    
    # Create provider
    provider = OllamaLLMProvider(config)
    
    # Test with async context manager
    async with provider:
        # Check that the adapter is HTTP
        assert provider.adapter_type == 'http'
        
        # Simple prompt
        prompt = "Write a Python function to calculate the factorial of a number."
        
        # Test response generation (should use non-streaming)
        response = await provider.generate_response(prompt)
        
        # Check that we got a valid response
        assert response is not None
        assert 'generated_code' in response
        assert len(response['generated_code']) > 0
