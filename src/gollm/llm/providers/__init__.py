"""LLM Provider implementations for goLLM."""

from typing import Dict, Any, Optional, Type, Union
import importlib
import logging

from .base import BaseLLMProvider

logger = logging.getLogger('gollm.providers')

# Map of provider names to their module and class names
PROVIDER_REGISTRY = {
    'ollama': ('gollm.llm.providers.ollama', 'OllamaLLMProvider'),
    'openai': ('gollm.llm.providers.openai', 'OpenAILlmProvider'),
    'anthropic': ('gollm.llm.providers.anthropic', 'AnthropicLLMProvider'),
}

def get_provider_class(provider_name: str) -> Type[BaseLLMProvider]:
    """Get the provider class for the given provider name.
    
    Args:
        provider_name: Name of the provider (e.g., 'ollama', 'openai')
        
    Returns:
        The provider class
        
    Raises:
        ImportError: If the provider module cannot be imported
        AttributeError: If the provider class is not found in the module
    """
    if provider_name not in PROVIDER_REGISTRY:
        raise ValueError(f"Unknown provider: {provider_name}")
    
    module_name, class_name = PROVIDER_REGISTRY[provider_name]
    
    try:
        module = importlib.import_module(module_name)
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        logger.error(f"Failed to load provider {provider_name}: {str(e)}")
        raise

def create_provider(
    provider_name: str,
    config: Dict[str, Any],
    **kwargs
) -> BaseLLMProvider:
    """Create a new LLM provider instance.
    
    Args:
        provider_name: Name of the provider (e.g., 'ollama', 'openai')
        config: Provider configuration
        **kwargs: Additional arguments to pass to the provider constructor
        
    Returns:
        An instance of the requested provider
    """
    provider_class = get_provider_class(provider_name)
    return provider_class({**config, **kwargs})

__all__ = [
    'BaseLLMProvider',
    'get_provider_class',
    'create_provider',
]
