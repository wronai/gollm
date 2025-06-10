"""
Model management for Ollama integration.

This module provides functionality for managing Ollama models,
including listing available models, checking model availability,
and pulling/deleting models.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set, Tuple

from ..api import OllamaAPIClient
from ...exceptions import ModelNotFoundError, ModelOperationError

logger = logging.getLogger("gollm.ollama.models")


class ModelManager:
    """Manages Ollama models and their operations."""
    
    def __init__(self, api_client: OllamaAPIClient):
        """Initialize the model manager.
        
        Args:
            api_client: Configured OllamaAPIClient instance
        """
        self.api_client = api_client
        self._available_models: Optional[Set[str]] = None
        self._model_details: Dict[str, Dict] = {}
        self._refresh_lock = asyncio.Lock()

    async def refresh_models(self) -> None:
        """Refresh the list of available models from the Ollama server."""
        async with self._refresh_lock:
            try:
                response = await self.api_client.get_models()
                models = response.get('models', [])
                self._available_models = {
                    model['name']  # Keep the full model name with tag
                    for model in models
                }
                self._model_details = {
                    model['name']: model  # Keep the full model name with tag
                    for model in models
                }
                logger.info("Refreshed %d available models", len(self._available_models))
            except Exception as e:
                logger.error("Failed to refresh models: %s", str(e))
                raise ModelOperationError(f"Failed to refresh models: {str(e)}")

    async def list_models(self, refresh: bool = False) -> List[str]:
        """Get a list of available model names.
        
        Args:
            refresh: Whether to force refresh the model list
            
        Returns:
            List of available model names
        """
        if refresh or self._available_models is None:
            await self.refresh_models()
            
        return list(self._available_models or [])

    async def model_exists(self, model_name: str, refresh: bool = False) -> bool:
        """Check if a model exists on the Ollama server.
        
        Args:
            model_name: Name of the model to check (with or without tag)
            refresh: Whether to force refresh the model list
            
        Returns:
            True if the model exists, False otherwise
        """
        if refresh or self._available_models is None:
            await self.refresh_models()
            
        if not self._available_models:
            return False
            
        # First check exact match
        if model_name in self._available_models:
            return True
            
        # If no tag is specified, check with :latest
        if ':' not in model_name:
            return f"{model_name}:latest" in self._available_models
            
        # If tag is specified but not found, check base name
        base_name = model_name.split(':')[0]
        return (
            base_name in self._available_models or
            f"{base_name}:latest" in self._available_models
        )

    async def get_model_info(self, model_name: str) -> Dict:
        """Get detailed information about a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary containing model information
            
        Raises:
            ModelNotFoundError: If the model doesn't exist
        """
        if not await self.model_exists(model_name):
            raise ModelNotFoundError(f"Model '{model_name}' not found")
            
        if model_name in self._model_details:
            return self._model_details[model_name]
            
        # If we don't have the details, try to get them
        try:
            # This is a placeholder - Ollama's API doesn't have a direct endpoint for this
            # So we'll just return basic info
            return {
                'name': model_name,
                'model': model_name,
                'size': 0,  # Unknown
                'digest': '',  # Unknown
                'details': {
                    'parameter_size': '7B',  # Default assumption
                    'quantization_level': 'Q4_0',  # Common quantization
                }
            }
        except Exception as e:
            logger.error("Failed to get model info for %s: %s", model_name, str(e))
            raise ModelOperationError(f"Failed to get model info: {str(e)}")

    async def pull_model(self, model_name: str) -> bool:
        """Pull a model from the Ollama model hub.
        
        Args:
            model_name: Name of the model to pull (e.g., "codellama:7b")
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ModelOperationError: If the pull operation fails
        """
        logger.info("Pulling model: %s", model_name)
        
        try:
            # Ollama's pull endpoint streams the download progress
            # We'll just wait for it to complete
            await self.api_client.request(
                'POST',
                '/api/pull',
                data={'name': model_name}
            )
            
            # Refresh the model list
            await self.refresh_models()
            return True
            
        except Exception as e:
            logger.error("Failed to pull model %s: %s", model_name, str(e))
            raise ModelOperationError(f"Failed to pull model: {str(e)}")

    async def delete_model(self, model_name: str) -> bool:
        """Delete a model from the Ollama server.
        
        Args:
            model_name: Name of the model to delete
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ModelNotFoundError: If the model doesn't exist
            ModelOperationError: If the delete operation fails
        """
        if not await self.model_exists(model_name):
            raise ModelNotFoundError(f"Model '{model_name}' not found")
            
        logger.info("Deleting model: %s", model_name)
        
        try:
            await self.api_client.request(
                'DELETE',
                '/api/delete',
                data={'name': model_name}
            )
            
            # Update our local cache
            if self._available_models and model_name in self._available_models:
                self._available_models.remove(model_name)
                if model_name in self._model_details:
                    del self._model_details[model_name]
                    
            return True
            
        except Exception as e:
            logger.error("Failed to delete model %s: %s", model_name, str(e))
            raise ModelOperationError(f"Failed to delete model: {str(e)}")

    async def ensure_model(self, model_name: str, pull_if_missing: bool = True) -> bool:
        """Ensure a model is available, pulling it if necessary.
        
        Args:
            model_name: Name of the model to ensure is available
            pull_if_missing: Whether to pull the model if it's not available
            
        Returns:
            True if the model is available, False otherwise
            
        Raises:
            ModelOperationError: If the model is not available and cannot be pulled
        """
        if await self.model_exists(model_name):
            return True
            
        if not pull_if_missing:
            return False
            
        try:
            await self.pull_model(model_name)
            return True
        except Exception as e:
            logger.error("Failed to ensure model %s: %s", model_name, str(e))
            return False
