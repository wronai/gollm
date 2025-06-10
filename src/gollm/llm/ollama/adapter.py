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
from typing import Any, Dict, List, Optional, Type, Union, AsyncGenerator

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
    
    @property
    def provider(self) -> str:
        """Get the name of the provider this adapter is for.
        
        Returns:
            str: The provider name ('ollama')
        """
        return "ollama"
        
    @property
    def config_class(self) -> Type['OllamaConfig']:
        """Get the configuration class for this adapter.
        
        Returns:
            Type[OllamaConfig]: The configuration class
        """
        return OllamaConfig
        
    @classmethod
    def get_default_config(cls) -> 'OllamaConfig':
        """Get the default configuration for this adapter.
        
        Returns:
            OllamaConfig: A default configuration instance
        """
        return OllamaConfig()
        
    def get_provider(self, config: 'OllamaConfig') -> 'OllamaLLMProvider':
        """Get a provider instance configured with the given config.
        
        Args:
            config: The configuration to use
            
        Returns:
            OllamaLLMProvider: A configured provider instance
            
        Raises:
            ConfigurationError: If the configuration is invalid
        """
        if not isinstance(config, OllamaConfig):
            config = OllamaConfig.from_dict(config)
            
        return OllamaLLMProvider(config)
    
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
            # The prompt is already included in params, so we don't need to pass it again
            response = await self.api_client.generate(**params)
            
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
            # The messages are already included in params, so we don't need to pass them again
            response = await self.api_client.chat(**params)
            
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
        logger.debug("[STREAM_GENERATE] Starting stream_generate")
        logger.debug(f"[STREAM_GENERATE] Prompt: {prompt[:100]}...")
        logger.debug(f"[STREAM_GENERATE] Model: {model or 'default'}")
        logger.debug(f"[STREAM_GENERATE] Additional kwargs: {kwargs}")
        
        await self.initialize()
        
        # Validate input
        is_valid, error = validate_prompt(prompt)
        if not is_valid:
            error_msg = f"Invalid prompt: {error}"
            logger.error(f"[STREAM_GENERATE] {error_msg}")
            raise ValidationError(error_msg)
            
        # Use configured model if none specified
        model = model or self.config.model
        logger.debug(f"[STREAM_GENERATE] Using model: {model}")
        validate_model(model)
        
        # Ensure model is available
        logger.debug("[STREAM_GENERATE] Ensuring model is available...")
        if not await self.ensure_model(model):
            error_msg = f"Model '{model}' not found and could not be pulled"
            logger.error(f"[STREAM_GENERATE] {error_msg}")
            raise ModelNotFoundError(error_msg)
            
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
        
        logger.debug(f"[STREAM_GENERATE] Prepared params: {params}")
        
        # Log the request
        request_context = log_request(
            logger=logger,
            method='POST',
            url=f"{self.config.base_url}/api/generate",
            data={**params, 'stream': '...'}
        )
        
        try:
            # Prepare parameters for the API call
            # Exclude prompt and model from params since they're passed separately
            stream_params = {k: v for k, v in params.items() 
                           if k not in ('prompt', 'model', 'stream')}
            
            logger.debug(f"[STREAM_GENERATE] Calling generate with stream=True")
            logger.debug(f"[STREAM_GENERATE] Prompt: {prompt[:50]}...")
            logger.debug(f"[STREAM_GENERATE] Model: {model}")
            logger.debug(f"[STREAM_GENERATE] Stream params: {stream_params}")
            
            # Debug the API client and its generate method
            logger.debug(f"[STREAM_GENERATE] API client: {self.api_client}")
            logger.debug(f"[STREAM_GENERATE] API client type: {type(self.api_client).__name__}")
            logger.debug(f"[STREAM_GENERATE] API client has generate: {hasattr(self.api_client, 'generate')}")
            
            if hasattr(self.api_client, 'generate'):
                logger.debug(f"[STREAM_GENERATE] API client generate type: {type(self.api_client.generate).__name__}")
                logger.debug(f"[STREAM_GENERATE] API client generate is coroutine: {asyncio.iscoroutinefunction(self.api_client.generate)}")
            
            # Call the API client's generate method with stream=True
            try:
                logger.debug("[STREAM_GENERATE] Starting async iteration over generate...")
                chunk_count = 0
                
                # Call the API client's generate method and await the result
                # This should return an async iterable
                logger.debug("[STREAM_GENERATE] Calling api_client.generate...")
                response = await self.api_client.generate(
                    prompt=prompt,
                    model=model,
                    stream=True,
                    **stream_params
                )
                
                logger.debug(f"[STREAM_GENERATE] Response type: {type(response).__name__}")
                logger.debug(f"[STREAM_GENERATE] Response is async iterable: {hasattr(response, '__aiter__')}")
                
                # Iterate over the response
                async for chunk in response:
                    chunk_count += 1
                    logger.debug(f"[STREAM_GENERATE] Yielding chunk {chunk_count}: {chunk}")
                    yield chunk
                    
                logger.debug(f"[STREAM_GENERATE] Completed streaming {chunk_count} chunks")
                
            except Exception as e:
                logger.error(f"[STREAM_GENERATE] Error in generate iteration: {str(e)}", exc_info=True)
                logger.error(f"[STREAM_GENERATE] Error type: {type(e).__name__}")
                raise
                
        except Exception as e:
            # Log the error
            error_type = type(e).__name__
            error_msg = str(e)
            logger.error(f"[STREAM_GENERATE] Stream generation failed: {error_type} - {error_msg}", exc_info=True)
            
            log_response(
                logger=logger,
                context=request_context,
                status_code=getattr(e, 'status', 500),
                error=e
            )
            raise ModelOperationError(f"Stream generation failed: {error_msg}") from e

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
