"""Generation operations for Ollama provider."""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Union, AsyncIterator

from .config import OllamaConfig
from .prompt import format_prompt_for_ollama, format_chat_messages, extract_response_content

logger = logging.getLogger('gollm.ollama.generation')


async def generate_completion(
    adapter,
    prompt: str,
    model: str,
    context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """Generate a completion using the Ollama API.
    
    Args:
        adapter: The Ollama adapter to use
        prompt: The prompt to generate from
        model: Model to use for generation
        context: Additional context for prompt formatting
        **kwargs: Additional generation parameters
            - temperature: Controls randomness (0.0 to 1.0)
            - max_tokens/num_predict: Maximum tokens to generate
            - top_p: Nucleus sampling parameter (0.0 to 1.0)
            - top_k: Limit next token selection to top K (1-100)
            - repeat_penalty: Penalty for repeated tokens (1.0+)
            - stop: List of strings to stop generation
            - stream: Whether to stream the response
            
    Returns:
        Dictionary containing the generated text and metadata
    """
    # Format the prompt with context
    formatted_prompt = format_prompt_for_ollama(prompt, context)
    
    # Track timing
    start_time = time.time()
    
    try:
        # Call the adapter's generate method
        result = await adapter.generate(
            prompt=formatted_prompt,
            model=model,
            **kwargs
        )
        
        # Add timing information
        end_time = time.time()
        result['client_duration'] = end_time - start_time
        
        # Add success status if not present
        if 'success' not in result:
            result['success'] = True
        
        return result
    
    except Exception as e:
        logger.error(f"Error generating completion: {e}")
        end_time = time.time()
        
        return {
            'success': False,
            'error': str(e),
            'client_duration': end_time - start_time
        }


async def generate_chat_completion(
    adapter,
    messages: List[Dict[str, str]],
    model: str,
    **kwargs
) -> Dict[str, Any]:
    """Generate a chat completion using the Ollama API.
    
    Args:
        adapter: The Ollama adapter to use
        messages: List of message dictionaries with 'role' and 'content' keys
        model: Model to use for generation
        **kwargs: Additional generation parameters
            - temperature: Controls randomness (0.0 to 1.0)
            - max_tokens/num_predict: Maximum tokens to generate
            - top_p: Nucleus sampling parameter (0.0 to 1.0)
            - top_k: Limit next token selection to top K (1-100)
            - repeat_penalty: Penalty for repeated tokens (1.0+)
            - stop: List of strings to stop generation
            - stream: Whether to stream the response
            
    Returns:
        Dictionary containing the generated response and metadata
    """
    # Track timing
    start_time = time.time()
    
    try:
        # Call the adapter's chat method
        result = await adapter.chat(
            messages=messages,
            model=model,
            **kwargs
        )
        
        # Add timing information
        end_time = time.time()
        result['client_duration'] = end_time - start_time
        
        # Add success status if not present
        if 'success' not in result:
            result['success'] = True
        
        return result
    
    except Exception as e:
        logger.error(f"Error generating chat completion: {e}")
        end_time = time.time()
        
        return {
            'success': False,
            'error': str(e),
            'client_duration': end_time - start_time
        }


async def generate_response(
    adapter,
    prompt: str,
    model: str,
    context: Optional[Dict[str, Any]] = None,
    api_type: str = "chat",
    **kwargs
) -> Dict[str, Any]:
    """Generate a response using either chat or completion API based on api_type.
    
    Args:
        adapter: The Ollama adapter to use
        prompt: The prompt to generate from
        model: Model to use for generation
        context: Additional context for prompt formatting
        api_type: API type to use ("chat" or "completion")
        **kwargs: Additional generation parameters
            
    Returns:
        Dictionary containing the generated response and metadata
    """
    # Normalize api_type
    api_type = api_type.lower()
    
    if api_type == "chat":
        # Format messages for chat API
        messages = format_chat_messages(prompt, context)
        return await generate_chat_completion(adapter, messages, model, **kwargs)
    else:
        # Use completion API
        return await generate_completion(adapter, prompt, model, context, **kwargs)


async def stream_completion(
    adapter,
    prompt: str,
    model: str,
    context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> AsyncIterator[Dict[str, Any]]:
    """Stream a completion using the Ollama API.
    
    Args:
        adapter: The Ollama adapter to use
        prompt: The prompt to generate from
        model: Model to use for generation
        context: Additional context for prompt formatting
        **kwargs: Additional generation parameters
            
    Yields:
        Dictionary containing chunks of generated text and metadata
    """
    # Format the prompt with context
    formatted_prompt = format_prompt_for_ollama(prompt, context)
    
    # Ensure streaming is enabled
    kwargs['stream'] = True
    
    try:
        # Call the adapter's generate method with streaming
        async for chunk in adapter.generate_stream(
            prompt=formatted_prompt,
            model=model,
            **kwargs
        ):
            yield chunk
    
    except Exception as e:
        logger.error(f"Error streaming completion: {e}")
        yield {
            'success': False,
            'error': str(e),
            'done': True
        }


async def stream_chat_completion(
    adapter,
    messages: List[Dict[str, str]],
    model: str,
    **kwargs
) -> AsyncIterator[Dict[str, Any]]:
    """Stream a chat completion using the Ollama API.
    
    Args:
        adapter: The Ollama adapter to use
        messages: List of message dictionaries with 'role' and 'content' keys
        model: Model to use for generation
        **kwargs: Additional generation parameters
            
    Yields:
        Dictionary containing chunks of generated response and metadata
    """
    # Ensure streaming is enabled
    kwargs['stream'] = True
    
    try:
        # Call the adapter's chat method with streaming
        async for chunk in adapter.chat_stream(
            messages=messages,
            model=model,
            **kwargs
        ):
            yield chunk
    
    except Exception as e:
        logger.error(f"Error streaming chat completion: {e}")
        yield {
            'success': False,
            'error': str(e),
            'done': True
        }


async def stream_response(
    adapter,
    prompt: str,
    model: str,
    context: Optional[Dict[str, Any]] = None,
    api_type: str = "chat",
    **kwargs
) -> AsyncIterator[Dict[str, Any]]:
    """Stream a response using either chat or completion API based on api_type.
    
    Args:
        adapter: The Ollama adapter to use
        prompt: The prompt to generate from
        model: Model to use for generation
        context: Additional context for prompt formatting
        api_type: API type to use ("chat" or "completion")
        **kwargs: Additional generation parameters
            
    Yields:
        Dictionary containing chunks of generated response and metadata
    """
    # Normalize api_type
    api_type = api_type.lower()
    
    if api_type == "chat":
        # Format messages for chat API
        messages = format_chat_messages(prompt, context)
        async for chunk in stream_chat_completion(adapter, messages, model, **kwargs):
            yield chunk
    else:
        # Use completion API
        async for chunk in stream_completion(adapter, prompt, model, context, **kwargs):
            yield chunk
