"""Model management module for Ollama adapter."""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("gollm.ollama.model")


class ModelManager:
    """Manages Ollama models including listing, pulling, and information retrieval."""

    def __init__(self, client):
        """Initialize the model manager.

        Args:
            client: HTTP client for making API requests
        """
        self.client = client
        self.models_cache = {}
        self.last_refresh_time = 0
        self.cache_ttl = 300  # Cache time-to-live in seconds (5 minutes)
        self.show_metadata = getattr(self.client.config, "show_metadata", False)

    async def list_models(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """List available models.

        Args:
            force_refresh: If True, force a refresh of the cache

        Returns:
            List of model information dictionaries
        """
        current_time = time.time()

        # Use cached result if available and not expired
        if (
            not force_refresh
            and self.models_cache
            and (current_time - self.last_refresh_time) < self.cache_ttl
        ):
            logger.debug("Using cached model list")
            return self.models_cache.get("models", [])

        # Fetch models from API
        try:
            logger.info("Fetching model list from Ollama API")
            result = await self.client._request("GET", "/api/tags")

            if self.show_metadata:
                logger.info(f"Found {len(result.get('models', []))} models")
                for model in result.get("models", []):
                    logger.info(
                        f"Model: {model.get('name', 'unknown')} - Size: {model.get('size', 0)} bytes"
                    )

            # Update cache
            self.models_cache = result
            self.last_refresh_time = current_time

            return result.get("models", [])

        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return []

    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific model.

        Args:
            model_name: Name of the model

        Returns:
            Dictionary containing model information
        """
        try:
            logger.info(f"Fetching information for model: {model_name}")
            data = {"name": model_name}
            result = await self.client._request("POST", "/api/show", json=data)

            if self.show_metadata and result:
                logger.info(f"Model info for {model_name}: {result}")

            return result

        except Exception as e:
            logger.error(f"Error getting model info for {model_name}: {str(e)}")
            return {"error": str(e)}

    async def pull_model(self, model_name: str) -> Dict[str, Any]:
        """Pull a model from Ollama registry.

        Args:
            model_name: Name of the model to pull

        Returns:
            Dictionary containing the pull status
        """
        try:
            logger.info(f"Pulling model: {model_name}")
            data = {"name": model_name}
            result = await self.client._request("POST", "/api/pull", json=data)

            # Invalidate cache after pulling a new model
            self.last_refresh_time = 0

            return result

        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {str(e)}")
            return {"error": str(e)}

    async def get_model_parameters(self, model_name: str) -> Dict[str, Any]:
        """Get recommended parameters for a specific model.

        Args:
            model_name: Name of the model

        Returns:
            Dictionary containing recommended parameters
        """
        # Get model info first
        model_info = await self.get_model_info(model_name)

        # Extract or determine parameters based on model info
        parameters = {
            "model": model_name,
            "temperature": 0.7,  # Default temperature
            "top_p": 0.9,  # Default top_p
            "top_k": 40,  # Default top_k
        }

        # Adjust parameters based on model size/type if available
        if "parameters" in model_info:
            model_params = model_info["parameters"]

            # Use model-specific parameters if available
            parameters.update(
                {
                    k: v
                    for k, v in model_params.items()
                    if k in ["temperature", "top_p", "top_k", "repeat_penalty"]
                }
            )

        # Adjust based on model name heuristics
        model_name_lower = model_name.lower()

        # Coding models often benefit from lower temperature
        if any(
            code_model in model_name_lower
            for code_model in ["code", "codellama", "starcoder", "wizard-code"]
        ):
            parameters["temperature"] = min(parameters.get("temperature", 0.7), 0.2)

        # Instruct models may need different settings
        if "instruct" in model_name_lower:
            parameters["instruct"] = True

        logger.debug(f"Recommended parameters for {model_name}: {parameters}")
        return parameters

    async def find_best_model(
        self, task_type: str, size_preference: str = "medium"
    ) -> Tuple[str, Dict[str, Any]]:
        """Find the best available model for a specific task.

        Args:
            task_type: Type of task (e.g., 'code', 'chat', 'completion')
            size_preference: Preferred model size ('small', 'medium', 'large')

        Returns:
            Tuple of (model_name, parameters)
        """
        # Get available models
        models = await self.list_models()

        # Define scoring criteria based on task type
        task_keywords = {
            "code": ["code", "starcoder", "codellama", "wizard-code"],
            "chat": ["chat", "instruct", "vicuna", "llama", "mistral"],
            "completion": ["completion", "llama", "mistral", "falcon"],
        }

        # Size preference mapping
        size_mapping = {
            "small": ["3b", "7b", "1.3b", "2b", "6b"],
            "medium": ["7b", "13b", "14b", "16b"],
            "large": ["30b", "34b", "40b", "65b", "70b"],
        }

        # Score each model
        scored_models = []
        for model in models:
            model_name = model.get("name", "").lower()
            score = 0

            # Score based on task type
            for keyword in task_keywords.get(task_type, []):
                if keyword in model_name:
                    score += 10

            # Score based on size preference
            for size in size_mapping.get(size_preference, []):
                if size in model_name:
                    score += 5

            # Prefer newer models
            if "2" in model_name:
                score += 3

            scored_models.append((model.get("name"), score))

        # Sort by score (descending)
        scored_models.sort(key=lambda x: x[1], reverse=True)

        if not scored_models:
            # No models found, return default
            logger.warning(
                f"No suitable models found for {task_type} task, using default"
            )
            return self.client.config.model, {}

        # Get the best model
        best_model = scored_models[0][0]
        logger.info(f"Selected best model for {task_type} task: {best_model}")

        # Get parameters for the selected model
        parameters = await self.get_model_parameters(best_model)

        return best_model, parameters
