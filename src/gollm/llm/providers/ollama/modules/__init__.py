"""
Modular components for the Ollama adapter.

This package contains modular components for the Ollama adapter, including:
- Prompt formatting and processing
- Health check and status monitoring
- Model management
"""

from .prompt import PromptFormatter, PromptLogger
from .health import HealthMonitor, DiagnosticsCollector
from .model import ModelManager, ModelInfo

__all__ = [
    'PromptFormatter', 
    'PromptLogger',
    'HealthMonitor', 
    'DiagnosticsCollector',
    'ModelManager', 
    'ModelInfo'
]
