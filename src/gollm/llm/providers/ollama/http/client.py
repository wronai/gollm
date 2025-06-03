"""HTTP client for Ollama API with optimized connection handling."""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, AsyncIterator, List

import aiohttp

from ..config import OllamaConfig

logger = logging.getLogger('gollm.ollama.http')

class OllamaHttpClient:
    """HTTP client for Ollama API with connection pooling and optimized request handling."""
    
    def __init__(self, config):
        """Initialize the Ollama HTTP client.
        
        Args:
            config: Ollama configuration (OllamaConfig or dict)
        """
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self._request_id = 0
        
        # Extract necessary attributes for both dict and OllamaConfig
        self.base_url = getattr(config, 'base_url', config.get('base_url', 'http://localhost:11434')) if isinstance(config, dict) else config.base_url
        self.timeout = getattr(config, 'timeout', config.get('timeout', 60)) if isinstance(config, dict) else config.timeout
        self.api_key = getattr(config, 'api_key', config.get('api_key', None)) if isinstance(config, dict) else getattr(config, 'api_key', None)
        self.headers = getattr(config, 'headers', config.get('headers', {})) if isinstance(config, dict) else getattr(config, 'headers', {})
    
    async def __aenter__(self):
        """Async context manager entry."""
        trace_config = aiohttp.TraceConfig()
        
        async def on_request_start(session, trace_config_ctx, params):
            """Log the start of a request."""
            trace_config_ctx.start = time.time()
            trace_config_ctx.request_id = self._request_id
            self._request_id += 1
            logger.debug(
                'Request #%d: %s %s', 
                trace_config_ctx.request_id, 
                params.method, 
                params.url
            )
            
        async def on_request_end(session, trace_config_ctx, params):
            """Log the completion of a request."""
            try:
                if not hasattr(trace_config_ctx, 'start') or not hasattr(trace_config_ctx, 'request_id'):
                    logger.debug("Request end logging: Missing trace context attributes")
                    return
                    
                duration = time.time() - trace_config_ctx.start
                status_code = getattr(params, 'response', None)
                status_code = getattr(status_code, 'status', 0) if status_code else 0
                
                logger.debug(
                    'Request #%d finished with status %s in %.2fs',
                    getattr(trace_config_ctx, 'request_id', 0),
                    status_code,
                    duration
                )
            except Exception as e:
                logger.warning("Error in request end logging: %s", str(e), exc_info=True)
            
        trace_config.on_request_start.append(on_request_start)
        trace_config.on_request_end.append(on_request_end)
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        # Handle headers from config (both dict and OllamaConfig)
        config_headers = {}
        if isinstance(self.config, dict) and 'headers' in self.config:
            config_headers = self.config['headers'] or {}
        elif hasattr(self.config, 'headers') and self.config.headers is not None:
            config_headers = self.config.headers
        headers.update(config_headers)
        
        # Handle API key (both dict and OllamaConfig)
        api_key = None
        if isinstance(self.config, dict) and 'api_key' in self.config:
            api_key = self.config['api_key']
        elif hasattr(self.config, 'api_key'):
            api_key = self.config.api_key
            
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        # Use default timeout for session creation, we'll override per request
        self.session = aiohttp.ClientSession(
            base_url=self.config.base_url,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            headers=headers,
            trace_configs=[trace_config]
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make an HTTP request to the Ollama API."""
        if not self.session:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        
        url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}" 
        
        # Log the request
        logger.debug("Making %s request to %s", method, url)
        if 'json' in kwargs:
            logger.debug("Request payload: %s", json.dumps(kwargs['json'], indent=2))
            
        # Calculate adaptive timeout based on request type and payload
        timeout = self.config.timeout
        if self.config.adaptive_timeout and 'json' in kwargs:
            payload = kwargs['json']
            prompt_length = 0
            
            # Extract prompt length from different request types
            if endpoint == '/api/generate' and 'prompt' in payload:
                prompt_length = len(payload['prompt'])
            elif endpoint == '/api/chat' and 'messages' in payload:
                # Sum up all message content lengths
                prompt_length = sum(len(msg.get('content', '')) for msg in payload.get('messages', []))
                
            # Get adjusted timeout based on model and prompt length
            timeout = self.config.get_adjusted_timeout(prompt_length)
            logger.debug(f"Using adaptive timeout of {timeout}s for request (prompt length: {prompt_length})")
        
        # Create a timeout just for this request
        request_timeout = aiohttp.ClientTimeout(total=timeout)
        
        try:
            async with self.session.request(method, url, timeout=request_timeout, **kwargs) as response:
                response.raise_for_status()
                
                # Log response status
                logger.debug("Response status: %d", response.status)
                
                # Handle no content
                if response.status == 204:
                    return {}
                
                # Parse JSON response
                try:
                    response_data = await response.json()
                    logger.debug("Response data: %s", json.dumps(response_data, indent=2))
                    return response_data
                except Exception as json_err:
                    # If JSON parsing fails, try to get text response
                    text_response = await response.text()
                    logger.debug("Non-JSON response: %s", text_response)
                    return {
                        'success': False,
                        'error': f'Invalid JSON response: {str(json_err)}',
                        'raw_response': text_response
                    }
                    
        except aiohttp.ClientResponseError as e:
            error_msg = f"HTTP error {e.status}: {e.message}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'status_code': e.status
            }
        except aiohttp.ClientError as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg
            }
        except asyncio.TimeoutError:
            error_msg = f"Request timed out after {timeout}s"
            logger.error(error_msg)
            
            # Provide more detailed error message with troubleshooting suggestions
            model_info = f" with model {self.config.model}" if hasattr(self.config, 'model') else ""
            suggestions = [
                f"Try increasing the timeout in your configuration (current: {timeout}s)",
                "Check if the Ollama server is under heavy load",
                "Consider using a smaller model if available",
                "Reduce the prompt length or complexity"
            ]
            
            return {
                'success': False,
                'error': error_msg,
                'timeout': True,
                'model': getattr(self.config, 'model', None),
                'suggestions': suggestions,
                'details': f"The request to {endpoint}{model_info} timed out. This could be due to server load, model size, or prompt complexity."
            }
    
    async def list_models(self) -> Dict[str, Any]:
        """List available models."""
        return await self._request('GET', '/api/tags')
    
    async def check_health(self) -> Dict[str, Any]:
        """Check if the Ollama API is healthy."""
        try:
            result = await self._request('GET', '/api/tags')
            return {
                'success': True,
                'status': 'healthy',
                'models_available': len(result.get('models', [])) > 0
            }
        except Exception as e:
            return {
                'success': False,
                'status': 'unhealthy',
                'error': str(e)
            }
