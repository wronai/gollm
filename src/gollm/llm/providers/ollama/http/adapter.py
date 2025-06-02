"""HTTP adapter for Ollama API."""

import logging
from typing import Dict, Any, Optional, List, AsyncIterator

from ..config import OllamaConfig
from .client import OllamaHttpClient
from .operations import OllamaOperations

logger = logging.getLogger('gollm.ollama.http')

class OllamaHttpAdapter:
    """HTTP adapter for Ollama API with optimized request handling."""
    
    def __init__(self, config: OllamaConfig):
        """Initialize the Ollama HTTP adapter.
        
        Args:
            config: Ollama configuration
        """
        self.config = config
        self.client: Optional[OllamaHttpClient] = None
        self.operations: Optional[OllamaOperations] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.client = OllamaHttpClient(self.config)
        await self.client.__aenter__()
        self.operations = OllamaOperations(self.client)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def is_available(self) -> bool:
        """Check if Ollama API is available.
        
        Returns:
            True if the API is available, False otherwise
        """
        try:
            result = await self.client.check_health()
            return result.get('success', False)
        except Exception as e:
            logger.error(f"Error checking Ollama availability: {str(e)}")
            return False
    
    async def list_models(self) -> Dict[str, Any]:
        """List available models.
        
        Returns:
            Dictionary containing available models
        """
        try:
            return await self.client.list_models()
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return {"models": [], "error": str(e)}
    
    async def generate(self, prompt: str, model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate text using the completion endpoint.
        
        Args:
            prompt: The prompt to generate from
            model: Model to use (defaults to config model)
            **kwargs: Additional generation parameters
                
        Returns:
            Dictionary containing the generated text and metadata
        """
        if not self.operations:
            return {"success": False, "error": "Adapter not initialized"}
            
        try:
            return await self.operations.generate(prompt, model, **kwargs)
        except Exception as e:
            logger.exception(f"Error in generate: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate chat completion.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            model: Model to use for generation (defaults to config model)
            **kwargs: Additional generation parameters
                
        Returns:
            Dictionary containing the generated response and metadata
        """
        if not self.operations:
            return {"success": False, "error": "Adapter not initialized"}
            
        try:
            return await self.operations.chat(messages, model, **kwargs)
        except Exception as e:
            logger.exception(f"Error in chat: {str(e)}")
            return {"success": False, "error": str(e)}
