"""Modular adapter implementation for Ollama API."""

import logging
import time
from typing import Dict, Any, Optional, List, AsyncIterator

from ..config import OllamaConfig
from .http.client import OllamaHttpClient
from .modules.prompt import PromptFormatter, PromptLogger
from .modules.health import HealthMonitor, DiagnosticsCollector
from .modules.model import ModelManager, ModelInfo
from .modules.generation.generator import OllamaGenerator
from .modules.config.manager import ConfigManager

logger = logging.getLogger('gollm.ollama.adapter')

class OllamaModularAdapter:
    """Modular adapter for Ollama API with optimized components."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Ollama modular adapter.
        
        Args:
            config: Optional configuration dictionary
        """
        # Initialize configuration manager and load config
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config(config)
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
        self.generator = None
    
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
        self.generator = OllamaGenerator(self.client.session, {
            'base_url': self.config.base_url,
            'model': self.config.model,
            'timeout': self.config.timeout,
            'max_tokens': self.config.max_tokens,
            'temperature': self.config.temperature,
            'api_type': 'chat' if hasattr(self.config, 'use_chat') and self.config.use_chat else 'completion'
        })
        
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
        if not self.client or not self.generator:
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
            
            # Prepare context for generator
            context = {
                'messages': formatted_messages,
                'temperature': kwargs.get('temperature', self.config.temperature),
                'max_tokens': kwargs.get('max_tokens', self.config.max_tokens),
                'system_message': kwargs.get('system_message')
            }
            
            # Add any other generation parameters to context
            for param in ['top_p', 'top_k', 'repeat_penalty', 'stop']:
                if param in kwargs:
                    context[param] = kwargs[param]
            
            # Override model if specified
            if model:
                self.generator.model_name = model
            
            # Use the generator component
            result = await self.generator.generate(formatted_prompt, context)
            
            # Add success flag if not present
            if 'success' not in result:
                result['success'] = 'error' not in result
            
            # Log the response
            self.prompt_logger.log_response(result, result.get('metadata', {}).get('duration', 0))
            
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
        if not self.client or not self.generator:
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
            
            # Prepare context for generator
            context = {
                'messages': formatted_messages,
                'temperature': kwargs.get('temperature', self.config.temperature),
                'max_tokens': kwargs.get('max_tokens', self.config.max_tokens),
                'system_message': kwargs.get('system_message')
            }
            
            # Add any other generation parameters to context
            for param in ['top_p', 'top_k', 'repeat_penalty', 'stop']:
                if param in kwargs:
                    context[param] = kwargs[param]
            
            # Override model if specified
            if model:
                self.generator.model_name = model
                
            # Temporarily switch to chat API type
            original_api_type = self.generator.api_type
            self.generator.api_type = 'chat'
            
            # Use the generator component
            # For chat, we pass an empty prompt since messages are in context
            result = await self.generator.generate("", context)
            
            # Restore original API type
            self.generator.api_type = original_api_type
            
            # Add success flag if not present
            if 'success' not in result:
                result['success'] = 'error' not in result
            
            # Log the response
            self.prompt_logger.log_response(result, result.get('metadata', {}).get('duration', 0))
            
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
        
    async def generate_stream(self, prompt: str, model: Optional[str] = None, **kwargs) -> AsyncIterator[str]:
        """Generate text using the completion endpoint with streaming.
        
        Args:
            prompt: The prompt to generate from
            model: Model to use (defaults to config model)
            **kwargs: Additional generation parameters
                
        Yields:
            Text chunks as they are generated
        """
        if not self.client or not self.generator:
            yield "[Error: Adapter not initialized]"
            return
            
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
            
            # Prepare context for generator
            context = {
                'temperature': kwargs.get('temperature', self.config.temperature),
                'max_tokens': kwargs.get('max_tokens', self.config.max_tokens),
                'system_message': kwargs.get('system_message')
            }
            
            # Add any other generation parameters to context
            for param in ['top_p', 'top_k', 'repeat_penalty', 'stop']:
                if param in kwargs:
                    context[param] = kwargs[param]
            
            # Override model if specified
            if model:
                self.generator.model_name = model
            
            # Use the generator component for streaming
            async for chunk in self.generator.generate_stream(formatted_prompt, context):
                yield chunk
                
        except Exception as e:
            logger.exception(f"Error in generate_stream: {str(e)}")
            self.prompt_logger.log_error(e, prompt, model)
            yield f"[Error: {str(e)}]"
            
    async def chat_stream(self, messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs) -> AsyncIterator[str]:
        """Generate chat completion with streaming.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            model: Model to use for generation (defaults to config model)
            **kwargs: Additional generation parameters
                
        Yields:
            Text chunks as they are generated
        """
        if not self.client or not self.generator:
            yield "[Error: Adapter not initialized]"
            return
            
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
            
            # Prepare context for generator
            context = {
                'messages': formatted_messages,
                'temperature': kwargs.get('temperature', self.config.temperature),
                'max_tokens': kwargs.get('max_tokens', self.config.max_tokens),
                'system_message': kwargs.get('system_message')
            }
            
            # Add any other generation parameters to context
            for param in ['top_p', 'top_k', 'repeat_penalty', 'stop']:
                if param in kwargs:
                    context[param] = kwargs[param]
            
            # Override model if specified
            if model:
                self.generator.model_name = model
                
            # Temporarily switch to chat API type
            original_api_type = self.generator.api_type
            self.generator.api_type = 'chat'
            
            # Use the generator component for streaming
            # For chat, we pass an empty prompt since messages are in context
            async for chunk in self.generator.generate_stream("", context):
                yield chunk
                
            # Restore original API type
            self.generator.api_type = original_api_type
                
        except Exception as e:
            logger.exception(f"Error in chat_stream: {str(e)}")
            self.prompt_logger.log_error(e, messages, model)
            yield f"[Error: {str(e)}]"
