"""
Configuration classes for Ollama integration.

This module contains configuration classes used to manage Ollama settings
and parameters for LLM interactions.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class OllamaConfig:
    """Configuration for Ollama LLM interactions.
    
    Attributes:
        base_url: Base URL of the Ollama API server
        model: Name of the model to use
        timeout: Request timeout in seconds
        max_tokens: Maximum number of tokens to generate
        temperature: Sampling temperature (0.0 to 1.0)
        top_p: Nucleus sampling parameter
        top_k: Top-k sampling parameter
        repeat_penalty: Penalty for repeated tokens
        stop: List of stop sequences
        additional_params: Additional parameters for the API
    """
    base_url: str = "http://localhost:11434"
    model: str = "codellama:7b"
    timeout: int = 60
    max_tokens: int = 4000
    temperature: float = 0.1
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    stop: list = field(default_factory=list)
    additional_params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary.
        
        Returns:
            Dictionary containing the configuration parameters
        """
        return {
            'base_url': self.base_url,
            'model': self.model,
            'timeout': self.timeout,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'top_k': self.top_k,
            'repeat_penalty': self.repeat_penalty,
            'stop': self.stop,
            **self.additional_params
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'OllamaConfig':
        """Create an OllamaConfig from a dictionary.
        
        Args:
            config_dict: Dictionary containing configuration parameters
            
        Returns:
            Configured OllamaConfig instance
        """
        # Known configuration parameters
        known_params = {
            'base_url', 'model', 'timeout', 'max_tokens',
            'temperature', 'top_p', 'top_k', 'repeat_penalty', 'stop'
        }
        
        # Separate known and additional parameters
        known = {k: v for k, v in config_dict.items() if k in known_params}
        additional = {k: v for k, v in config_dict.items() if k not in known_params}
        
        # Create config with known params
        config = cls(**known)
        
        # Add additional parameters
        config.additional_params = additional
        
        return config
