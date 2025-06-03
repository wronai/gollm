"""LLM client for interacting with different LLM providers."""

import logging
from typing import Dict, Any, Optional, AsyncContextManager

from ..providers import create_provider
from .models import LLMGenerationConfig

logger = logging.getLogger('gollm.orchestrator.llm_client')

class LLMClient(AsyncContextManager):
    """Client for interacting with LLM providers."""
    
    def __init__(self, config: Dict[str, Any], provider_name: Optional[str] = None):
        """Initialize the LLM client.
        
        Args:
            config: Configuration dictionary
            provider_name: Name of the provider to use (default: from config)
        """
        self.config = config
        self.provider_name = provider_name or config.llm_integration.api_provider.lower()
        self.provider = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        # Get provider config
        provider_config = self._get_provider_config()
        
        # Create and initialize provider
        self.provider = create_provider(self.provider_name, provider_config)
        await self.provider.__aenter__()
        
        logger.info(f"Initialized LLM provider: {self.provider_name}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.provider:
            await self.provider.__aexit__(exc_type, exc_val, exc_tb)
    
    def _get_provider_config(self) -> Dict[str, Any]:
        """Get the configuration for the current provider."""
        # Get base config from llm_integration
        base_config = {
            'model': self.config.llm_integration.model_name,
            'temperature': 0.1,
            'max_tokens': self.config.llm_integration.token_limit,
        }
        
        # Merge with provider-specific config
        provider_config = self.config.llm_integration.providers.get(self.provider_name, {})
        return {**base_config, **provider_config}
    
    async def generate(self, prompt: str, context: Optional[Dict[str, Any]] = None, generation_config: Optional[LLMGenerationConfig] = None) -> str:
        """Generate a response from the LLM provider.
        
        Args:
            prompt: The prompt to send to the LLM
            context: Optional context to include with the request
            generation_config: Optional configuration for generation
            
        Returns:
            The generated response
        """
        logger = logging.getLogger(__name__)
        logger.info(f"===== LLM CLIENT GENERATE =====")
        logger.info(f"Provider: {self.provider_name}")
        logger.info(f"Prompt length: {len(prompt)}")
        logger.debug(f"Prompt first 200 chars: {prompt[:200]}...")
        logger.info(f"Context keys: {list(context.keys()) if context else []}")
        
        # Log provider-specific configuration
        if hasattr(self.provider, 'config'):
            provider_config = getattr(self.provider, 'config', {})
            if isinstance(provider_config, dict):
                logger.info(f"Provider config: {provider_config}")
            else:
                logger.info(f"Provider has config object: {type(provider_config).__name__}")
        
        if not self.provider:
            raise RuntimeError("LLM provider not initialized. Use 'async with' context manager.")
        
        # Default generation parameters
        is_simple_prompt = any(term in prompt.lower() for term in ['simple', 'hello', 'world', 'example', 'basic'])
        
        # Prepare base parameters with conservative defaults
        base_params = {
            'temperature': 0.1,  # Very low temperature for deterministic output
            'max_tokens': 50,    # Limit response length
            'top_p': 0.9,        # Focus on high-probability tokens
            'top_k': 40,         # Limit sampling pool
            'repeat_penalty': 1.1,  # Penalize repetition
            'stop': ['```', '\n\n', '\n#', '---', '==='],  # Stop on formatting markers
            'echo': False,       # Don't include the prompt in the output,
        }
        
        # Update with any generation config overrides
        if generation_config:
            if generation_config.temperature is not None:
                base_params['temperature'] = generation_config.temperature
            if generation_config.max_tokens is not None:
                base_params['max_tokens'] = generation_config.max_tokens
        
        # For simple prompts, be extremely strict
        if is_simple_prompt:
            base_params.update({
                'temperature': 0.0,  # Completely deterministic
                'max_tokens': 30,    # Very short output
                'top_p': 0.8,        # Very focused sampling
                'top_k': 20,         # Small sampling pool
                'frequency_penalty': 1.2,  # Strongly discourage repetition
                'presence_penalty': 1.2,   # Strongly encourage new content
            })
        
        # Add any additional context
        if context:
            base_params['context'] = context
        
        # Log the parameters for debugging
        logger.debug(f"Generating with params: {base_params}")
        
        # Generate the response
        try:
            response = await self.provider.generate_response(prompt, **base_params)
            
            if not response.get('success', False):
                error = response.get('error', 'Unknown error')
                logger.error(f"LLM generation failed: {error}")
                raise RuntimeError(f"LLM generation failed: {error}")
                
            return response
            
        except Exception as e:
            logger.exception(f"Error generating response with {self.provider_name}")
            raise RuntimeError(f"Error generating response: {str(e)}") from e
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the LLM provider.
        
        Returns:
            Dictionary with health check results
        """
        if not self.provider:
            return {
                'status': False,
                'error': 'Provider not initialized'
            }
            
        try:
            return await self.provider.health_check()
        except Exception as e:
            logger.exception("Health check failed")
            return {
                'status': False,
                'error': str(e)
            }
