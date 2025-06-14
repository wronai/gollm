"""Ollama LLM Provider for goLLM.

This package provides integration with Ollama's local LLM service with both HTTP and gRPC support.
The provider is organized into modular components for better maintainability and testability.
"""

# Core components
from .config import OllamaConfig
from .factory import AdapterType, create_adapter, get_best_available_adapter
from .generation import generate_response, stream_response
from .health import (check_model_availability, check_service_availability,
                     comprehensive_health_check)
# Import HTTP modules
from .http import OllamaHttpAdapter, OllamaHttpClient, OllamaOperations
from .models import (ensure_model_available, get_model_info, list_models,
                     validate_model_config)
# New modular components
from .prompt import (extract_response_content, format_chat_messages,
                     format_prompt_for_ollama)
from .provider import OllamaLLMProvider

# Try to import gRPC modules if available
try:
    from .grpc import GRPC_AVAILABLE, OllamaGrpcAdapter, OllamaGrpcClient

    __all__ = [
        # Core components
        "OllamaConfig",
        "OllamaLLMProvider",
        "create_adapter",
        "get_best_available_adapter",
        "AdapterType",
        # New modular components
        "format_prompt_for_ollama",
        "format_chat_messages",
        "extract_response_content",
        "list_models",
        "get_model_info",
        "ensure_model_available",
        "validate_model_config",
        "check_service_availability",
        "check_model_availability",
        "comprehensive_health_check",
        "generate_response",
        "stream_response",
        # HTTP components
        "OllamaHttpAdapter",
        "OllamaHttpClient",
        "OllamaOperations",
        # gRPC components (if available)
        "OllamaGrpcAdapter",
        "OllamaGrpcClient",
        "GRPC_AVAILABLE",
    ]
except ImportError:
    GRPC_AVAILABLE = False
    __all__ = [
        "OllamaConfig",
        "OllamaLLMProvider",
        "create_adapter",
        "get_best_available_adapter",
        "AdapterType",
        "OllamaHttpAdapter",
        "OllamaHttpClient",
        "OllamaOperations",
        "GRPC_AVAILABLE",
    ]

# For backward compatibility
from .http.adapter import OllamaHttpAdapter as OllamaAdapter
