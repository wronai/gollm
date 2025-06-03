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
        adaptive_timeout: Whether to adjust timeout based on model size
    """
    base_url: str = "http://localhost:11434"
    model: str = "codellama:7b"
    timeout: int = 120  # Increased default timeout to 120 seconds
    max_tokens: int = 4000
    temperature: float = 0.1
    api_type: str = "chat"
    api_key: Optional[str] = None
    headers: Dict[str, str] = None
    adaptive_timeout: bool = True
    
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
            headers=config_dict.get('headers'),
            adaptive_timeout=config_dict.get('adaptive_timeout', cls.adaptive_timeout)
        )
        
    def get_adjusted_timeout(self, prompt_length: int = 0) -> int:
        """Calculate an appropriate timeout based on model size and prompt length.
        
        Args:
            prompt_length: Length of the prompt in characters
            
        Returns:
            Adjusted timeout in seconds
        """
        if not self.adaptive_timeout:
            return self.timeout
            
        # Extract model size from model name if possible
        model_size_factor = 1.0
        model_name = self.model.lower()
        
        # Check for model size indicators in the name
        if any(size in model_name for size in ['70b', '65b', '34b']):  # Very large models
            model_size_factor = 2.5
        elif any(size in model_name for size in ['13b', '14b', '16b']):  # Large models
            model_size_factor = 1.5
        elif any(size in model_name for size in ['7b', '8b']):  # Medium models
            model_size_factor = 1.0
        elif any(size in model_name for size in ['3b', '4b', '2b']):  # Small models
            model_size_factor = 0.8
        
        # Factor in prompt length (longer prompts need more time)
        prompt_factor = 1.0
        if prompt_length > 10000:
            prompt_factor = 1.5
        elif prompt_length > 5000:
            prompt_factor = 1.2
        
        # Calculate adjusted timeout with a minimum of the configured timeout
        adjusted_timeout = max(int(self.timeout * model_size_factor * prompt_factor), self.timeout)
        
        return adjusted_timeout
