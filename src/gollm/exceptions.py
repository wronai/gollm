"""
Core exceptions for the GoLLM package.

This module defines all custom exceptions used throughout the GoLLM codebase.
"""

class GollmError(Exception):
    """Base exception for all GoLLM-specific exceptions."""
    pass


class ConfigurationError(GollmError):
    """Raised when there is a configuration error."""
    pass


class ValidationError(GollmError):
    """Raised when validation of input data fails."""
    pass


class ModelError(GollmError):
    """Base exception for model-related errors."""
    pass


class ModelNotFoundError(ModelError):
    """Raised when a specified model is not found or unavailable."""
    pass


class ModelOperationError(ModelError):
    """Raised when an operation on a model fails."""
    pass


class APIError(GollmError):
    """Base exception for API-related errors."""
    pass


class AuthenticationError(APIError):
    """Raised when authentication with an API fails."""
    pass


class RateLimitError(APIError):
    """Raised when the rate limit for an API is exceeded."""
    pass


class TimeoutError(APIError):
    """Raised when a request to an API times out."""
    pass


class GenerationError(GollmError):
    """Raised when there is an error during text generation."""
    pass


class InvalidPromptError(GenerationError):
    """Raised when an invalid prompt is provided for generation."""
    pass


class ContextLengthExceededError(GenerationError):
    """Raised when the context length is exceeded during generation."""
    pass


class ProviderError(GollmError):
    """Base exception for LLM provider errors."""
    pass


class ProviderNotAvailableError(ProviderError):
    """Raised when a requested provider is not available."""
    pass


class ProviderInitializationError(ProviderError):
    """Raised when a provider fails to initialize."""
    pass


class AdapterError(GollmError):
    """Base exception for adapter-related errors."""
    pass


class AdapterInitializationError(AdapterError):
    """Raised when an adapter fails to initialize."""
    pass


class AdapterConfigurationError(AdapterError):
    """Raised when there is an error in the adapter configuration."""
    pass
