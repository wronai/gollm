"""
LLM Integration module for goLLM

Provides integration with various LLM providers including:
- OpenAI GPT models
- Anthropic Claude
- Local Ollama models
"""

# Base classes
from .base import BaseLLMProvider, BaseLLMConfig, BaseLLMAdapter

# Legacy imports for backward compatibility
from .context_builder import ContextBuilder
from .ollama_adapter import OllamaAdapter, OllamaLLMProvider

# Import from the orchestrator package
from .orchestrator import (LLMClient, LLMGenerationConfig, LLMIterationResult,
                           LLMOrchestrator, LLMRequest, LLMResponse,
                           ResponseValidator)
from .prompt_formatter import PromptFormatter

# Import exceptions
from .exceptions import (
    LLMError,
    ModelError,
    ModelNotFoundError,
    ModelOperationError,
    ConfigurationError,
    ValidationError,
    APIError,
    AuthenticationError,
    RateLimitError,
    TimeoutError,
    GenerationError,
    InvalidPromptError,
    ContextLengthExceededError
)

__all__ = [
    # Base classes
    "BaseLLMProvider",
    "BaseLLMConfig",
    "BaseLLMAdapter",
    
    # Core components
    "LLMOrchestrator",
    
    # Exceptions
    "LLMError",
    "ModelError",
    "ModelNotFoundError",
    "ModelOperationError",
    "ConfigurationError",
    "ValidationError",
    "APIError",
    "AuthenticationError",
    "RateLimitError",
    "TimeoutError",
    "GenerationError",
    "InvalidPromptError",
    "ContextLengthExceededError",
    "LLMRequest",
    "LLMResponse",
    "LLMIterationResult",
    "LLMGenerationConfig",
    "LLMClient",
    "ResponseValidator",
    # Legacy components
    "ContextBuilder",
    "PromptFormatter",
    "OllamaAdapter",
    "OllamaLLMProvider",
    "OllamaLLMProvider",
]
