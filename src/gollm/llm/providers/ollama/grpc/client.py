"""gRPC client for Ollama API providing faster communication."""

import asyncio
import logging
import os
import time
from typing import Dict, Any, Optional, List, Tuple

import grpc

# Import the generated protobuf code
# Note: These will be available after running generate_protos.py
try:
    from . import ollama_pb2
    from . import ollama_pb2_grpc
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False
    logging.warning("gRPC dependencies not available. Run generate_protos.py first.")

from ..config import OllamaConfig

logger = logging.getLogger('gollm.ollama.grpc')

class OllamaGrpcClient:
    """gRPC client for Ollama API with optimized communication.
    
    This client provides significantly faster communication with the Ollama API
    by using gRPC instead of HTTP REST calls.
    """
    
    def __init__(self, config: OllamaConfig):
        """Initialize the Ollama gRPC client.
        
        Args:
            config: Ollama configuration
        """
        if not GRPC_AVAILABLE:
            raise ImportError(
                "gRPC dependencies not available. "
                "Install grpcio and grpcio-tools, then run generate_protos.py"
            )
            
        self.config = config
        self._channel = None
        self._stub = None
        
        # Extract host and port from base_url
        # Example: http://localhost:11434 -> localhost:11434
        url = config.base_url.lower()
        if url.startswith('http://'):
            url = url[7:]
        elif url.startswith('https://'):
            url = url[8:]
            
        # Remove any path component
        url = url.split('/', 1)[0]
        
        self.server_address = url
        logger.debug(f"gRPC client initialized with server address: {self.server_address}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        # Create a gRPC channel
        self._channel = grpc.aio.insecure_channel(self.server_address)
        self._stub = ollama_pb2_grpc.OllamaServiceStub(self._channel)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._channel:
            await self._channel.close()
    
    async def generate(self, 
                      prompt: str,
                      model: Optional[str] = None,
                      **kwargs) -> Dict[str, Any]:
        """Generate text using the gRPC Generate endpoint.
        
        Args:
            prompt: The prompt to generate from
            model: Model to use (defaults to config model)
            **kwargs: Additional generation parameters
                - temperature: Controls randomness (0.0 to 1.0)
                - max_tokens/num_predict: Maximum tokens to generate
                - top_p: Nucleus sampling parameter (0.0 to 1.0)
                - top_k: Limit next token selection to top K (1-100)
                - repeat_penalty: Penalty for repeated tokens (1.0+)
                - stop: List of strings to stop generation
                - stream: Whether to stream the response
                
        Returns:
            Dictionary containing the generated text and metadata
        """
        if not self._stub:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
            
        # Extract options
        stream = kwargs.pop('stream', False)
        options = kwargs.pop('options', {})
        
        # Set default options
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
        
        # Build the gRPC request
        grpc_options = ollama_pb2.GenerateOptions(
            temperature=float(options.get('temperature', 0.1)),
            num_predict=int(options.get('num_predict', 4000)),
            top_p=float(options.get('top_p', 0.9)),
            top_k=int(options.get('top_k', 40)),
            repeat_penalty=float(options.get('repeat_penalty', 1.1))
        )
        
        # Add stop sequences if provided
        if 'stop' in options and options['stop']:
            if isinstance(options['stop'], str):
                grpc_options.stop.append(options['stop'])
            else:
                for stop_seq in options['stop']:
                    grpc_options.stop.append(stop_seq)
        
        request = ollama_pb2.GenerateRequest(
            model=model or self.config.model,
            prompt=prompt,
            stream=stream,
            options=grpc_options
        )
        
        logger.debug(f"Sending gRPC generate request for model: {request.model}")
        start_time = time.time()
        
        try:
            # Make the gRPC call
            response = await self._stub.Generate(request, timeout=self.config.timeout)
            
            duration = time.time() - start_time
            logger.debug(f"gRPC generate request completed in {duration:.2f}s")
            
            # Convert to dict format similar to HTTP API
            result = {
                'model': response.model,
                'response': response.response,
                'done': response.done,
                'success': True,
                'duration_seconds': duration
            }
            
            # Add usage info if available
            if hasattr(response, 'usage') and response.usage:
                result['usage'] = {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
                
            return result
            
        except grpc.RpcError as e:
            duration = time.time() - start_time
            error_msg = f"gRPC error: {e.code()} - {e.details()}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg,
                'duration_seconds': duration,
                'grpc_code': str(e.code())
            }
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            error_msg = f"gRPC request timed out after {self.config.timeout}s"
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg,
                'duration_seconds': duration,
                'timeout': True
            }
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Unexpected error in gRPC generate: {str(e)}"
            logger.exception(error_msg)
            
            return {
                'success': False,
                'error': error_msg,
                'duration_seconds': duration
            }
    
    async def chat(self,
                  messages: List[Dict[str, str]],
                  model: Optional[str] = None,
                  **kwargs) -> Dict[str, Any]:
        """Generate chat completion using the gRPC Chat endpoint.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            model: Model to use for generation (defaults to config model)
            **kwargs: Additional generation parameters
                
        Returns:
            Dictionary containing the generated response and metadata
        """
        if not self._stub:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
            
        # Extract options
        stream = kwargs.pop('stream', False)
        options = kwargs.pop('options', {})
        
        # Set default options
        if 'temperature' not in options:
            options['temperature'] = self.config.temperature
        if 'num_predict' not in options and 'max_tokens' in kwargs:
            options['num_predict'] = kwargs.pop('max_tokens')
        elif 'num_predict' not in options:
            options['num_predict'] = self.config.max_tokens
            
        # Build the gRPC request
        grpc_options = ollama_pb2.GenerateOptions(
            temperature=float(options.get('temperature', 0.1)),
            num_predict=int(options.get('num_predict', 4000)),
            top_p=float(options.get('top_p', 0.9)),
            top_k=int(options.get('top_k', 40)),
            repeat_penalty=float(options.get('repeat_penalty', 1.1))
        )
        
        # Add stop sequences if provided
        if 'stop' in options and options['stop']:
            if isinstance(options['stop'], str):
                grpc_options.stop.append(options['stop'])
            else:
                for stop_seq in options['stop']:
                    grpc_options.stop.append(stop_seq)
        
        # Convert messages to gRPC format
        grpc_messages = []
        for msg in messages:
            grpc_message = ollama_pb2.Message(
                role=msg.get('role', 'user'),
                content=msg.get('content', '')
            )
            grpc_messages.append(grpc_message)
        
        request = ollama_pb2.ChatRequest(
            model=model or self.config.model,
            messages=grpc_messages,
            stream=stream,
            options=grpc_options
        )
        
        logger.debug(f"Sending gRPC chat request for model: {request.model}")
        start_time = time.time()
        
        try:
            # Make the gRPC call
            response = await self._stub.Chat(request, timeout=self.config.timeout)
            
            duration = time.time() - start_time
            logger.debug(f"gRPC chat request completed in {duration:.2f}s")
            
            # Convert to dict format similar to HTTP API
            result = {
                'model': response.model,
                'message': {
                    'role': response.message.role,
                    'content': response.message.content
                },
                'done': response.done,
                'success': True,
                'duration_seconds': duration
            }
            
            # Add usage info if available
            if hasattr(response, 'usage') and response.usage:
                result['usage'] = {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
                
            return result
            
        except grpc.RpcError as e:
            duration = time.time() - start_time
            error_msg = f"gRPC error: {e.code()} - {e.details()}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg,
                'duration_seconds': duration,
                'grpc_code': str(e.code())
            }
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            error_msg = f"gRPC request timed out after {self.config.timeout}s"
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg,
                'duration_seconds': duration,
                'timeout': True
            }
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Unexpected error in gRPC chat: {str(e)}"
            logger.exception(error_msg)
            
            return {
                'success': False,
                'error': error_msg,
                'duration_seconds': duration
            }
    
    async def list_models(self) -> Dict[str, Any]:
        """List available models using gRPC.
        
        Returns:
            Dictionary containing available models
        """
        if not self._stub:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
            
        try:
            request = ollama_pb2.ListModelsRequest()
            response = await self._stub.ListModels(request, timeout=self.config.timeout)
            
            # Convert to dict format similar to HTTP API
            models = []
            for model in response.models:
                models.append({
                    'name': model.name,
                    'family': model.family,
                    'size': model.size,
                    'modified_at': model.modified_at
                })
                
            return {'models': models}
            
        except Exception as e:
            error_msg = f"Error listing models: {str(e)}"
            logger.error(error_msg)
            return {'models': [], 'error': error_msg}
    
    async def check_health(self) -> Dict[str, Any]:
        """Check if the Ollama API is healthy using gRPC.
        
        Returns:
            Dictionary containing health status
        """
        if not self._stub:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
            
        try:
            request = ollama_pb2.HealthRequest()
            response = await self._stub.Health(request, timeout=self.config.timeout)
            
            return {
                'success': response.healthy,
                'status': response.status,
                'version': response.version
            }
            
        except Exception as e:
            error_msg = f"Error checking health: {str(e)}"
            logger.error(error_msg)
            return {'success': False, 'status': 'unhealthy', 'error': error_msg}
