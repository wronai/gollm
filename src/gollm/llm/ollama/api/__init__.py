"""
API communication for Ollama integration.

This module handles all HTTP communication with the Ollama API,
including request/response handling and error management.
"""

from .client import OllamaAPIClient
from .endpoints import (
    get_models_endpoint,
    get_generate_endpoint,
    get_chat_endpoint
)

__all__ = [
    'OllamaAPIClient',
    'get_models_endpoint',
    'get_generate_endpoint',
    'get_chat_endpoint'
]
