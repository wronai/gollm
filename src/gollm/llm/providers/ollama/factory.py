"""Factory for creating Ollama adapters based on configuration."""

import logging
from typing import Any, Dict, Optional, Union

from .config import OllamaConfig
from .http import OllamaHttpAdapter
from .modular_adapter import OllamaModularAdapter

# Conditionally import gRPC adapter if available
try:
    from .grpc import GRPC_AVAILABLE, OllamaGrpcAdapter
except ImportError:
    GRPC_AVAILABLE = False

logger = logging.getLogger("gollm.ollama.factory")


class AdapterType:
    """Enum-like class for adapter types."""

    HTTP = "http"
    GRPC = "grpc"
    MODULAR = "modular"


def create_adapter(
    config: OllamaConfig, adapter_type: Optional[str] = None
) -> Union[OllamaHttpAdapter, "OllamaGrpcAdapter", OllamaModularAdapter]:
    """Create an appropriate Ollama adapter based on configuration.

    Args:
        config: Ollama configuration
        adapter_type: Type of adapter to create (http, grpc, or modular)

    Returns:
        An initialized adapter instance

    Raises:
        ImportError: If gRPC adapter is requested but dependencies are not available
        ValueError: If an invalid adapter type is specified
    """
    # Check if adapter_type is specified in config
    if adapter_type is None and hasattr(config, "adapter_type"):
        adapter_type = config.adapter_type
        logger.debug(f"Using adapter_type from config: {adapter_type}")

    # If adapter_type is still not specified, use HTTP by default
    if adapter_type is None:
        adapter_type = AdapterType.HTTP

    # Normalize adapter type
    adapter_type = adapter_type.lower()

    if adapter_type == AdapterType.HTTP:
        logger.debug("Creating HTTP adapter")
        return OllamaHttpAdapter(config)
    elif adapter_type == AdapterType.MODULAR:
        logger.debug("Creating modular adapter with enhanced logging and performance")
        return OllamaModularAdapter(config)
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


def get_best_available_adapter(
    config: OllamaConfig,
) -> Union[OllamaHttpAdapter, "OllamaGrpcAdapter", OllamaModularAdapter]:
    """Get the best available adapter based on installed dependencies.

    This will prefer the modular adapter for enhanced logging and performance,
    then gRPC if available, otherwise fall back to HTTP.

    Args:
        config: Ollama configuration

    Returns:
        An initialized adapter instance
    """
    # First check if adapter_type is explicitly set in config
    if hasattr(config, "adapter_type") and config.adapter_type:
        adapter_type = config.adapter_type.lower()
        logger.info(f"Using adapter type from config: {adapter_type}")
        return create_adapter(config, adapter_type)

    # If not, check if we should use the modular adapter (default to True)
    use_modular = getattr(config, "use_modular_adapter", True)

    if use_modular:
        logger.info("Using modular adapter for enhanced logging and performance")
        return create_adapter(config, AdapterType.MODULAR)
    elif GRPC_AVAILABLE:
        logger.info("Using gRPC adapter for better performance")
        return create_adapter(config, AdapterType.GRPC)
    else:
        logger.info("Using HTTP adapter")
        return create_adapter(config, AdapterType.HTTP)
