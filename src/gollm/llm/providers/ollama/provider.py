"""Ollama LLM Provider implementation for goLLM."""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Union, AsyncIterator

from ..base import BaseLLMProvider
from .adapter import OllamaAdapter
from .config import OllamaConfig

logger = logging.getLogger('gollm.ollama.provider')

class OllamaLLMProvider(BaseLLMProvider):
    """LLM Provider for Ollama - compatible with goLLM interface."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Ollama provider with configuration.
        
        Args:
            config: Dictionary containing provider configuration
        """
        super().__init__(config)
        self.config = OllamaConfig.from_dict(config)
        self.adapter: Optional[OllamaAdapter] = None
        self._model_available: Optional[bool] = None
        
        logger.info(
            f"Ollama configuration - URL: {self.config.base_url}, "
            f"Model: {self.config.model}, "
            f"Timeout: {self.config.timeout}"
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.adapter = OllamaAdapter(self.config)
        await self.adapter.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.adapter:
            await self.adapter.__aexit__(exc_type, exc_val, exc_tb)
    
    async def _ensure_valid_model(self) -> bool:
        """Ensure the configured model is available.
        
        Returns:
            bool: True if the model is available, False otherwise
        """
        if self._model_available is not None:
            return self._model_available
            
        try:
            models = await self.adapter.list_models()
            model_names = [model['name'] for model in models.get('models', [])]
            self._model_available = any(
                model_name.startswith(self.config.model) 
                for model_name in model_names
            )
            
            if not self._model_available:
                logger.warning(
                    f"Model '{self.config.model}' not found in available models. "
                    f"Available models: {', '.join(model_names)[:200]}..."
                )
                
            return self._model_available
            
        except Exception as e:
            logger.error(f"Failed to list models: {str(e)}")
            self._model_available = False
            return False
    
    async def generate_response(
        self, 
        prompt: str, 
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a response using the Ollama API.
        
        Args:
            prompt: The prompt to generate a response for
            context: Additional context for the generation
            **kwargs: Additional generation parameters (temperature, max_tokens, etc.)
                - temperature: Controls randomness (0.0 to 1.0)
                - max_tokens: Maximum number of tokens to generate
                - top_p: Nucleus sampling parameter
                - top_k: Limit next token selection to top K
                - repeat_penalty: Penalty for repeated tokens
                - stop: List of strings to stop generation
                - Any other Ollama API parameters
                
        Returns:
            Dictionary containing the generated response and metadata
        """
        if not await self._ensure_valid_model():
            return {
                "success": False,
                "error": f"Model '{self.config.model}' is not available"
            }
        
        # Default generation parameters
        default_params = {
            'temperature': 0.7,
            'max_tokens': 2000,
            'top_p': 0.9,
            'top_k': 40,
            'repeat_penalty': 1.1,
        }
        
        # Update defaults with any provided kwargs
        generation_params = {**default_params, **kwargs}
        
        try:
            # Prepare the options dictionary with generation parameters
            options = {}
            
            # Map common parameter names to Ollama's expected names
            param_mapping = {
                'max_tokens': 'num_predict',
                'frequency_penalty': 'repeat_penalty',
                'presence_penalty': 'repeat_penalty',
            }
            
            # Add all generation parameters to options with proper mapping
            for param, value in generation_params.items():
                # Skip None values to use Ollama defaults
                if value is None:
                    continue
                    
                # Map parameter names if needed
                mapped_param = param_mapping.get(param, param)
                options[mapped_param] = value
            
            # Special handling for stop sequences
            if 'stop' in generation_params and generation_params['stop']:
                options['stop'] = generation_params['stop']
            
            if self.config.api_type == 'chat':
                messages = [{"role": "user", "content": prompt}]
                if context and 'messages' in context:
                    messages = context['messages'] + messages
                    
                response = await self.adapter.chat(
                    messages=messages,
                    model=self.config.model,
                    options=options,
                    stream=False
                )
                
                return {
                    "success": True,
                    "generated_text": response.get('message', {}).get('content', ''),
                    "model": response.get('model', self.config.model),
                    "usage": {
                        "prompt_tokens": len(prompt.split()),
                        "completion_tokens": len(response.get('message', {}).get('content', '').split()),
                        "total_tokens": 0  # Ollama doesn't provide this
                    }
                }
            else:
                response = await self.adapter.generate(
                    prompt=prompt,
                    model=self.config.model,
                    options=options,
                    stream=False
                )
                
                return {
                    "success": True,
                    "generated_text": response.get('response', ''),
                    "model": response.get('model', self.config.model),
                    "usage": {
                        "prompt_tokens": response.get('prompt_eval_count', 0),
                        "completion_tokens": response.get('eval_count', 0),
                        "total_tokens": response.get('eval_count', 0) + response.get('prompt_eval_count', 0)
                    }
                }
                
        except Exception as e:
            logger.exception("Failed to generate response")
            return {
                "success": False,
                "error": f"Failed to generate response: {str(e)}"
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the Ollama service.
        
        Returns:
            Dict containing health check results
        """
        result = {
            'status': False,
            'available': False,
            'model_available': False,
            'error': None,
            'config': {
                'base_url': self.config.base_url,
                'model': self.config.model,
                'timeout': self.config.timeout,
                'api_type': self.config.api_type
            }
        }
        
        try:
            # Check if service is reachable
            await self.adapter.list_models()
            result['available'] = True
            
            # Check if model is available
            result['model_available'] = await self._ensure_valid_model()
            result['status'] = result['model_available']
            
            if not result['model_available']:
                result['error'] = f"Model '{self.config.model}' not found"
                
        except Exception as e:
            result['error'] = str(e)
            
        return result
    
    def is_available(self) -> bool:
        """Check if the Ollama service is available."""
        try:
            return asyncio.get_event_loop().run_until_complete(
                self.health_check()
            )['status']
        except Exception:
            return False
