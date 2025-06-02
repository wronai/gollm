"""Direct API access module for fast LLM requests without extensive validation."""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List

import aiohttp

logger = logging.getLogger('gollm.direct_api')

class DirectLLMClient:
    """Direct LLM client for fast API access without extensive processing.
    
    This client provides a streamlined interface for making direct API calls
    to LLM providers with minimal overhead, similar to using curl directly.
    """
    
    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 30):
        """Initialize the direct LLM client.
        
        Args:
            base_url: Base URL of the LLM API server
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={'Content-Type': 'application/json'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def chat_completion(self, 
                             model: str, 
                             messages: List[Dict[str, str]], 
                             temperature: float = 0.1,
                             max_tokens: int = 1000,
                             stream: bool = False) -> Dict[str, Any]:
        """Make a direct chat completion request to the API.
        
        Args:
            model: The model to use
            messages: List of message objects with role and content
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            The API response as a dictionary
        """
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers={'Content-Type': 'application/json'}
            )
        
        url = f"{self.base_url.rstrip('/')}/api/chat"
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        logger.debug(f"Making direct chat request to {url} with model {model}")
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with self.session.post(url, json=payload) as response:
                response.raise_for_status()
                result = await response.json()
                
                duration = asyncio.get_event_loop().time() - start_time
                logger.debug(f"Direct API request completed in {duration:.2f}s")
                
                return result
                
        except Exception as e:
            logger.error(f"Direct API request failed: {str(e)}")
            return {
                "error": str(e),
                "success": False
            }
    
    async def generate(self,
                      model: str,
                      prompt: str,
                      temperature: float = 0.1,
                      max_tokens: int = 1000,
                      stream: bool = False) -> Dict[str, Any]:
        """Make a direct generation request to the API.
        
        Args:
            model: The model to use
            prompt: The prompt text
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            The API response as a dictionary
        """
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers={'Content-Type': 'application/json'}
            )
        
        url = f"{self.base_url.rstrip('/')}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        logger.debug(f"Making direct generate request to {url} with model {model}")
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with self.session.post(url, json=payload) as response:
                response.raise_for_status()
                result = await response.json()
                
                duration = asyncio.get_event_loop().time() - start_time
                logger.debug(f"Direct API request completed in {duration:.2f}s")
                
                return result
                
        except Exception as e:
            logger.error(f"Direct API request failed: {str(e)}")
            return {
                "error": str(e),
                "success": False
            }
