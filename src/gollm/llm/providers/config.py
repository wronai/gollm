"""Configuration classes for LLM providers."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class BaseProviderConfig:
    """Base configuration for LLM providers."""

    provider_name: str
    timeout_seconds: int = 60
    max_retries: int = 3
    retry_delay_seconds: int = 1
    debug_mode: bool = False


@dataclass
class OllamaConfig(BaseProviderConfig):
    """Configuration for Ollama provider."""

    provider_name: str = "ollama"
    host: str = "localhost"
    port: int = 11434
    base_url: Optional[str] = None
    model: str = "codellama:7b"
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    max_tokens: int = 4096
    stop_sequences: List[str] = field(default_factory=list)
    system_prompt: Optional[str] = None
    adapter_type: str = "modular"  # "modular" or "legacy"
    use_streaming: bool = True

    def __post_init__(self):
        """Set base_url if not provided."""
        if not self.base_url:
            self.base_url = f"http://{self.host}:{self.port}"


@dataclass
class OpenAIConfig(BaseProviderConfig):
    """Configuration for OpenAI provider."""

    provider_name: str = "openai"
    api_key: str = ""
    model: str = "gpt-4"
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 4096
    stop_sequences: List[str] = field(default_factory=list)
    system_prompt: Optional[str] = None


@dataclass
class AnthropicConfig(BaseProviderConfig):
    """Configuration for Anthropic provider."""

    provider_name: str = "anthropic"
    api_key: str = ""
    model: str = "claude-3-opus-20240229"
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 4096
    stop_sequences: List[str] = field(default_factory=list)
    system_prompt: Optional[str] = None


def create_provider_config(
    provider_name: str, config_dict: Dict[str, Any]
) -> BaseProviderConfig:
    """Create a provider configuration from a dictionary.

    Args:
        provider_name: Name of the provider
        config_dict: Dictionary with configuration values

    Returns:
        Provider configuration object
    """
    if provider_name == "ollama":
        return OllamaConfig(**config_dict)
    elif provider_name == "openai":
        return OpenAIConfig(**config_dict)
    elif provider_name == "anthropic":
        return AnthropicConfig(**config_dict)
    else:
        raise ValueError(f"Unknown provider: {provider_name}")
