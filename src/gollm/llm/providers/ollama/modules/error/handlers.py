"""Error handling utilities for Ollama API requests."""

import logging
from typing import Dict, Any

logger = logging.getLogger("gollm.ollama.error")


def handle_timeout_error(timeout: int, model: str) -> Dict[str, Any]:
    """Handle timeout errors during API requests.
    
    Args:
        timeout: The timeout value in seconds that was exceeded
        model: The model being used when the timeout occurred
        
    Returns:
        Dict with error information and a meaningful error message
    """
    error_message = f"Request to model '{model}' timed out after {timeout} seconds. "
    error_message += "The model may be overloaded or the request may be too complex."
    
    logger.error(f"Timeout error: {error_message}")
    
    return {
        "success": False,
        "error": "Timeout",
        "error_message": error_message,
        "generated_text": f"ERROR: {error_message}",
        "model": model,
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
        },
    }


def handle_api_error(error: Exception, model: str) -> Dict[str, Any]:
    """Handle API errors during requests.
    
    Args:
        error: The exception that occurred
        model: The model being used when the error occurred
        
    Returns:
        Dict with error information and a meaningful error message
    """
    error_message = f"Error while communicating with model '{model}': {str(error)}"
    
    logger.error(f"API error: {error_message}")
    
    return {
        "success": False,
        "error": "APIError",
        "error_message": error_message,
        "generated_text": f"ERROR: {error_message}",
        "model": model,
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
        },
    }
