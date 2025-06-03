"""Error handling utilities for Ollama API requests."""

import logging
import traceback
from typing import Dict, Any, Optional

logger = logging.getLogger("gollm.ollama.error")


def handle_timeout_error(error: Exception, model: str, prompt: str) -> Dict[str, Any]:
    """Handle timeout errors from the Ollama API.
    
    Args:
        error: The timeout error
        model: The model that was used
        prompt: The prompt that was sent
        
    Returns:
        Error response dictionary
    """
    logger.error(f"Timeout error with model {model}: {str(error)}")
    logger.debug(f"Timeout occurred with prompt: {prompt[:100]}...")
    
    # Get detailed error information
    error_details = {
        "error_type": "TimeoutError",
        "error_message": str(error),
        "traceback": traceback.format_exc(),
    }
    
    return {
        "success": False,
        "error": "TimeoutError",
        "error_details": error_details,
        "generated_text": f"ERROR: Request to Ollama API timed out. The model {model} may be overloaded or the request was too complex.",
        "model": model,
        "usage": {
            "prompt_tokens": len(prompt.split()),
            "completion_tokens": 0,
        }
    }


def handle_api_error(error: Exception, model: str, prompt: str) -> Dict[str, Any]:
    """Handle general API errors from the Ollama API.
    
    Args:
        error: The API error
        model: The model that was used
        prompt: The prompt that was sent
        
    Returns:
        Error response dictionary
    """
    error_type = type(error).__name__
    error_message = str(error)
    
    logger.error(f"{error_type} with model {model}: {error_message}")
    logger.debug(f"Error occurred with prompt: {prompt[:100]}...")
    logger.debug(f"Error traceback: {traceback.format_exc()}")
    
    # Get detailed error information
    error_details = {
        "error_type": error_type,
        "error_message": error_message,
        "traceback": traceback.format_exc(),
    }
    
    # Handle specific error types
    if "connection refused" in error_message.lower():
        error_type = "ConnectionError"
        user_message = f"ERROR: Could not connect to Ollama API. Please ensure Ollama is running and accessible at the configured URL."
    elif "not found" in error_message.lower() or "404" in error_message:
        error_type = "NotFoundError"
        user_message = f"ERROR: Resource not found. The model {model} may not exist or the API endpoint is incorrect."
    elif "unauthorized" in error_message.lower() or "401" in error_message:
        error_type = "AuthenticationError"
        user_message = f"ERROR: Authentication failed with the Ollama API. Please check your credentials."
    elif "bad request" in error_message.lower() or "400" in error_message:
        error_type = "BadRequestError"
        user_message = f"ERROR: Bad request to Ollama API. The request parameters may be invalid."
    elif "too many requests" in error_message.lower() or "429" in error_message:
        error_type = "RateLimitError"
        user_message = f"ERROR: Rate limit exceeded for Ollama API. Please try again later."
    elif "internal server error" in error_message.lower() or "500" in error_message:
        error_type = "ServerError"
        user_message = f"ERROR: Ollama API server error. The server may be overloaded or experiencing issues."
    else:
        user_message = f"ERROR: An error occurred while communicating with the Ollama API: {error_message}"
    
    return {
        "success": False,
        "error": error_type,
        "error_details": error_details,
        "generated_text": user_message,
        "model": model,
        "usage": {
            "prompt_tokens": len(prompt.split()),
            "completion_tokens": 0,
        }
    }


def handle_empty_response_error(model: str, prompt: str, response: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Handle empty response errors from the Ollama API.
    
    Args:
        model: The model that was used
        prompt: The prompt that was sent
        response: The original response dictionary, if available
        
    Returns:
        Error response dictionary
    """
    logger.error(f"Empty response from model {model}")
    logger.debug(f"Empty response occurred with prompt: {prompt[:100]}...")
    
    if response:
        logger.debug(f"Original response: {response}")
    
    # Get detailed error information
    error_details = {
        "error_type": "EmptyResponse",
        "error_message": "The model returned an empty response",
        "original_response": response,
    }
    
    return {
        "success": False,
        "error": "EmptyResponse",
        "error_details": error_details,
        "generated_text": f"ERROR: The model {model} returned an empty response. Please try again with a different prompt or model.",
        "model": model,
        "usage": {
            "prompt_tokens": len(prompt.split()),
            "completion_tokens": 0,
        }
    }


def handle_model_not_available_error(model: str, error_message: str) -> Dict[str, Any]:
    """Handle model not available errors from the Ollama API.
    
    Args:
        model: The model that was requested
        error_message: The error message from the model availability check
        
    Returns:
        Error response dictionary
    """
    logger.error(f"Model {model} is not available: {error_message}")
    
    # Get detailed error information
    error_details = {
        "error_type": "ModelNotAvailable",
        "error_message": error_message,
        "model": model,
    }
    
    return {
        "success": False,
        "error": "ModelNotAvailable",
        "error_details": error_details,
        "generated_text": f"ERROR: Model {model} is not available. {error_message}",
        "model": model,
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
        }
    }
