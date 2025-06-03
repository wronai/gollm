"""
Model management module for Ollama adapter.

This module handles all model-related operations including:
- Model discovery and listing
- Model information retrieval
- Model downloading and management
- Model selection and configuration
"""

from .info import ModelInfo
from .manager import ModelManager

__all__ = ["ModelManager", "ModelInfo"]
