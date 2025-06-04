"""
Exceptions for the LLM module.

This module defines custom exceptions used throughout the LLM components.
"""

class LLMError(Exception):
    """Base exception for all LLM-related errors."""
    pass


class ModelError(LLMError):
    """Base exception for model-related errors."""
    pass


class ModelNotFoundError(ModelError):
    """Raised when a specified model is not found or unavailable."""
    pass


class ModelOperationError(ModelError):
    """Raised when an operation on a model fails."""
    pass


class ConfigurationError(LLMError):
    """Raised when there is a configuration error."""
    pass


class ValidationError(LLMError):
    """Raised when validation of input data fails."""
    pass


class APIError(LLMError):
    """Raised when there is an error communicating with the LLM API."""
    pass


class AuthenticationError(APIError):
    """Raised when authentication with the LLM API fails."""
    pass


class RateLimitError(APIError):
    """Raised when the rate limit for the LLM API is exceeded."""
    pass


class TimeoutError(APIError):
    """Raised when a request to the LLM API times out."""
    pass


class GenerationError(LLMError):
    """Raised when there is an error during text generation."""
    pass


class InvalidPromptError(GenerationError):
    """Raised when an invalid prompt is provided for generation."""
    pass


class ContextLengthExceededError(GenerationError):
    """Raised when the context length is exceeded during generation."""
    pass
