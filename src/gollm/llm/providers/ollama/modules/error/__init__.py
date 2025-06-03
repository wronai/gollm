"""Error handling module for Ollama API requests."""

from .handlers import handle_timeout_error, handle_api_error

__all__ = ["handle_timeout_error", "handle_api_error"]
