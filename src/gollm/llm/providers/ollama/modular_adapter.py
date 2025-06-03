"""Modular adapter implementation for Ollama API."""

import logging
import time
from typing import Dict, Any, Optional, List, AsyncIterator

from ..config import OllamaConfig
from .http.client import OllamaHttpClient
from .modules.prompt import PromptFormatter, PromptLogger
from .modules.health import HealthMonitor, DiagnosticsCollector
from .modules.model import ModelManager, ModelInfo

logger = logging.getLogger('gollm.ollama.adapter')

class OllamaModularAdapter:
    """Modular adapter for Ollama API with optimized components."""
    
    def __init__(self, config: OllamaConfig):
        """Initialize the Ollama modular adapter.
        
        Args:
            config: Ollama configuration
        """
        self.config = config
        self.client: Optional[OllamaHttpClient] = None
        
        # Component configuration
        self.component_config = {
            'show_prompt': getattr(config, 'show_prompt', False),
            'show_response': getattr(config, 'show_response', False),
            'show_metadata': getattr(config, 'show_metadata', False),
            'adaptive_timeout': getattr(config, 'adaptive_timeout', True),
        }
        
        # Component instances (initialized in __aenter__)
        self.prompt_formatter = None
        self.prompt_logger = None
        self.health_monitor = None
        self.model_manager = None
        self.diagnostics = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        # Initialize HTTP client
        self.client = OllamaHttpClient(self.config)
        await self.client.__aenter__()
        
        # Initialize components
        self.prompt_formatter = PromptFormatter(self.component_config)
        self.prompt_logger = PromptLogger(self.component_config)
        self.health_monitor = HealthMonitor(self.client)
        self.model_manager = ModelManager(self.client)
        self.diagnostics = DiagnosticsCollector(self.component_config, self.client)
        
        # Log initialization
        logger.info(f"Initialized Ollama modular adapter with URL: {self.config.base_url}")
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def is_available(self) -> bool:
        """Check if Ollama API is available.
        
        Returns:
            True if the API is available, False otherwise
        """
        try:
            status = await self.health_monitor.check_health()
            return status.get('success', False)
        except Exception as e:
            logger.error(f"Error checking Ollama availability: {str(e)}")
            return False
    
    async def list_models(self) -> Dict[str, Any]:
        """List available models.
        
        Returns:
            Dictionary containing available models
        """
        try:
            models = await self.model_manager.list_models()
            return {"models": models, "success": True}
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return {"models": [], "error": str(e), "success": False}
    
    async def generate(self, prompt: str, model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate text using the completion endpoint.
        
        Args:
            prompt: The prompt to generate from
            model: Model to use (defaults to config model)
            **kwargs: Additional generation parameters
                
        Returns:
            Dictionary containing the generated text and metadata
        """
        if not self.client:
            return {"success": False, "error": "Adapter not initialized"}
            
        try:
            # Format the prompt
            formatted_prompt = self.prompt_formatter.format_completion_prompt(
                prompt, 
                system_message=kwargs.get('system_message')
            )
            
            # Get prompt metadata
            prompt_metadata = self.prompt_formatter.get_prompt_metadata(formatted_prompt)
            
            # Log the request
            self.prompt_logger.log_request(
                formatted_prompt, 
                model or self.config.model,
                metadata=prompt_metadata
            )
            
            # Extract options from kwargs
            options = kwargs.pop('options', {})
            
            # Set default options if not provided
            if 'temperature' not in options:
                options['temperature'] = self.config.temperature
            if 'num_predict' not in options and 'max_tokens' in kwargs:
                options['num_predict'] = kwargs.pop('max_tokens')
            elif 'num_predict' not in options:
                options['num_predict'] = self.config.max_tokens
                
            # Add any other generation parameters to options
            for param in ['top_p', 'top_k', 'repeat_penalty', 'stop']:
                if param in kwargs and param not in options:
                    options[param] = kwargs.pop(param)
            
            data = {
                "model": model or self.config.model,
                "prompt": formatted_prompt,
                "options": options,
                **kwargs  # Include any remaining kwargs at the top level
            }
            
            # Calculate adaptive timeout if needed
            if self.config.adaptive_timeout:
                timeout = self.config.get_adjusted_timeout(len(formatted_prompt))
                logger.debug(f"Using adaptive timeout of {timeout}s for generation request")
            
            # Send the request
            start_time = time.time()
            result = await self.client._request('POST', '/api/generate', json=data)
            duration = time.time() - start_time
            
            # Add performance metrics
            if 'success' not in result:
                result['success'] = 'error' not in result
            result['duration_seconds'] = duration
            
            # Log the response
            self.prompt_logger.log_response(result, duration)
            
            return result
            
        except Exception as e:
            logger.exception(f"Error in generate: {str(e)}")
            self.prompt_logger.log_error(e, prompt, model)
            return {"success": False, "error": str(e)}
    
    async def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate chat completion.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            model: Model to use for generation (defaults to config model)
            **kwargs: Additional generation parameters
                
        Returns:
            Dictionary containing the generated response and metadata
        """
        if not self.client:
            return {"success": False, "error": "Adapter not initialized"}
            
        try:
            # Format the messages
            formatted_messages = self.prompt_formatter.format_chat_messages(messages)
            
            # Get prompt metadata
            prompt_metadata = self.prompt_formatter.get_prompt_metadata(formatted_messages)
            
            # Log the request
            self.prompt_logger.log_request(
                formatted_messages, 
                model or self.config.model,
                metadata=prompt_metadata
            )
            
            # Extract options from kwargs
            options = kwargs.pop('options', {})
            
            # Set default options if not provided
            if 'temperature' not in options:
                options['temperature'] = self.config.temperature
            
            # Handle max_tokens/num_predict
            if 'num_predict' not in options and 'max_tokens' in kwargs:
                options['num_predict'] = kwargs.pop('max_tokens')
            elif 'num_predict' not in options:
                options['num_predict'] = self.config.max_tokens
                
            # Add any other generation parameters to options
            for param in ['top_p', 'top_k', 'repeat_penalty', 'stop']:
                if param in kwargs and param not in options:
                    options[param] = kwargs.pop(param)
                    
            data = {
                "model": model or self.config.model,
                "messages": formatted_messages,
                "options": options,
                **kwargs  # Include any remaining kwargs at the top level
            }
            
            # Calculate adaptive timeout if needed
            if self.config.adaptive_timeout:
                total_length = sum(len(msg.get('content', '')) for msg in formatted_messages)
                timeout = self.config.get_adjusted_timeout(total_length)
                logger.debug(f"Using adaptive timeout of {timeout}s for chat request")
            
            # Send the request
            start_time = time.time()
            result = await self.client._request('POST', '/api/chat', json=data)
            duration = time.time() - start_time
            
            # Add performance metrics
            if 'success' not in result:
                result['success'] = 'error' not in result
            result['duration_seconds'] = duration
            
            # Log the response
            self.prompt_logger.log_response(result, duration)
            
            return result
            
        except Exception as e:
            logger.exception(f"Error in chat: {str(e)}")
            self.prompt_logger.log_error(e, messages, model)
            return {"success": False, "error": str(e)}
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get the current health status of the Ollama API.
        
        Returns:
            Dictionary containing health status information
        """
        return await self.health_monitor.check_health()
    
    async def get_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostic information about the Ollama setup.
        
        Returns:
            Dictionary containing diagnostic information
        """
        return await self.diagnostics.collect_all_diagnostics()
    
    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary containing model information
        """
        return await self.model_manager.get_model_info(model_name)
