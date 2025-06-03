"""OpenAI LLM Provider implementation for goLLM."""

import logging
import os
from typing import Any, Dict, List, Optional

import openai

from ..base import BaseLLMProvider

logger = logging.getLogger("gollm.openai.provider")


class OpenAILlmProvider(BaseLLMProvider):
    """LLM Provider for OpenAI's API."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the OpenAI provider.

        Args:
            config: Configuration dictionary with OpenAI settings
        """
        super().__init__(config)
        self.api_key = config.get("api_key", os.environ.get("OPENAI_API_KEY"))
        self.model = config.get("model", "gpt-4")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 2000)

        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        openai.api_key = self.api_key

        # Configure API base if provided (for Azure or custom endpoints)
        if "api_base" in config:
            openai.api_base = config["api_base"]

        if "api_type" in config:
            openai.api_type = config["api_type"]

        if "api_version" in config:
            openai.api_version = config["api_version"]

        logger.info(f"Initialized OpenAI provider with model: {self.model}")

    async def generate_response(
        self, prompt: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a response using the OpenAI API.

        Args:
            prompt: The prompt to generate a response for
            context: Additional context for the generation

        Returns:
            Dictionary containing the generated response and metadata
        """
        try:
            messages = [{"role": "user", "content": prompt}]

            # Add conversation history if provided
            if context and "messages" in context:
                messages = context["messages"] + messages

            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **context.get("generation_params", {}) if context else {},
            )

            return {
                "success": True,
                "generated_text": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            }

        except Exception as e:
            logger.exception("Failed to generate response with OpenAI")
            return {"success": False, "error": f"OpenAI API error: {str(e)}"}

    async def health_check(self) -> Dict[str, Any]:
        """Check if the OpenAI API is available.

        Returns:
            Dictionary with health check results
        """
        try:
            await openai.Model.aretrieve(self.model)
            return {"status": True, "model_available": True, "error": None}
        except Exception as e:
            return {"status": False, "model_available": False, "error": str(e)}

    def is_available(self) -> bool:
        """Check if the OpenAI API is available."""
        try:
            import asyncio

            return asyncio.get_event_loop().run_until_complete(self.health_check())[
                "status"
            ]
        except Exception:
            return False
