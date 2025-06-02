"""HTTP adapter for Ollama API."""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, AsyncIterator

import aiohttp

logger = logging.getLogger('gollm.ollama.adapter')

class OllamaAdapter:
    """HTTP client adapter for Ollama API with connection pooling and retries."""
    
    def __init__(self, config: 'OllamaConfig'):
        """Initialize the Ollama HTTP adapter.
        
        Args:
            config: Ollama configuration
        """
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self._request_id = 0
    
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
            duration = time.time() - trace_config_ctx.start
            status_code = getattr(params.response, 'status', 0)
            logger.debug(
                'Request #%d finished: %s - %d in %.2fs',
                trace_config_ctx.request_id,
                status_code,
                duration
            )
            
        trace_config.on_request_start.append(on_request_start)
        trace_config.on_request_end.append(on_request_end)
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            **(self.config.headers or {})
        }
        
        if self.config.api_key:
            headers['Authorization'] = f'Bearer {self.config.api_key}'
        
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
            raise RuntimeError("Adapter not initialized. Use 'async with' context manager.")
        
        url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                if response.status == 204:  # No content
                    return {}
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error("Request failed: %s", str(e))
            raise
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text using the completion endpoint."""
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
            "prompt": prompt,
            "options": options,
            **kwargs  # Include any remaining kwargs at the top level
        }
        
        logger.debug(f"Sending generate request with data: {json.dumps(data, indent=2)}")
        return await self._request('POST', '/api/generate', json=data)
    
    async def chat(
        self,
        messages: list,
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate chat completion."""
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
            "messages": messages,
            "options": options,
            **kwargs  # Include any remaining kwargs at the top level
        }
        
        logger.debug(f"Sending chat request with data: {json.dumps(data, indent=2)}")
        return await self._request('POST', '/api/chat', json=data)
    
    async def list_models(self) -> Dict[str, Any]:
        """List available models."""
        return await self._request('GET', '/api/tags')
    
    async def show_model_info(self, name: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        return await self._request('POST', '/api/show', json={"name": name})
    
    async def create_model(self, name: str, modelfile: str) -> Dict[str, Any]:
        """Create a new model from a Modelfile."""
        return await self._request('POST', '/api/create', json={"name": name, "modelfile": modelfile})
    
    async def delete_model(self, name: str) -> Dict[str, Any]:
        """Delete a model."""
        return await self._request('DELETE', f'/api/delete', json={"name": name})
    
    async def pull_model(self, name: str, insecure: bool = False) -> AsyncIterator[Dict[str, Any]]:
        """Pull a model from the registry with progress updates."""
        if not self.session:
            raise RuntimeError("Adapter not initialized. Use 'async with' context manager.")
        
        url = f"{self.config.base_url.rstrip('/')}/api/pull"
        data = {"name": name, "insecure": insecure}
        
        async with self.session.post(url, json=data) as response:
            response.raise_for_status()
            async for line in response.content:
                if line:
                    yield json.loads(line)
