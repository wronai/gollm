"""Modular adapter implementation for Ollama API."""

import logging
import time
from typing import Dict, Any, Optional, List, AsyncIterator

from ..config import OllamaConfig
from .http.client import OllamaHttpClient
from .modules.prompt import PromptFormatter, PromptLogger, CodePromptFormatter
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
        
        # Handle both dictionary and OllamaConfig objects
        if isinstance(config, dict):
            self.config = self.config_manager.load_config(config)
        else:
            # Convert OllamaConfig to dictionary if needed
            config_dict = {
                'base_url': getattr(config, 'base_url', 'http://localhost:11434'),
                'model': getattr(config, 'model', 'mistral:latest'),
                'timeout': getattr(config, 'timeout', 60),
                'temperature': getattr(config, 'temperature', 0.7),
                'top_p': getattr(config, 'top_p', 0.9),
                'top_k': getattr(config, 'top_k', 40),
                'max_tokens': getattr(config, 'max_tokens', 2048),
            }
            self.config = self.config_manager.load_config(config_dict)
        self.client: Optional[OllamaHttpClient] = None
        
        # Component configuration
        if isinstance(config, dict):
            self.component_config = {
                'show_prompt': config.get('show_prompt', False),
                'show_response': config.get('show_response', False),
                'show_metadata': config.get('show_metadata', False),
                'adaptive_timeout': config.get('adaptive_timeout', True),
            }
        else:
            self.component_config = {
                'show_prompt': getattr(config, 'show_prompt', False),
                'show_response': getattr(config, 'show_response', False),
                'show_metadata': getattr(config, 'show_metadata', False),
                'adaptive_timeout': getattr(config, 'adaptive_timeout', True),
            }
        
        # Component instances (initialized in __aenter__)
        self.prompt_formatter = None
        self.prompt_logger = None
        self.code_formatter = None  # New code-specific formatter
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
        self.code_formatter = CodePromptFormatter(self.component_config)
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
            # Determine if this is a code generation task
            is_code_task = kwargs.get('is_code_generation', False)
            if not is_code_task:
                # Use heuristics to detect code generation requests
                code_keywords = ['code', 'function', 'class', 'implement', 'write', 'create a', 
                                'develop', 'script', 'program', 'algorithm']
                is_code_task = any(keyword in prompt.lower() for keyword in code_keywords)
            
            # Get the target programming language if specified
            language = kwargs.get('language', 'python')
            
            # Format the prompt based on task type
            if is_code_task:
                # Use specialized code formatter
                formatted_prompt = self.code_formatter.format_code_prompt(
                    prompt,
                    language=language,
                    code_context=kwargs.get('code_context'),
                    file_context=kwargs.get('file_context'),
                    system_message=kwargs.get('system_message')
                )
                logger.info(f"Using code-optimized prompt for {language} generation")
            else:
                # Use standard formatter
                formatted_prompt = self.prompt_formatter.format_completion_prompt(
                    prompt, 
                    system_message=kwargs.get('system_message')
                )
            
            # Get prompt metadata
            prompt_metadata = self.prompt_formatter.get_prompt_metadata(formatted_prompt)
            if is_code_task:
                prompt_metadata['task_type'] = 'code_generation'
                prompt_metadata['language'] = language
            
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
                'system_message': kwargs.get('system_message'),
                'is_code_generation': is_code_task,
                'language': language
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
            
            # Post-process code generation results if needed
            if context.get('is_code_generation', False) and 'text' in result:
                # Extract clean code from the response
                original_text = result['text']
                clean_code = self.code_formatter.extract_code_from_response(
                    original_text, 
                    language=context.get('language', 'python')
                )
                
                # Update the result with clean code
                if clean_code != original_text:
                    logger.debug(f"Cleaned up code response, removed {len(original_text) - len(clean_code)} characters")
                    result['original_text'] = original_text
                    result['text'] = clean_code
                    # Also update the generated_text field for backward compatibility
                    if 'generated_text' in result:
                        result['generated_text'] = clean_code
            
            # Log the response
            self.prompt_logger.log_response(result, result.get('metadata', {}).get('duration', 0))
            
            return result
            
        except Exception as e:
            logger.exception(f"Error in generate: {str(e)}")
            self.prompt_logger.log_error(e, prompt, model)
            return {"success": False, "error": str(e)}
    
    async def chat(self, messages, model=None, **kwargs):
        """
        Generate a chat response using the Ollama API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Optional model override
            **kwargs: Additional parameters for generation
            
        Returns:
            Dictionary with generated response
        """
        # Import logger at the module level to avoid UnboundLocalError
        import logging
        logger = logging.getLogger('gollm.ollama.adapter')
        
        logger.info(f"===== STARTING OLLAMA CHAT GENERATION =====")
        logger.info(f"Messages count: {len(messages)}")
        logger.info(f"Model: {model or self.config.model}")
        logger.info(f"Kwargs keys: {list(kwargs.keys())}")
        
        # Log message roles for better tracing
        message_roles = [msg.get('role', 'unknown') for msg in messages]
        logger.info(f"Message roles: {message_roles}")
        
        # Log first user message content preview for context
        user_message = next((msg.get('content', '') for msg in messages if msg.get('role') == 'user'), '')
        if user_message:
            logger.info(f"User message preview: {user_message[:100]}...")
        
        try:
            # Determine if this is a code generation task
            is_code_task = kwargs.get('is_code_generation', False)
            
            # If not explicitly set, try to detect from the last user message
            if not is_code_task and messages:
                last_user_msg = next((msg for msg in reversed(messages) if msg.get('role') == 'user'), None)
                if last_user_msg and 'content' in last_user_msg:
                    # Use heuristics to detect code generation requests
                    code_keywords = ['code', 'function', 'class', 'implement', 'write', 'create a', 
                                    'develop', 'script', 'program', 'algorithm']
                    is_code_task = any(keyword in last_user_msg['content'].lower() for keyword in code_keywords)
            
            # Get the target programming language if specified
            language = kwargs.get('language', 'python')
            
            # Format the messages based on task type
            if is_code_task:
                # Extract the last user prompt from messages
                last_user_msg = next((msg for msg in reversed(messages) if msg.get('role') == 'user'), None)
                if last_user_msg and 'content' in last_user_msg:
                    # Get previous messages for context
                    prev_messages = [msg for msg in messages if msg != last_user_msg]
                    
                    # Use specialized code formatter for chat
                    formatted_messages = self.code_formatter.format_code_chat_messages(
                        last_user_msg['content'],
                        language=language,
                        code_context=kwargs.get('code_context'),
                        file_context=kwargs.get('file_context'),
                        chat_history=prev_messages
                    )
                    logger.info(f"Using code-optimized chat messages for {language} generation")
                    logger.debug(f"Formatted message count: {len(formatted_messages)}")
                    # Log the system message for debugging
                    system_msg = next((msg.get('content', '') for msg in formatted_messages if msg.get('role') == 'system'), '')
                    if system_msg:
                        logger.debug(f"System message preview: {system_msg[:100]}...")
                else:
                    # Fallback to standard formatting if no user message found
                    formatted_messages = self.prompt_formatter.format_chat_messages(messages)
            else:
                # Use standard formatter
                formatted_messages = self.prompt_formatter.format_chat_messages(messages)
            
            # Get prompt metadata
            prompt_metadata = self.prompt_formatter.get_prompt_metadata(formatted_messages)
            if is_code_task:
                prompt_metadata['task_type'] = 'code_generation'
                prompt_metadata['language'] = language
            
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
                'system_message': kwargs.get('system_message'),
                'is_code_generation': is_code_task,
                'language': language
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
            
            logger.info(f"OllamaModularAdapter.chat_async called with context keys: {list(context.keys())}")
            
            # For code generation, ensure we set the flag for higher token limits
            if 'is_code_generation' not in context and any(key in str(context).lower() for key in ['python', 'code', 'function', 'class']):
                logger.info("Setting is_code_generation=True based on context")
                context['is_code_generation'] = True
                
            # Ensure max_tokens is high enough for code generation
            if 'max_tokens' not in context:
                logger.info("Setting default max_tokens=2000 for generation")
                context['max_tokens'] = 2000
            
            result = await self.generator.generate('', context)
            
            # Restore original API type
            self.generator.api_type = original_api_type
            
            # Add success flag if not present
            if 'success' not in result:
                result['success'] = 'error' not in result
            
            # Post-process code generation results if needed
            if context.get('is_code_generation', False) and 'text' in result:
                # Extract clean code from the response
                original_text = result['text']
                clean_code = self.code_formatter.extract_code_from_response(
                    original_text, 
                    language=context.get('language', 'python')
                )
                
                # Update the result with clean code
                if clean_code != original_text:
                    logger.debug(f"Cleaned up code response, removed {len(original_text) - len(clean_code)} characters")
                    result['original_text'] = original_text
                    result['text'] = clean_code
                    # Also update the generated_text field for backward compatibility
                    if 'generated_text' in result:
                        result['generated_text'] = clean_code
            
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
