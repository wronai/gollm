"""Ollama API operations module."""

import logging
from typing import Any, Dict, List, Optional

from .client import OllamaHttpClient

logger = logging.getLogger("gollm.ollama.http.operations")


class OllamaOperations:
    """Operations for interacting with the Ollama API."""

    def __init__(self, client: OllamaHttpClient):
        """Initialize with an HTTP client.

        Args:
            client: Configured HTTP client
        """
        self.client = client

    async def generate(
        self, prompt: str, model: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """Generate text using the completion endpoint.

        Args:
            prompt: The prompt to generate from
            model: Model to use (defaults to config model)
            **kwargs: Additional generation parameters
                - temperature: Controls randomness (0.0 to 1.0)
                - max_tokens/num_predict: Maximum tokens to generate
                - top_p: Nucleus sampling parameter (0.0 to 1.0)
                - top_k: Limit next token selection to top K (1-100)
                - repeat_penalty: Penalty for repeated tokens (1.0+)
                - stop: List of strings to stop generation
                - stream: Whether to stream the response

        Returns:
            Dictionary containing the generated text and metadata
        """
        # Extract options from kwargs
        options = kwargs.pop("options", {})

        # Set default options if not provided
        if "temperature" not in options:
            options["temperature"] = self.client.config.temperature
        if "num_predict" not in options and "max_tokens" in kwargs:
            options["num_predict"] = kwargs.pop("max_tokens")
        elif "num_predict" not in options:
            options["num_predict"] = self.client.config.max_tokens

        # Add any other generation parameters to options
        for param in ["top_p", "top_k", "repeat_penalty", "stop"]:
            if param in kwargs and param not in options:
                options[param] = kwargs.pop(param)

        data = {
            "model": model or self.client.config.model,
            "prompt": prompt,
            "options": options,
            **kwargs,  # Include any remaining kwargs at the top level
        }

        logger.debug(f"Sending generate request with data: {data}")
        import time

        start_time = time.time()
        result = await self.client._request("POST", "/api/generate", json=data)
        duration = time.time() - start_time

        # Add performance metrics
        if "success" not in result:
            result["success"] = "error" not in result
        result["duration_seconds"] = duration

        return result

    async def chat(
        self, messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """Generate chat completion.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            model: Model to use for generation (defaults to config model)
            **kwargs: Additional generation parameters
                - options: Dictionary of model options
                - stream: Whether to stream the response
                - format: Response format (e.g., 'json')
                - Any other Ollama API parameters

        Returns:
            Dictionary containing the generated response and metadata
        """
        # Extract options from kwargs
        options = kwargs.pop("options", {})

        # Set default options if not provided
        if "temperature" not in options:
            options["temperature"] = self.client.config.temperature

        # Handle max_tokens/num_predict
        if "num_predict" not in options and "max_tokens" in kwargs:
            options["num_predict"] = kwargs.pop("max_tokens")
        elif "num_predict" not in options:
            options["num_predict"] = self.client.config.max_tokens

        # Add any other generation parameters to options
        for param in ["top_p", "top_k", "repeat_penalty", "stop"]:
            if param in kwargs and param not in options:
                options[param] = kwargs.pop(param)

        data = {
            "model": model or self.client.config.model,
            "messages": messages,
            "options": options,
            **kwargs,  # Include any remaining kwargs at the top level
        }

        logger.debug(f"Sending chat request with data: {data}")
        import time

        start_time = time.time()
        result = await self.client._request("POST", "/api/chat", json=data)
        duration = time.time() - start_time

        # Add performance metrics
        if "success" not in result:
            result["success"] = "error" not in result
        result["duration_seconds"] = duration

        return result

    async def pull_model(self, model_name: str) -> Dict[str, Any]:
        """Pull a model from Ollama registry.

        Args:
            model_name: Name of the model to pull

        Returns:
            Dictionary containing the pull status
        """
        data = {"name": model_name}
        return await self.client._request("POST", "/api/pull", json=data)

    async def model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a model.

        Args:
            model_name: Name of the model

        Returns:
            Dictionary containing model information
        """
        data = {"name": model_name}
        return await self.client._request("POST", "/api/show", json=data)
