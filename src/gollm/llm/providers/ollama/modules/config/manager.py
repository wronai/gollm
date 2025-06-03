"""Configuration manager module for Ollama adapter."""

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger("gollm.ollama.config")


@dataclass
class OllamaConfig:
    """Configuration for Ollama API."""

    base_url: str = "http://localhost:11434"
    model: str = "codellama:7b"
    timeout: int = 60
    max_tokens: int = 4000
    temperature: float = 0.1
    use_chat: bool = True
    show_prompt: bool = False
    show_response: bool = False
    show_metadata: bool = False
    adaptive_timeout: bool = True
    adapter_type: str = "http"  # Options: "http", "grpc", "modular"

    def get_adjusted_timeout(self, prompt_length: int) -> int:
        """Calculate an adaptive timeout based on prompt length.

        Args:
            prompt_length: Length of the prompt in characters

        Returns:
            Adjusted timeout in seconds
        """
        if not self.adaptive_timeout:
            return self.timeout

        # Base timeout plus additional time based on prompt length
        # Roughly 1 second per 500 characters
        additional_time = int(prompt_length / 500)
        return self.timeout + additional_time


class ConfigManager:
    """Manages configuration for the Ollama adapter."""

    def __init__(self):
        """Initialize the configuration manager."""
        self.default_config = OllamaConfig()

    def load_config(self, config_dict: Optional[Dict[str, Any]] = None) -> OllamaConfig:
        """Load and validate configuration.

        Args:
            config_dict: Optional dictionary with configuration values

        Returns:
            OllamaConfig instance
        """
        # Start with default config
        config = OllamaConfig()

        # Apply environment variables
        self._apply_env_vars(config)

        # Apply provided config dict if any
        if config_dict:
            self._apply_config_dict(config, config_dict)

        # Validate the configuration
        self._validate_config(config)

        logger.info(
            f"Loaded Ollama configuration: model={config.model}, base_url={config.base_url}"
        )
        return config

    def _apply_env_vars(self, config: OllamaConfig) -> None:
        """Apply environment variables to configuration.

        Args:
            config: Configuration to update
        """
        # Base URL
        if "OLLAMA_BASE_URL" in os.environ:
            config.base_url = os.environ["OLLAMA_BASE_URL"]

        # Model
        if "OLLAMA_MODEL" in os.environ:
            config.model = os.environ["OLLAMA_MODEL"]

        # Timeout
        if "OLLAMA_TIMEOUT" in os.environ:
            try:
                config.timeout = int(os.environ["OLLAMA_TIMEOUT"])
            except ValueError:
                logger.warning(
                    f"Invalid OLLAMA_TIMEOUT value: {os.environ['OLLAMA_TIMEOUT']}"
                )

        # Max tokens
        if "OLLAMA_MAX_TOKENS" in os.environ:
            try:
                config.max_tokens = int(os.environ["OLLAMA_MAX_TOKENS"])
            except ValueError:
                logger.warning(
                    f"Invalid OLLAMA_MAX_TOKENS value: {os.environ['OLLAMA_MAX_TOKENS']}"
                )

        # Temperature
        if "OLLAMA_TEMPERATURE" in os.environ:
            try:
                config.temperature = float(os.environ["OLLAMA_TEMPERATURE"])
            except ValueError:
                logger.warning(
                    f"Invalid OLLAMA_TEMPERATURE value: {os.environ['OLLAMA_TEMPERATURE']}"
                )

        # Use chat API
        if "OLLAMA_USE_CHAT" in os.environ:
            config.use_chat = os.environ["OLLAMA_USE_CHAT"].lower() in [
                "true",
                "1",
                "yes",
            ]

        # Adapter type (support both OLLAMA_ADAPTER_TYPE and GOLLM_ADAPTER_TYPE)
        if "GOLLM_ADAPTER_TYPE" in os.environ:
            adapter_type = os.environ["GOLLM_ADAPTER_TYPE"].lower()
            if adapter_type in ["http", "grpc", "modular"]:
                config.adapter_type = adapter_type
                logger.info(
                    f"Using adapter type from GOLLM_ADAPTER_TYPE: {adapter_type}"
                )
            else:
                logger.warning(f"Invalid GOLLM_ADAPTER_TYPE value: {adapter_type}")

        # OLLAMA_ADAPTER_TYPE takes precedence if both are set
        if "OLLAMA_ADAPTER_TYPE" in os.environ:
            adapter_type = os.environ["OLLAMA_ADAPTER_TYPE"].lower()
            if adapter_type in ["http", "grpc", "modular"]:
                config.adapter_type = adapter_type
                logger.info(
                    f"Using adapter type from OLLAMA_ADAPTER_TYPE: {adapter_type}"
                )
            else:
                logger.warning(f"Invalid OLLAMA_ADAPTER_TYPE value: {adapter_type}")

        # Adaptive timeout
        if "OLLAMA_ADAPTIVE_TIMEOUT" in os.environ:
            config.adaptive_timeout = os.environ["OLLAMA_ADAPTIVE_TIMEOUT"].lower() in [
                "true",
                "1",
                "yes",
            ]

    def _apply_config_dict(
        self, config: OllamaConfig, config_dict: Dict[str, Any]
    ) -> None:
        """Apply configuration from dictionary.

        Args:
            config: Configuration to update
            config_dict: Dictionary with configuration values
        """
        # Apply each key from the dictionary if it exists in the config
        for key, value in config_dict.items():
            if hasattr(config, key):
                setattr(config, key, value)
            else:
                logger.warning(f"Unknown configuration key: {key}")

    def _validate_config(self, config: OllamaConfig) -> None:
        """Validate configuration values.

        Args:
            config: Configuration to validate
        """
        # Validate base URL
        if not config.base_url.startswith(("http://", "https://")):
            logger.warning(f"Invalid base URL format: {config.base_url}")
            config.base_url = self.default_config.base_url

        # Validate temperature
        if not 0 <= config.temperature <= 1:
            logger.warning(
                f"Temperature must be between 0 and 1, got: {config.temperature}"
            )
            config.temperature = self.default_config.temperature

        # Validate timeout
        if config.timeout <= 0:
            logger.warning(f"Timeout must be positive, got: {config.timeout}")
            config.timeout = self.default_config.timeout

        # Validate max tokens
        if config.max_tokens <= 0:
            logger.warning(f"Max tokens must be positive, got: {config.max_tokens}")
            config.max_tokens = self.default_config.max_tokens
