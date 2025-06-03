"""Model availability utilities for Ollama API requests."""

import logging
from typing import Any, Dict

logger = logging.getLogger("gollm.ollama.models")


async def ensure_model_available(adapter, model: str) -> tuple[bool, str]:
    """Ensure the specified model is available.

    Args:
        adapter: The adapter to use for the API request
        model: The model to check availability for

    Returns:
        tuple[bool, str]: A tuple containing (is_available, error_message)
            where is_available is True if the model is available, False otherwise
            and error_message is an empty string if available, or an error message if not
    """
    try:
        result = await adapter.list_models()
        available_models = [model_info["name"] for model_info in result.get("models", [])]
        model_available = model in available_models

        if not model_available:
            error_message = f"Model '{model}' not found in available models. Available models: {', '.join(available_models)}"
            logger.warning(error_message)
            return False, error_message

        return True, ""

    except Exception as e:
        error_message = f"Failed to list models: {str(e)}"
        logger.error(error_message)
        return False, error_message
