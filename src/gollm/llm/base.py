"""
Base classes for LLM providers.

This module defines the abstract base classes that all LLM providers must implement.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncGenerator, Union


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers.
    
    All LLM providers must implement these methods to be compatible with the
    GoLLM system.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the provider.
        
        Returns:
            str: The name of the provider (e.g., 'openai', 'ollama', etc.)
        """
        pass
    
    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if the provider is initialized.
        
        Returns:
            bool: True if the provider is initialized, False otherwise
        """
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider.
        
        This method should be called before any other methods. It should
        perform any necessary setup, such as establishing connections or
        loading models.
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close the provider and release resources.
        
        This method should be called when the provider is no longer needed.
        It should clean up any resources, such as connections or models.
        """
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the provider is available.
        
        This method should check if the provider is available for use. This
        might involve checking if a local model is loaded or if an API key is
        valid.
        
        Returns:
            bool: True if the provider is available, False otherwise
        """
        pass
    
    @abstractmethod
    async def list_models(self) -> List[str]:
        """List available models.
        
        Returns:
            List[str]: A list of available model names
            
        Raises:
            ModelOperationError: If there's an error listing models
        """
        pass
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text using the specified model.
        
        Args:
            prompt: The prompt to generate text from
            model: Name of the model to use (defaults to the provider's default)
            **kwargs: Additional generation parameters
            
        Returns:
            Dictionary containing the generated text and metadata
            
        Raises:
            ModelNotFoundError: If the specified model is not available
            ModelOperationError: If there's an error during generation
        """
        pass
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a chat completion.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Name of the model to use (defaults to the provider's default)
            **kwargs: Additional generation parameters
            
        Returns:
            Dictionary containing the generated response and metadata
            
        Raises:
            ModelNotFoundError: If the specified model is not available
            ModelOperationError: If there's an error during generation
        """
        pass
    
    @abstractmethod
    async def stream_generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream generated text chunks from the model.
        
        Args:
            prompt: The prompt to generate text from
            model: Name of the model to use (defaults to the provider's default)
            **kwargs: Additional generation parameters
            
        Yields:
            Dictionary containing chunks of generated text and metadata
            
        Raises:
            ModelNotFoundError: If the specified model is not available
            ModelOperationError: If there's an error during generation
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the provider.
        
        Returns:
            Dictionary containing health check information, including at least:
            - status: 'healthy', 'degraded', or 'unhealthy'
            - service_available: bool indicating if the service is reachable
            - model_available: bool indicating if the model is loaded/available
        """
        pass
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


class BaseLLMConfig(ABC):
    """Abstract base class for LLM provider configurations.
    
    All LLM provider configurations should inherit from this class.
    """
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary.
        
        Returns:
            Dict[str, Any]: The configuration as a dictionary
        """
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'BaseLLMConfig':
        """Create a configuration from a dictionary.
        
        Args:
            config: Dictionary containing configuration values
            
        Returns:
            BaseLLMConfig: A new configuration instance
            
        Raises:
            ConfigurationError: If the configuration is invalid
        """
        pass
