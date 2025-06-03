"""Model management utilities for Ollama provider."""

import logging
from typing import Any, Dict, List, Optional, Union

from .config import OllamaConfig

logger = logging.getLogger("gollm.ollama.models")


async def list_models(adapter) -> List[Dict[str, Any]]:
    """List available models from Ollama.

    Args:
        adapter: The Ollama adapter to use

    Returns:
        List of model information dictionaries
    """
    try:
        result = await adapter.list_models()
        if "models" in result and isinstance(result["models"], list):
            logger.debug(f"Found {len(result['models'])} models")
            return result["models"]
        else:
            logger.warning(f"Unexpected response format from list_models: {result}")
            return []
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return []


async def get_model_info(adapter, model_name: str) -> Optional[Dict[str, Any]]:
    """Get information about a specific model.

    Args:
        adapter: The Ollama adapter to use
        model_name: Name of the model to get information for

    Returns:
        Model information dictionary or None if not found
    """
    try:
        result = await adapter.model_info(model_name)
        if result and isinstance(result, dict):
            logger.debug(f"Got info for model {model_name}")
            return result
        else:
            logger.warning(f"Unexpected response format from model_info: {result}")
            return None
    except Exception as e:
        logger.error(f"Error getting model info for {model_name}: {e}")
        return None


async def ensure_model_available(adapter, model_name: str) -> bool:
    """Ensure that a model is available, pulling it if necessary.

    Args:
        adapter: The Ollama adapter to use
        model_name: Name of the model to ensure is available

    Returns:
        True if the model is available, False otherwise
    """
    # First check if the model is already available
    models = await list_models(adapter)
    for model in models:
        if model.get("name") == model_name:
            logger.debug(f"Model {model_name} is already available")
            return True

    # If not, try to pull it
    logger.info(f"Model {model_name} not found, attempting to pull")
    try:
        result = await adapter.pull_model(model_name)
        if result and isinstance(result, dict) and result.get("status") == "success":
            logger.info(f"Successfully pulled model {model_name}")
            return True
        else:
            logger.warning(f"Failed to pull model {model_name}: {result}")
            return False
    except Exception as e:
        logger.error(f"Error pulling model {model_name}: {e}")
        return False


async def validate_model_config(adapter, config: OllamaConfig) -> Dict[str, Any]:
    """Validate the model configuration and ensure the model is available.

    Args:
        adapter: The Ollama adapter to use
        config: Ollama configuration

    Returns:
        Dictionary with validation results
    """
    result = {"valid": False, "model": config.model, "available": False, "error": None}

    try:
        # Check if Ollama is available
        is_available = await adapter.is_available()
        if not is_available:
            result["error"] = "Ollama service is not available"
            return result

        # Check if the model is available
        model_available = await ensure_model_available(adapter, config.model)
        result["available"] = model_available

        if not model_available:
            result["error"] = (
                f"Model {config.model} is not available and could not be pulled"
            )
            return result

        # Get model info
        model_info = await get_model_info(adapter, config.model)
        if model_info:
            result["info"] = model_info

        # All checks passed
        result["valid"] = True
        return result

    except Exception as e:
        logger.error(f"Error validating model configuration: {e}")
        result["error"] = str(e)
        return result
