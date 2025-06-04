"""
API endpoint definitions for Ollama service.

This module contains functions that return the API endpoints
for various Ollama operations.
"""

from typing import Optional


def get_models_endpoint() -> str:
    """Get the endpoint for listing available models.
    
    Returns:
        API endpoint path for listing models
    """
    return "/api/tags"


def get_generate_endpoint() -> str:
    """Get the endpoint for text generation.
    
    Returns:
        API endpoint path for text generation
    """
    return "/api/generate"


def get_chat_endpoint() -> str:
    """Get the endpoint for chat completions.
    
    Returns:
        API endpoint path for chat completions
    """
    return "/api/chat"


def get_model_info_endpoint(model: str) -> str:
    """Get the endpoint for model information.
    
    Args:
        model: Name of the model
        
    Returns:
        API endpoint path for model information
    """
    return f"/api/show"


def get_pull_model_endpoint() -> str:
    """Get the endpoint for pulling a model.
    
    Returns:
        API endpoint path for pulling models
    """
    return "/api/pull"


def get_delete_model_endpoint() -> str:
    """Get the endpoint for deleting a model.
    
    Returns:
        API endpoint path for deleting models
    """
    return "/api/delete"


def get_embeddings_endpoint() -> str:
    """Get the endpoint for generating embeddings.
    
    Returns:
        API endpoint path for generating embeddings
    """
    return "/api/embeddings"


def get_health_check_endpoint() -> str:
    """Get the endpoint for health checks.
    
    Returns:
        API endpoint path for health checks
    """
    return "/api/health"


def get_version_endpoint() -> str:
    """Get the endpoint for version information.
    
    Returns:
        API endpoint path for version information
    """
    return "/api/version"
