"""
Validation utilities for Ollama integration.

This module provides functions for validating configuration,
model names, and other inputs to the Ollama integration.
"""

import re
from typing import Any, Dict, Optional, Tuple

from ...exceptions import ConfigurationError, ValidationError

# Regex for valid model names (alphanumeric, colon, hyphen, underscore, dot)
MODEL_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9:_\-\.]+$')

# Maximum lengths for various fields
MAX_MODEL_NAME_LENGTH = 128
MAX_PROMPT_LENGTH = 10000  # Adjust based on model context size


def validate_model_name(model_name: str) -> Tuple[bool, str]:
    """Validate a model name.
    
    Args:
        model_name: The model name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not model_name:
        return False, "Model name cannot be empty"
        
    if len(model_name) > MAX_MODEL_NAME_LENGTH:
        return False, f"Model name exceeds maximum length of {MAX_MODEL_NAME_LENGTH} characters"
        
    if not MODEL_NAME_PATTERN.match(model_name):
        return False, (
            "Model name can only contain alphanumeric characters, ",
            "colons, hyphens, underscores, and dots"
        )
        
    return True, ""


def validate_config(config: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate a configuration dictionary.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(config, dict):
        return False, "Configuration must be a dictionary"
        
    # Check required fields
    required_fields = ['base_url', 'model']
    for field in required_fields:
        if field not in config:
            return False, f"Missing required field: {field}"
            
    # Validate base URL
    base_url = config.get('base_url', '').strip()
    if not base_url:
        return False, "base_url cannot be empty"
    if not (base_url.startswith('http://') or base_url.startswith('https://')):
        return False, "base_url must start with http:// or https://"
        
    # Validate model name
    model_name = config.get('model', '').strip()
    is_valid, error = validate_model_name(model_name)
    if not is_valid:
        return False, f"Invalid model name: {error}"
        
    # Validate timeout
    timeout = config.get('timeout', 60)
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        return False, "timeout must be a positive number"
        
    # Validate max_tokens
    max_tokens = config.get('max_tokens', 2000)
    if not isinstance(max_tokens, int) or max_tokens <= 0:
        return False, "max_tokens must be a positive integer"
        
    # Validate temperature
    temperature = config.get('temperature', 0.7)
    if not isinstance(temperature, (int, float)) or not (0 <= temperature <= 2.0):
        return False, "temperature must be a number between 0 and 2.0"
        
    return True, ""


def validate_prompt(prompt: str) -> Tuple[bool, str]:
    """Validate a prompt before sending to the API.
    
    Args:
        prompt: The prompt to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not prompt or not prompt.strip():
        return False, "Prompt cannot be empty"
        
    if len(prompt) > MAX_PROMPT_LENGTH:
        return False, f"Prompt exceeds maximum length of {MAX_PROMPT_LENGTH} characters"
        
    return True, ""


def validate_api_response(response: Dict[str, Any]) -> bool:
    """Validate an API response from Ollama.
    
    Args:
        response: The API response to validate
        
    Returns:
        True if the response is valid, False otherwise
        
    Note:
        This is a basic validation. Different endpoints may have different
        response structures that need to be validated specifically.
    """
    if not isinstance(response, dict):
        return False
        
    # Check for error in response
    if 'error' in response:
        return False
        
    # For generation responses
    if 'response' in response and not isinstance(response.get('response'), str):
        return False
        
    # For model listing
    if 'models' in response and not isinstance(response.get('models'), list):
        return False
        
    return True


def validate_config_dict(config: Dict[str, Any]) -> None:
    """Validate a configuration dictionary and raise an exception if invalid.
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        ConfigurationError: If the configuration is invalid
    """
    is_valid, error = validate_config(config)
    if not is_valid:
        raise ConfigurationError(f"Invalid configuration: {error}")


def validate_model(model_name: str) -> None:
    """Validate a model name and raise an exception if invalid.
    
    Args:
        model_name: The model name to validate
        
    Raises:
        ValidationError: If the model name is invalid
    """
    is_valid, error = validate_model_name(model_name)
    if not is_valid:
        raise ValidationError(f"Invalid model name: {error}")
