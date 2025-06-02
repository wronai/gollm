"""Configuration for Ollama LLM provider."""

from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class OllamaConfig:
    """Configuration for connecting to Ollama service.
    
    Attributes:
        base_url: Base URL of the Ollama API server
        model: Name of the model to use
        timeout: Request timeout in seconds
        max_tokens: Maximum number of tokens to generate
        temperature: Sampling temperature (0.0 to 1.0)
        api_key: Optional API key for authentication
        headers: Additional headers to include in requests
    """
    base_url: str = "http://localhost:11434"
    model: str = "codellama:7b"
    timeout: int = 60
    max_tokens: int = 4000
    temperature: float = 0.1
    api_type: str = "chat"
    api_key: Optional[str] = None
    headers: Dict[str, str] = None
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'OllamaConfig':
        """Create config from dictionary with environment variable resolution."""
        return cls(
            base_url=config_dict.get('base_url', cls.base_url),
            api_type=config_dict.get('api_type', cls.api_type),
            model=config_dict.get('model', cls.model),
            timeout=config_dict.get('timeout', cls.timeout),
            max_tokens=config_dict.get('max_tokens', cls.max_tokens),
            temperature=config_dict.get('temperature', cls.temperature),
            api_key=config_dict.get('api_key'),
            headers=config_dict.get('headers')
        )
