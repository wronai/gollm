# src/gollm/__init__.py
"""
goLLM - Go Learn, Lead, Master!

Intelligent Python code quality guardian with LLM integration,
automated TODO management and CHANGELOG generation.
"""

__version__ = "0.1.0"
__author__ = "goLLM Team"

# Core imports
from .config.config import GollmConfig
from .main import GollmCore
from .validation.validators import CodeValidator

# LLM components
from .llm import (
    BaseLLMProvider,
    BaseLLMConfig as LLMConfig,
    BaseLLMAdapter as LLMAdapter,
)

# LLM Providers
try:
    from .llm.providers.openai import OpenAIClient
    from .llm.providers.openai import OpenAILlmProvider
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAIClient = None
    OpenAILlmProvider = None
    OPENAI_AVAILABLE = False

try:
    from .llm.providers.ollama import OllamaConfig, OllamaLLMProvider, OllamaError
    from .llm.providers.ollama.http import OllamaHttpClient, OllamaHttpAdapter
    OLLAMA_AVAILABLE = True
except ImportError as e:
    OllamaConfig = None
    OllamaLLMProvider = None
    OllamaError = None
    OllamaHttpClient = None
    OllamaHttpAdapter = None
    OLLAMA_AVAILABLE = False

# Exceptions
from .exceptions import (
    GollmError,
    ConfigurationError,
    ValidationError,
    ModelError,
    ModelNotFoundError,
    ModelOperationError,
    APIError,
    AuthenticationError,
    RateLimitError,
    TimeoutError,
    GenerationError,
    InvalidPromptError,
    ContextLengthExceededError,
    ProviderError,
    ProviderNotAvailableError,
    ProviderInitializationError,
    AdapterError,
    AdapterInitializationError,
    AdapterConfigurationError,
)

__all__ = [
    # Core
    "GollmCore",
    "GollmConfig",
    "CodeValidator",
    
    # LLM Base Classes
    "BaseLLMProvider",
    "LLMConfig",
    "LLMAdapter",
    
    # Clients
    "OpenAIClient",
    "OllamaClient",
    
    # Exceptions
    "GollmError",
    "ConfigurationError",
    "ValidationError",
    "ModelError",
    "ModelNotFoundError",
    "ModelOperationError",
    "APIError",
    "AuthenticationError",
    "RateLimitError",
    "TimeoutError",
    "GenerationError",
    "InvalidPromptError",
    "ContextLengthExceededError",
    "ProviderError",
    "ProviderNotAvailableError",
    "ProviderInitializationError",
    "AdapterError",
    "AdapterInitializationError",
    "AdapterConfigurationError",
]
