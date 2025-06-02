"""Factory for creating Ollama adapters based on configuration."""

import logging
from typing import Optional, Union, Dict, Any

from .config import OllamaConfig
from .http import OllamaHttpAdapter

# Conditionally import gRPC adapter if available
try:
    from .grpc import OllamaGrpcAdapter, GRPC_AVAILABLE
except ImportError:
    GRPC_AVAILABLE = False

logger = logging.getLogger('gollm.ollama.factory')

class AdapterType:
    """Enum-like class for adapter types."""
    HTTP = "http"
    GRPC = "grpc"

def create_adapter(
    config: OllamaConfig,
    adapter_type: Optional[str] = None
) -> Union[OllamaHttpAdapter, 'OllamaGrpcAdapter']:
    """Create an appropriate Ollama adapter based on configuration.
    
    Args:
        config: Ollama configuration
        adapter_type: Type of adapter to create (http or grpc)
        
    Returns:
        An initialized adapter instance
        
    Raises:
        ImportError: If gRPC adapter is requested but dependencies are not available
        ValueError: If an invalid adapter type is specified
    """
    # If adapter_type is not specified, use HTTP by default
    if adapter_type is None:
        adapter_type = AdapterType.HTTP
        
    # Normalize adapter type
    adapter_type = adapter_type.lower()
    
    if adapter_type == AdapterType.HTTP:
        logger.debug("Creating HTTP adapter")
        return OllamaHttpAdapter(config)
    elif adapter_type == AdapterType.GRPC:
        if not GRPC_AVAILABLE:
            logger.warning(
                "gRPC adapter requested but dependencies not available. "
                "Falling back to HTTP adapter."
            )
            return OllamaHttpAdapter(config)
            
        logger.debug("Creating gRPC adapter")
        from .grpc import OllamaGrpcAdapter
        return OllamaGrpcAdapter(config)
    else:
        raise ValueError(f"Invalid adapter type: {adapter_type}")

def get_best_available_adapter(config: OllamaConfig) -> Union[OllamaHttpAdapter, 'OllamaGrpcAdapter']:
    """Get the best available adapter based on installed dependencies.
    
    This will prefer gRPC if available, otherwise fall back to HTTP.
    
    Args:
        config: Ollama configuration
        
    Returns:
        An initialized adapter instance
    """
    if GRPC_AVAILABLE:
        logger.info("Using gRPC adapter for better performance")
        return create_adapter(config, AdapterType.GRPC)
    else:
        logger.info("Using HTTP adapter (gRPC not available)")
        return create_adapter(config, AdapterType.HTTP)
