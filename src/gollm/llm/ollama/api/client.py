"""
HTTP client for Ollama API communication.

This module provides an async HTTP client for making requests to the Ollama API,
including request/response handling, retries, and error management.
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional, AsyncGenerator

import aiohttp

logger = logging.getLogger("gollm.ollama.api.client")


class OllamaAPIClient:
    """Async HTTP client for Ollama API communication."""
    
    def __init__(self, base_url: str, timeout: int = 60):
        """Initialize the API client.
        
        Args:
            base_url: Base URL of the Ollama API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self._session_initialized = False

    async def _ensure_session(self) -> None:
        """Ensure the aiohttp session is initialized."""
        if self._session_initialized and not self.session.closed:
            return

        trace_config = aiohttp.TraceConfig()
        
        async def on_request_start(session, trace_config_ctx, params):
            trace_config_ctx.start = asyncio.get_event_loop().time()
            logger.debug(
                "Starting request: %s %s", 
                params.method, 
                str(params.url).replace(self.base_url, '')
            )

        async def on_request_end(session, trace_config_ctx, params):
            duration = asyncio.get_event_loop().time() - trace_config_ctx.start
            logger.debug(
                "Request finished: %s %s - %d in %.2fs",
                params.method,
                str(params.url).replace(self.base_url, ''),
                params.response.status,
                duration
            )

        trace_config.on_request_start.append(on_request_start)
        trace_config.on_request_end.append(on_request_end)

        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            trace_configs=[trace_config],
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            json_serialize=json.dumps
        )
        self._session_initialized = True

    async def close(self) -> None:
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            self._session_initialized = False

    async def __aenter__(self):
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Any:
        """Make an HTTP request to the Ollama API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            stream: Whether to stream the response
            
        Returns:
            Parsed JSON response or async generator for streaming
            
        Raises:
            aiohttp.ClientError: For HTTP request errors
            json.JSONDecodeError: If response is not valid JSON
        """
        await self._ensure_session()
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout
            ) as response:
                response.raise_for_status()
                
                if stream:
                    return self._stream_response(response)
                    
                try:
                    return await response.json()
                except aiohttp.ContentTypeError as e:
                    text = await response.text()
                    logger.error(
                        "Failed to parse JSON response from %s: %s", 
                        url, text[:200]
                    )
                    raise
                    
        except aiohttp.ClientError as e:
            logger.error("Request to %s failed: %s", url, str(e))
            raise

    async def _stream_response(
        self, 
        response: aiohttp.ClientResponse
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream and parse JSON lines from a streaming response.
        
        Args:
            response: aiohttp client response
            
        Yields:
            Parsed JSON objects from the stream
        """
        buffer = ""
        async for chunk in response.content:
            if not chunk:
                continue
                
            buffer += chunk.decode('utf-8')
            
            # Process complete JSON objects from the buffer
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    data = json.loads(line)
                    yield data
                except json.JSONDecodeError as e:
                    logger.warning("Failed to parse JSON line: %s", line)
                    continue

    async def get_models(self) -> Dict[str, Any]:
        """Get the list of available models.
        
        Returns:
            Dictionary containing model information
        """
        return await self.request('GET', '/api/tags')

    async def generate(
        self, 
        prompt: str, 
        model: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text using a model.
        
        Args:
            prompt: The prompt to generate from
            model: Name of the model to use
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text and metadata
        """
        data = {
            'model': model,
            'prompt': prompt,
            'stream': kwargs.pop('stream', False),
            **kwargs
        }
        return await self.request(
            'POST', 
            '/api/generate', 
            data=data
        )

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a chat completion.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Name of the model to use
            **kwargs: Additional generation parameters
            
        Returns:
            Generated response and metadata
        """
        data = {
            'model': model,
            'messages': messages,
            'stream': kwargs.pop('stream', False),
            **kwargs
        }
        return await self.request(
            'POST',
            '/api/chat',
            data=data
        )
