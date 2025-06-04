"""
Ollama LLM Adapter

This module provides the main adapter class for interacting with Ollama's
language models, handling model selection, prompt processing, and response
generation with proper error handling and logging.
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Union, AsyncGenerator

import aiohttp

from .config import OllamaConfig
from .models.manager import ModelManager
from .api.client import OllamaAPIClient
from ..base import BaseLLMAdapter
from ...exceptions import (
    ModelNotFoundError,
    ModelOperationError,
    ConfigurationError,
    ValidationError
)
from .utils.validation import validate_prompt, validate_model
from .utils.logging import log_request, log_response

logger = logging.getLogger("gollm.ollama.adapter")


class OllamaAdapter(BaseLLMAdapter):
    """Adapter for interacting with Ollama's LLM API.
    
    This class provides methods for generating text, managing models,
    and handling API communication with proper error handling and logging.
    """
    
    def __init__(self, config: Optional[Union[OllamaConfig, Dict[str, Any]]] = None):
        """Initialize the Ollama adapter.
        
        Args:
            config: Configuration dictionary or OllamaConfig instance
        """
        if config is None:
            config = OllamaConfig()
        elif isinstance(config, dict):
            config = OllamaConfig.from_dict(config)
            
        self.config = config
        self.api_client: Optional[OllamaAPIClient] = None
        self.model_manager: Optional[ModelManager] = None
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize the adapter and its dependencies."""
        if self._initialized:
            return
            
        # Initialize the API client
        self.api_client = OllamaAPIClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout
        )
        
        # Initialize the model manager
        self.model_manager = ModelManager(self.api_client)
        
        # Verify the model exists
        try:
            await self.ensure_model(self.config.model)
        except Exception as e:
            logger.error("Failed to initialize Ollama adapter: %s", str(e))
            raise
            
        self._initialized = True
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        
    async def close(self) -> None:
        """Clean up resources."""
        if self.api_client:
            await self.api_client.close()
            self.api_client = None
            
        self.model_manager = None
        self._initialized = False
        
    async def ensure_model(self, model_name: str) -> bool:
        """Ensure the specified model is available.
        
        Args:
            model_name: Name of the model to ensure is available
            
        Returns:
            bool: True if the model is available, False otherwise
            
        Raises:
            ModelOperationError: If there's an error checking the model
        """
        if not self.model_manager:
            raise RuntimeError("Adapter not initialized")
            
        return await self.model_manager.ensure_model(model_name)
        
    async def is_available(self) -> bool:
        """Check if the Ollama service is available.
        
        Returns:
            bool: True if the service is available, False otherwise
        """
        try:
            if not self.api_client:
                async with OllamaAPIClient(base_url=self.config.base_url) as client:
                    await client.get_models()
                return True
                
            await self.api_client.get_models()
            return True
        except Exception:
            return False
            
    async def list_models(self) -> List[str]:
        """List available models.
        
        Returns:
            List of available model names
            
        Raises:
            ModelOperationError: If there's an error listing models
        """
        if not self.model_manager:
            raise RuntimeError("Adapter not initialized")
            
        return await self.model_manager.list_models()
        
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
            ValidationError: If the prompt is invalid
        """
        await self.initialize()
        
        # Validate input
        is_valid, error = validate_prompt(prompt)
        if not is_valid:
            raise ValidationError(f"Invalid prompt: {error}")
            
        # Use configured model if none specified
        model = model or self.config.model
        validate_model(model)
        
        # Ensure model is available
        if not await self.ensure_model(model):
            raise ModelNotFoundError(f"Model '{model}' not found and could not be pulled")
            
        # Prepare generation parameters
        params = {
            'model': model,
            'prompt': prompt,
            'temperature': kwargs.pop('temperature', self.config.temperature),
            'top_p': kwargs.pop('top_p', self.config.top_p),
            'top_k': kwargs.pop('top_k', self.config.top_k),
            'repeat_penalty': kwargs.pop('repeat_penalty', self.config.repeat_penalty),
            'stop': kwargs.pop('stop', self.config.stop),
            'max_tokens': kwargs.pop('max_tokens', self.config.max_tokens),
            **kwargs
        }
        
        # Log the request
        request_context = log_request(
            logger=logger,
            method='POST',
            url=f"{self.config.base_url}/api/generate",
            data=params
        )
        
        try:
            # Make the API request
            response = await self.api_client.generate(
                prompt=prompt,
                model=model,
                **params
            )
            
            # Log successful response
            log_response(
                logger=logger,
                context=request_context,
                status_code=200,
                data=response
            )
            
            return response
            
        except Exception as e:
            # Log the error
            log_response(
                logger=logger,
                context=request_context,
                status_code=getattr(e, 'status', 500),
                error=e
            )
            raise ModelOperationError(f"Failed to generate text: {str(e)}") from e
            
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
            ValidationError: If the messages are invalid
        """
        await self.initialize()
        
        # Validate input
        if not messages or not all(
            isinstance(m, dict) and 'role' in m and 'content' in m
            for m in messages
        ):
            raise ValidationError("Messages must be a list of dicts with 'role' and 'content' keys")
            
        # Use configured model if none specified
        model = model or self.config.model
        validate_model(model)
        
        # Ensure model is available
        if not await self.ensure_model(model):
            raise ModelNotFoundError(f"Model '{model}' not found and could not be pulled")
            
        # Prepare chat parameters
        params = {
            'model': model,
            'messages': messages,
            'temperature': kwargs.pop('temperature', self.config.temperature),
            'top_p': kwargs.pop('top_p', self.config.top_p),
            'top_k': kwargs.pop('top_k', self.config.top_k),
            'repeat_penalty': kwargs.pop('repeat_penalty', self.config.repeat_penalty),
            'stop': kwargs.pop('stop', self.config.stop),
            'max_tokens': kwargs.pop('max_tokens', self.config.max_tokens),
            **kwargs
        }
        
        # Log the request
        request_context = log_request(
            logger=logger,
            method='POST',
            url=f"{self.config.base_url}/api/chat",
            data=params
        )
        
        try:
            # Make the API request
            response = await self.api_client.chat(
                messages=messages,
                model=model,
                **params
            )
            
            # Log successful response
            log_response(
                logger=logger,
                context=request_context,
                status_code=200,
                data=response
            )
            
            return response
            
        except Exception as e:
            # Log the error
            log_response(
                logger=logger,
                context=request_context,
                status_code=getattr(e, 'status', 500),
                error=e
            )
            raise ModelOperationError(f"Chat completion failed: {str(e)}") from e
    
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
        await self.initialize()
        
        # Validate input
        is_valid, error = validate_prompt(prompt)
        if not is_valid:
            raise ValidationError(f"Invalid prompt: {error}")
            
        # Use configured model if none specified
        model = model or self.config.model
        validate_model(model)
        
        # Ensure model is available
        if not await self.ensure_model(model):
            raise ModelNotFoundError(f"Model '{model}' not found and could not be pulled")
            
        # Prepare generation parameters
        params = {
            'model': model,
            'prompt': prompt,
            'stream': True,
            'temperature': kwargs.pop('temperature', self.config.temperature),
            'top_p': kwargs.pop('top_p', self.config.top_p),
            'top_k': kwargs.pop('top_k', self.config.top_k),
            'repeat_penalty': kwargs.pop('repeat_penalty', self.config.repeat_penalty),
            'stop': kwargs.pop('stop', self.config.stop),
            'max_tokens': kwargs.pop('max_tokens', self.config.max_tokens),
            **kwargs
        }
        
        # Log the request
        request_context = log_request(
            logger=logger,
            method='POST',
            url=f"{self.config.base_url}/api/generate",
            data={**params, 'stream': '...'}
        )
        
        try:
            # Make the streaming request
            async for chunk in self.api_client.generate(
                prompt=prompt,
                model=model,
                stream=True,
                **{k: v for k, v in params.items() if k not in ('prompt', 'model')}
            ):
                yield chunk
                
        except Exception as e:
            # Log the error
            log_response(
                logger=logger,
                context=request_context,
                status_code=getattr(e, 'status', 500),
                error=e
            )
            raise ModelOperationError(f"Stream generation failed: {str(e)}") from e

    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the Ollama service.
        
        Returns:
            Dictionary containing health check information
        """
        try:
            # Check if the service is available
            is_available = await self.is_available()
            
            # Get model information if available
            model_info = {}
            if is_available and self.model_manager:
                try:
                    model_info = await self.model_manager.get_model_info(self.config.model)
                except Exception as e:
                    logger.warning(f"Failed to get model info: {str(e)}")
            
            return {
                'status': 'healthy' if is_available else 'unhealthy',
                'service_available': is_available,
                'model_available': 'model' in model_info,
                'model_info': model_info if model_info else None,
                'config': {
                    'base_url': self.config.base_url,
                    'model': self.config.model,
                    'timeout': self.config.timeout,
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'service_available': False,
                'model_available': False,
                'config': {
                    'base_url': self.config.base_url,
                    'model': self.config.model,
                    'timeout': self.config.timeout,
                }
            }
