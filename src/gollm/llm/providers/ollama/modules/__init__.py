"""
Modular components for the Ollama adapter.

This package contains modular components for the Ollama adapter, including:
- Prompt formatting and processing
- Health check and status monitoring
- Model management
"""

from .health import DiagnosticsCollector, HealthMonitor
from .model import ModelInfo, ModelManager
from .prompt import PromptFormatter, PromptLogger

__all__ = [
    "PromptFormatter",
    "PromptLogger",
    "HealthMonitor",
    "DiagnosticsCollector",
    "ModelManager",
    "ModelInfo",
]
