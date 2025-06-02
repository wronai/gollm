"""Ollama LLM Provider implementation for goLLM."""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Union, AsyncIterator

from ..base import BaseLLMProvider
from .config import OllamaConfig
from .factory import get_best_available_adapter, create_adapter, AdapterType

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
        self.adapter = None
        self._model_available: Optional[bool] = None
        
        # Determine adapter type from config
        self.adapter_type = config.get('adapter_type', 'http')
        
        # Check if we should use gRPC for better performance
        self.use_grpc = config.get('use_grpc', False)
        
        logger.info(
            f"Ollama configuration - URL: {self.config.base_url}, "
            f"Model: {self.config.model}, "
            f"Adapter: {self.adapter_type}, "
            f"Timeout: {self.config.timeout}"
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        # Create the appropriate adapter
        if self.use_grpc:
            try:
                self.adapter = create_adapter(self.config, AdapterType.GRPC)
            except (ImportError, ValueError):
                logger.warning("Failed to create gRPC adapter, falling back to HTTP")
                self.adapter = create_adapter(self.config, AdapterType.HTTP)
        else:
            self.adapter = create_adapter(self.config, self.adapter_type)
            
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
            result = await self.adapter.list_models()
            available_models = [model['name'] for model in result.get('models', [])]
            self._model_available = self.config.model in available_models
            
            if not self._model_available:
                logger.warning(
                    f"Model '{self.config.model}' not found in available models. "
                    f"Available models: {', '.join(available_models)}"
                )
                
            return self._model_available
            
        except Exception as e:
            logger.error(f"Failed to list models: {str(e)}")
            self._model_available = False
            return False
    
    def _prepare_generation_parameters(self, model: str, **kwargs) -> Dict[str, Any]:
        """Prepare generation parameters for the Ollama API.
        
        Args:
            model: The model name
            **kwargs: Additional generation parameters
                
        Returns:
            Dictionary of prepared generation parameters
        """
        # Start with default parameters
        params = {
            'model': model,
            'temperature': 0.7,
            'top_p': 0.9,
            'top_k': 40,
            'repeat_penalty': 1.1,
            'num_ctx': 4096,
            'num_predict': 500,
            'stop': ['```', '\n```', '\n#', '---', '==='],
        }
        
        # Update with any provided kwargs, filtering out None values
        params.update({k: v for k, v in kwargs.items() if v is not None})
        
        # Ensure parameter values are within valid ranges
        if 'temperature' in params:
            params['temperature'] = max(0.0, min(1.0, float(params['temperature'])))
            
        if 'top_p' in params:
            params['top_p'] = max(0.0, min(1.0, float(params['top_p'])))
            
        if 'top_k' in params:
            params['top_k'] = max(1, min(100, int(params['top_k'])))
            
        if 'repeat_penalty' in params:
            params['repeat_penalty'] = max(1.0, float(params['repeat_penalty']))
            
        if 'num_predict' in params:
            params['num_predict'] = max(1, int(params['num_predict']))
        
        # Ensure stop is a list of strings
        if 'stop' in params and params['stop'] is not None:
            if isinstance(params['stop'], str):
                params['stop'] = [params['stop']]
            elif not isinstance(params['stop'], list):
                params['stop'] = list(map(str, params['stop']))
        
        return params
    
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
            **kwargs: Additional generation parameters
                
        Returns:
            Dictionary containing the generated response and metadata
        """
        if not self.adapter:
            return {
                "success": False,
                "error": "Adapter not initialized",
                "generated_text": ""
            }
            
        if not await self._ensure_valid_model():
            return {
                "success": False,
                "error": f"Model '{self.config.model}' is not available",
                "generated_text": ""
            }
            
        try:
            # Default generation parameters - optimized for code generation
            default_params = {
                'temperature': 0.1,      # Very low for deterministic output
                'max_tokens': 500,       # Increased to allow for longer code blocks
                'top_p': 0.9,            # Focus on high probability tokens
                'top_k': 40,             # Limit sampling pool
                'repeat_penalty': 1.2,   # Penalize repetition more
                'num_ctx': 4096,         # Increased context window for code generation
                'stop': ['```', '\n\n', '\n#', '---', '===', '\n'],  # Stop on formatting
            }
        
            # Update defaults with any provided kwargs, filtering out None values
            generation_params = {**default_params, **{k: v for k, v in kwargs.items() if v is not None}}
            
            # Modify the prompt to be extremely explicit about the expected output format
            if 'CODE_ONLY' not in prompt:
                prompt = f"""
                {prompt}
                
                RULES:
                - Provide clean, well-documented code
                - Include necessary imports
                - Follow best practices for the language
                - Ensure the code is complete and runnable
                - Comment your code where appropriate
                """
            
            # Determine whether to use chat or generate API
            if self.config.api_type == 'chat':
                # Format as chat messages
                messages = [
                    {"role": "system", "content": "You are a helpful coding assistant that writes clean, well-documented code."},
                    {"role": "user", "content": prompt}
                ]
                
                # Add context as system message if provided
                if context:
                    context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
                    messages.insert(
                        1, 
                        {"role": "system", "content": f"Context information:\n{context_str}"}
                    )
                
                # Make the API call
                result = await self.adapter.chat(
                    messages=messages,
                    model=self.config.model,
                    **generation_params
                )
                
                # Extract generated text from response
                if result.get('success', False):
                    if 'message' in result:
                        generated_text = result['message'].get('content', '')
                    else:
                        generated_text = result.get('response', '')
                    
                    return {
                        "success": True,
                        "generated_text": generated_text,
                        "model": self.config.model,
                        "raw_response": result
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get('error', 'Unknown error'),
                        "generated_text": "",
                        "raw_response": result
                    }
            else:
                # Format context as part of the prompt if provided
                if context:
                    context_str = "\n".join([f"# {k}: {v}" for k, v in context.items()])
                    prompt = f"{context_str}\n\n{prompt}"
                
                # Make the API call
                result = await self.adapter.generate(
                    prompt=prompt,
                    model=self.config.model,
                    **generation_params
                )
                
                # Extract generated text from response
                if result.get('success', False):
                    generated_text = result.get('response', '')
                    
                    return {
                        "success": True,
                        "generated_text": generated_text,
                        "model": self.config.model,
                        "raw_response": result
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get('error', 'Unknown error'),
                        "generated_text": "",
                        "raw_response": result
                    }
                
        except Exception as e:
            logger.error(f"Failed to generate response: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to generate response: {str(e)}",
                "generated_text": ""
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a comprehensive health check of the Ollama service.
        
        Returns:
            Dict containing health status information
        """
        if not self.adapter:
            return {
                "status": False,
                "available": False,
                "model_available": False,
                "error": "Adapter not initialized",
                "config": {
                    "base_url": self.config.base_url,
                    "model": self.config.model,
                    "adapter_type": self.adapter_type
                }
            }
        
        # Check if service is available
        available = await self.adapter.is_available()
        
        # Check if model is available
        model_available = False
        if available:
            model_available = await self._ensure_valid_model()
        
        return {
            "status": available and model_available,
            "available": available,
            "model_available": model_available,
            "error": None if (available and model_available) else (
                "Service not available" if not available else f"Model '{self.config.model}' not available"
            ),
            "config": {
                "base_url": self.config.base_url,
                "model": self.config.model,
                "adapter_type": self.adapter_type,
                "use_grpc": self.use_grpc
            }
        }
    
    async def is_available(self) -> bool:
        """Check if Ollama service is available.
        
        Returns:
            True if available, False otherwise
        """
        if not self.adapter:
            return False
            
        return await self.adapter.is_available()
