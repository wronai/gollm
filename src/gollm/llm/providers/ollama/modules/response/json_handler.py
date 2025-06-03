"""JSON response handling for Ollama API responses.

This module provides utilities for handling JSON responses from the Ollama API,
particularly for cases where the model returns JSON instead of plain text.
"""

import json
import logging
import re
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("gollm.ollama.response.json_handler")

def extract_code_from_json(response_text: str) -> Tuple[bool, str]:
    """
    Attempts to extract code from a JSON response.
    
    Args:
        response_text: The raw response text that might contain JSON
        
    Returns:
        Tuple of (is_json, extracted_code)
        - is_json: True if the response was JSON and we extracted code
        - extracted_code: The extracted code or the original text if not JSON
    """
    if not response_text or not response_text.strip():
        logger.warning("Empty response received, cannot extract code from JSON")
        return False, response_text
    
    # Check if the response looks like JSON
    if not (response_text.strip().startswith('{') and response_text.strip().endswith('}')):
        return False, response_text
    
    try:
        # Try to parse as JSON
        json_data = json.loads(response_text)
        
        # Look for common code fields in the JSON
        code_fields = ['code', 'source', 'implementation', 'solution', 'program', 'snippet']
        
        for field in code_fields:
            if field in json_data and isinstance(json_data[field], str) and json_data[field].strip():
                logger.info(f"Extracted code from JSON field: {field}")
                return True, json_data[field]
        
        # If no direct code field, look for a field that might contain code blocks
        for key, value in json_data.items():
            if isinstance(value, str) and '```' in value:
                # Extract code blocks from markdown
                code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', value, re.DOTALL)
                if code_blocks:
                    logger.info(f"Extracted code blocks from JSON field: {key}")
                    return True, '\n\n'.join(code_blocks)
        
        # If we still don't have code but have a single string field, use that
        if len(json_data) == 1 and isinstance(list(json_data.values())[0], str):
            logger.info("Using single string field from JSON response")
            return True, list(json_data.values())[0]
        
        # If we have an 'error' field, log it but return the original
        if 'error' in json_data and isinstance(json_data['error'], str):
            logger.warning(f"JSON response contains error: {json_data['error']}")
        
        # If we couldn't extract anything useful, convert the JSON back to a string
        logger.warning("Could not extract code from JSON response, returning formatted JSON")
        return True, json.dumps(json_data, indent=2)
        
    except json.JSONDecodeError:
        # Not valid JSON, return original
        return False, response_text

def is_error_json(response_text: str) -> Tuple[bool, Optional[str]]:
    """
    Checks if the response is a JSON error message.
    
    Args:
        response_text: The raw response text
        
    Returns:
        Tuple of (is_error_json, error_message)
        - is_error_json: True if the response is a JSON error
        - error_message: The extracted error message or None
    """
    if not response_text or not response_text.strip():
        return False, None
    
    # Check if the response looks like JSON
    if not (response_text.strip().startswith('{') and response_text.strip().endswith('}')):
        return False, None
    
    try:
        json_data = json.loads(response_text)
        
        # Check for common error fields
        error_fields = ['error', 'errors', 'message', 'errorMessage', 'error_message']
        
        for field in error_fields:
            if field in json_data and isinstance(json_data[field], str) and json_data[field].strip():
                logger.warning(f"JSON error response detected: {json_data[field]}")
                return True, json_data[field]
        
        return False, None
        
    except json.JSONDecodeError:
        return False, None
