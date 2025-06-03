"""
Health check and status monitoring module for Ollama adapter.

This module handles all health and status monitoring operations including:
- API availability checks
- Service status monitoring
- Performance metrics collection
- Error reporting and diagnostics
"""

from .diagnostics import DiagnosticsCollector
from .monitor import HealthMonitor

__all__ = ["HealthMonitor", "DiagnosticsCollector"]
