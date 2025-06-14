"""Ollama LLM Provider for goLLM.

This package provides integration with Ollama's local LLM service with both HTTP and gRPC support.
"""

from .config import OllamaConfig
from .factory import AdapterType, create_adapter, get_best_available_adapter
# Import HTTP modules
from .http import OllamaHttpAdapter, OllamaHttpClient, OllamaOperations
from .provider_new import OllamaLLMProvider

# Try to import gRPC modules if available
try:
    from .grpc import GRPC_AVAILABLE, OllamaGrpcAdapter, OllamaGrpcClient

    __all__ = [
        "OllamaConfig",
        "OllamaLLMProvider",
        "create_adapter",
        "get_best_available_adapter",
        "AdapterType",
        "OllamaHttpAdapter",
        "OllamaHttpClient",
        "OllamaOperations",
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
