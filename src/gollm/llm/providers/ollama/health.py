"""Health check and status monitoring utilities for Ollama provider."""

import asyncio
import logging
import time
from typing import Any, Dict, Optional

from .config import OllamaConfig
from .models import get_model_info, list_models

logger = logging.getLogger("gollm.ollama.health")


async def check_service_availability(adapter) -> Dict[str, Any]:
    """Check if the Ollama service is available.

    Args:
        adapter: The Ollama adapter to use

    Returns:
        Dictionary with availability status and details
    """
    result = {"available": False, "response_time_ms": None, "error": None}

    try:
        start_time = time.time()
        is_available = await adapter.is_available()
        end_time = time.time()

        result["available"] = is_available
        result["response_time_ms"] = round((end_time - start_time) * 1000, 2)

        if not is_available:
            result["error"] = "Service responded but reported as unavailable"

        return result
    except Exception as e:
        logger.error(f"Error checking service availability: {e}")
        result["error"] = str(e)
        return result


async def check_model_availability(adapter, model_name: str) -> Dict[str, Any]:
    """Check if a specific model is available.

    Args:
        adapter: The Ollama adapter to use
        model_name: Name of the model to check

    Returns:
        Dictionary with model availability status and details
    """
    result = {"model": model_name, "available": False, "info": None, "error": None}

    try:
        # First check if the model is in the list of available models
        models = await list_models(adapter)
        model_found = any(model.get("name") == model_name for model in models)

        if model_found:
            result["available"] = True
            # Get detailed model info
            model_info = await get_model_info(adapter, model_name)
            if model_info:
                result["info"] = model_info
        else:
            result["error"] = f"Model {model_name} not found in available models"

        return result
    except Exception as e:
        logger.error(f"Error checking model availability: {e}")
        result["error"] = str(e)
        return result


async def perform_basic_generation_test(adapter, model_name: str) -> Dict[str, Any]:
    """Perform a basic generation test to verify model functionality.

    Args:
        adapter: The Ollama adapter to use
        model_name: Name of the model to test

    Returns:
        Dictionary with test results
    """
    result = {
        "success": False,
        "response_time_ms": None,
        "error": None,
        "sample_output": None,
    }

    try:
        # Simple test prompt
        test_prompt = "Return the string 'OK' if you can process this message."

        start_time = time.time()
        response = await adapter.generate(
            prompt=test_prompt, model=model_name, temperature=0.1, max_tokens=10
        )
        end_time = time.time()

        result["response_time_ms"] = round((end_time - start_time) * 1000, 2)

        if response and "response" in response:
            result["success"] = True
            result["sample_output"] = response["response"][:50]  # Limit sample size
        else:
            result["error"] = "No valid response received from model"

        return result
    except Exception as e:
        logger.error(f"Error performing generation test: {e}")
        result["error"] = str(e)
        return result


async def comprehensive_health_check(adapter, config: OllamaConfig) -> Dict[str, Any]:
    """Perform a comprehensive health check of the Ollama service and configured model.

    Args:
        adapter: The Ollama adapter to use
        config: Ollama configuration

    Returns:
        Dictionary with detailed health check results
    """
    result = {
        "timestamp": time.time(),
        "status": False,  # Overall health status
        "config": {
            "base_url": config.base_url,
            "model": config.model,
            "timeout": config.timeout,
        },
        "service": {},
        "model": {},
        "generation_test": {},
    }

    # Check service availability
    result["service"] = await check_service_availability(adapter)

    # If service is available, check model
    if result["service"]["available"]:
        result["model"] = await check_model_availability(adapter, config.model)

        # If model is available, perform generation test
        if result["model"]["available"]:
            result["generation_test"] = await perform_basic_generation_test(
                adapter, config.model
            )

            # Set overall status based on generation test
            result["status"] = result["generation_test"]["success"]

    # Log summary
    if result["status"]:
        logger.info(f"Health check passed for {config.model} at {config.base_url}")
    else:
        logger.warning(f"Health check failed for {config.model} at {config.base_url}")

    return result
