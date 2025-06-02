"""gRPC client implementation for Ollama API."""

import logging

try:
    from .adapter import OllamaGrpcAdapter
    from .client import OllamaGrpcClient, GRPC_AVAILABLE
    
    __all__ = ['OllamaGrpcAdapter', 'OllamaGrpcClient', 'GRPC_AVAILABLE']
except ImportError:
    logging.warning("gRPC dependencies not available. Some features will be disabled.")
    GRPC_AVAILABLE = False
    __all__ = ['GRPC_AVAILABLE']
