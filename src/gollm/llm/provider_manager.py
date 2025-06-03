"""Manager for handling multiple LLM providers with fallback support."""

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""

    name: str
    enabled: bool = True
    priority: int = 99
    config: Dict[str, Any] = None
    provider_class: Any = None


class LLMProviderManager:
    """Manages multiple LLM providers with fallback support."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration."""
        self.config = config
        self.providers: Dict[str, ProviderConfig] = {}
        self.fallback_order: List[str] = config.get("fallback_order", [])
        self.default_timeout: int = config.get("timeout", 10)
        self.max_retries: int = config.get("max_retries", 2)
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize all configured providers."""
        providers_config = self.config.get("providers", {})

        for provider_name, provider_config in providers_config.items():
            if not provider_config.get("enabled", False):
                continue

            # Resolve environment variables in config
            resolved_config = self._resolve_env_vars(provider_config)

            # Import provider class dynamically
            try:
                module_name = f"gollm.llm.{provider_name}_adapter"
                module = __import__(
                    module_name, fromnames=[f"{provider_name.capitalize()}LLMProvider"]
                )
                provider_class = getattr(
                    module, f"{provider_name.capitalize()}LLMProvider"
                )

                self.providers[provider_name] = ProviderConfig(
                    name=provider_name,
                    enabled=resolved_config.get("enabled", True),
                    priority=resolved_config.get("priority", 99),
                    config=resolved_config,
                    provider_class=provider_class,
                )

            except (ImportError, AttributeError) as e:
                logger.warning(f"Failed to initialize provider {provider_name}: {e}")
                continue

    def _resolve_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve environment variables in config values."""
        resolved = {}
        for key, value in config.items():
            if isinstance(value, str) and value.startswith("${") and "}" in value:
                # Handle ${VAR:-default} syntax
                var_part = value[2:].split("}")[0]
                if ":-" in var_part:
                    var_name, default = var_part.split(":-", 1)
                    resolved[key] = os.getenv(var_name, default)
                else:
                    resolved[key] = os.getenv(var_part, "")
            else:
                resolved[key] = value
        return resolved

    def get_provider_order(self) -> List[str]:
        """Get the order in which providers should be tried."""
        # Sort by explicit fallback order first, then by priority
        return sorted(
            [name for name in self.fallback_order if name in self.providers],
            key=lambda x: self.fallback_order.index(x),
        )

    async def get_response(
        self, prompt: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Get a response from the first available provider.

        Args:
            prompt: The prompt to send to the LLM
            context: Additional context for the generation

        Returns:
            Dictionary with the response or error information
        """
        provider_order = self.get_provider_order()
        last_error = None

        for provider_name in provider_order:
            provider_config = self.providers.get(provider_name)
            if not provider_config or not provider_config.enabled:
                continue

            logger.info(f"Trying provider: {provider_name}")

            try:
                provider = provider_config.provider_class(provider_config.config)
                response = await asyncio.wait_for(
                    provider.generate_response(prompt, context or {}),
                    timeout=provider_config.config.get("timeout", self.default_timeout),
                )

                if response.get("success", False):
                    return response

                last_error = response.get("error", "Unknown error")
                logger.warning(f"Provider {provider_name} failed: {last_error}")

            except asyncio.TimeoutError:
                last_error = f"Provider {provider_name} timed out"
                logger.warning(last_error)
            except Exception as e:
                last_error = str(e)
                logger.error(f"Error with provider {provider_name}: {e}", exc_info=True)

        return {
            "success": False,
            "error": f"All providers failed. Last error: {last_error}",
            "generated_code": "",
            "explanation": "Failed to get a response from any provider",
            "provider_info": {
                "tried_providers": provider_order,
                "last_error": last_error,
            },
        }
