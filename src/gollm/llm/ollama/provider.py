"""
Ollama LLM Provider for GoLLM.

This module implements the LLM provider interface for Ollama, allowing it to be used
as a drop-in replacement for other LLM providers in the GoLLM system.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union, AsyncGenerator

from ..base import BaseLLMProvider
from .adapter import OllamaAdapter
from .config import OllamaConfig
from ...exceptions import (
    ModelNotFoundError,
    ModelOperationError,
    ConfigurationError,
    ValidationError
)
from .utils.validation import validate_model

logger = logging.getLogger("gollm.ollama.provider")


class OllamaLLMProvider(BaseLLMProvider):
    """LLM Provider implementation for Ollama."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Ollama LLM provider.
        
        Args:
            config: Configuration dictionary for the provider
        """
        self.config = OllamaConfig.from_dict(config or {})
        self._adapter: Optional[OllamaAdapter] = None
        self._initialized = False
    
    @property
    def name(self) -> str:
        """Get the name of the provider."""
        return "ollama"
    
    @property
    def is_initialized(self) -> bool:
        """Check if the provider is initialized."""
        return self._initialized and self._adapter is not None
    
    async def initialize(self) -> None:
        """Initialize the provider."""
        if self._initialized:
            return
            
        logger.info("Initializing Ollama LLM provider")
        
        try:
            # Initialize the adapter
            self._adapter = OllamaAdapter(self.config)
            await self._adapter.initialize()
            
            self._initialized = True
            logger.info(
                "Ollama LLM provider initialized with model: %s", 
                self.config.model
            )
            
        except Exception as e:
            logger.error("Failed to initialize Ollama LLM provider: %s", str(e))
            self._initialized = False
            raise
    
    async def close(self) -> None:
        """Close the provider and release resources."""
        if self._adapter:
            await self._adapter.close()
            self._adapter = None
            
        self._initialized = False
        logger.info("Ollama LLM provider closed")
    
    async def is_available(self) -> bool:
        """Check if the provider is available.
        
        Returns:
            bool: True if the provider is available, False otherwise
        """
        if not self._adapter:
            return False
            
        return await self._adapter.is_available()
    
    async def list_models(self) -> List[str]:
        """List available models.
        
        Returns:
            List of available model names
            
        Raises:
            ModelOperationError: If there's an error listing models
        """
        if not self.is_initialized:
            await self.initialize()
            
        return await self._adapter.list_models()
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text using the specified model.
        
        Args:
            prompt: The prompt to generate text from
            model: Name of the model to use (defaults to config.model)
            **kwargs: Additional generation parameters
            
        Returns:
            Dictionary containing the generated text and metadata
            
        Raises:
            ModelNotFoundError: If the specified model is not available
            ModelOperationError: If there's an error during generation
        """
        if not self.is_initialized:
            await self.initialize()
            
        # Use configured model if none specified
        model = model or self.config.model
        validate_model(model)
        
        # Map provider-agnostic parameters to Ollama parameters if needed
        params = self._map_generation_params(kwargs)
        
        return await self._adapter.generate(
            prompt=prompt,
            model=model,
            **params
        )
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a chat completion.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Name of the model to use (defaults to config.model)
            **kwargs: Additional generation parameters
            
        Returns:
            Dictionary containing the generated response and metadata
            
        Raises:
            ModelNotFoundError: If the specified model is not available
            ModelOperationError: If there's an error during generation
        """
        if not self.is_initialized:
            await self.initialize()
            
        # Use configured model if none specified
        model = model or self.config.model
        validate_model(model)
        
        # Map provider-agnostic parameters to Ollama parameters if needed
        params = self._map_generation_params(kwargs)
        
        return await self._adapter.chat(
            messages=messages,
            model=model,
            **params
        )
    
    async def stream_generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream generated text chunks from the model.
        
        Args:
            prompt: The prompt to generate text from
            model: Name of the model to use (defaults to config.model)
            **kwargs: Additional generation parameters
            
        Yields:
            Dictionary containing chunks of generated text and metadata
            
        Raises:
            ModelNotFoundError: If the specified model is not available
            ModelOperationError: If there's an error during generation
        """
        if not self.is_initialized:
            await self.initialize()
            
        # Use configured model if none specified
        model = model or self.config.model
        validate_model(model)
        
        # Map provider-agnostic parameters to Ollama parameters if needed
        params = self._map_generation_params(kwargs)
        
        async for chunk in self._adapter.stream_generate(
            prompt=prompt,
            model=model,
            **params
        ):
            yield chunk
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the provider.
        
        Returns:
            Dictionary containing health check information
        """
        if not self.is_initialized:
            try:
                await self.initialize()
            except Exception as e:
                return {
                    'status': 'error',
                    'error': str(e),
                    'service_available': False,
                    'model_available': False,
                    'initialized': False
                }
        
        try:
            return await self._adapter.health_check()
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'service_available': False,
                'model_available': False,
                'initialized': True
            }
    
    def _map_generation_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Map provider-agnostic parameters to Ollama parameters.
        
        Args:
            params: Provider-agnostic parameters
            
        Returns:
            Mapped parameters for Ollama
        """
        mapped = {}
        
        # Map common parameter names
        param_mapping = {
            'max_tokens': 'max_tokens',
            'temperature': 'temperature',
            'top_p': 'top_p',
            'top_k': 'top_k',
            'stop': 'stop',
            'frequency_penalty': 'repeat_penalty',
            'presence_penalty': 'repeat_penalty',
        }
        
        for src, dest in param_mapping.items():
            if src in params:
                mapped[dest] = params[src]
        
        # Add any remaining parameters
        for k, v in params.items():
            if k not in param_mapping:
                mapped[k] = v
                
        return mapped
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Register the provider with the factory
def register() -> None:
    """Register the Ollama provider with the LLM provider factory."""
    from ...providers import register_provider
    
    async def create_provider(config: Optional[Dict[str, Any]] = None) -> OllamaLLMProvider:
        return OllamaLLMProvider(config or {})
    
    register_provider("ollama", create_provider)
