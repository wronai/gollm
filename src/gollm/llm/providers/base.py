"""Base classes for LLM providers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncContextManager

class BaseLLMProvider(AsyncContextManager, ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the LLM provider with configuration.
        
        Args:
            config: Provider-specific configuration
        """
        self.config = config
    
    @abstractmethod
    async def generate_response(
        self, 
        prompt: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a response from the LLM.
        
        Args:
            prompt: The prompt to generate a response for
            context: Additional context for the generation
            
        Returns:
            Dictionary containing at least:
            - success (bool): Whether the generation was successful
            - generated_text (str): The generated text (if successful)
            - error (str): Error message if not successful
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the LLM provider.
        
        Returns:
            Dictionary containing health check information
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available for use.
        
        Returns:
            bool: True if available, False otherwise
        """
        pass
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass
