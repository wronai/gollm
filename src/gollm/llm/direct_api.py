"""Direct API access module for fast LLM requests without extensive validation."""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

import aiohttp

# Try to import gRPC-related modules
try:
    from ..llm.providers.ollama.config import OllamaConfig
    from ..llm.providers.ollama.factory import AdapterType, create_adapter

    ADAPTERS_AVAILABLE = True
except ImportError:
    ADAPTERS_AVAILABLE = False

logger = logging.getLogger("gollm.direct_api")


class DirectLLMClient:
    """Direct LLM client for fast API access without extensive processing.

    This client provides a streamlined interface for making direct API calls
    to LLM providers with minimal overhead, similar to using curl directly.
    Supports both HTTP and gRPC communication for improved performance.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        timeout: int = 30,
        use_grpc: bool = False,
    ):
        """Initialize the direct LLM client.

        Args:
            base_url: Base URL of the LLM API server
            timeout: Request timeout in seconds
            use_grpc: Whether to use gRPC for faster communication
        """
        self.base_url = base_url
        self.timeout = timeout
        self.use_grpc = use_grpc and ADAPTERS_AVAILABLE
        self.session: Optional[aiohttp.ClientSession] = None
        self.adapter = None

    async def __aenter__(self):
        """Async context manager entry."""
        if self.use_grpc and ADAPTERS_AVAILABLE:
            # Create a config object for the adapter
            config = OllamaConfig(base_url=self.base_url, timeout=self.timeout)

            try:
                # Try to create a gRPC adapter
                self.adapter = create_adapter(config, AdapterType.GRPC)
                await self.adapter.__aenter__()
                logger.info("Using gRPC adapter for improved performance")
            except Exception as e:
                logger.warning(
                    f"Failed to create gRPC adapter: {e}. Falling back to HTTP."
                )
                self.adapter = None
                self.use_grpc = False
                # Fall back to HTTP session
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    headers={"Content-Type": "application/json"},
                )
        else:
            # Use standard HTTP session
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers={"Content-Type": "application/json"},
            )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.adapter:
            await self.adapter.__aexit__(exc_type, exc_val, exc_tb)
        elif self.session:
            await self.session.close()

    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 1000,
        stream: bool = False,
    ) -> Dict[str, Any]:
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
        # Use gRPC adapter if available
        if self.adapter and self.use_grpc:
            try:
                start_time = asyncio.get_event_loop().time()
                logger.debug(f"Making direct chat request via gRPC with model {model}")

                # Prepare options for the adapter
                options = {"temperature": temperature, "num_predict": max_tokens}

                # Call the adapter's chat method
                result = await self.adapter.chat(
                    model=model, messages=messages, options=options
                )

                duration = asyncio.get_event_loop().time() - start_time
                logger.debug(f"Direct gRPC request completed in {duration:.2f}s")

                # Add duration information for consistency with HTTP response
                if "total_duration" not in result:
                    result["total_duration"] = int(
                        duration * 1_000_000_000
                    )  # Convert to nanoseconds

                return result

            except Exception as e:
                logger.error(f"Direct gRPC request failed: {str(e)}")
                return {"error": str(e), "success": False}

        # Fall back to HTTP if gRPC is not available or failed
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers={"Content-Type": "application/json"},
            )

        url = f"{self.base_url.rstrip('/')}/api/chat"

        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {"temperature": temperature, "num_predict": max_tokens},
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
            return {"error": str(e), "success": False}

    async def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 1000,
        stream: bool = False,
    ) -> Dict[str, Any]:
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
        # Use gRPC adapter if available
        if self.adapter and self.use_grpc:
            try:
                start_time = asyncio.get_event_loop().time()
                logger.debug(
                    f"Making direct generate request via gRPC with model {model}"
                )

                # Prepare options for the adapter
                options = {"temperature": temperature, "num_predict": max_tokens}

                # Call the adapter's generate method
                result = await self.adapter.generate(
                    model=model, prompt=prompt, options=options
                )

                duration = asyncio.get_event_loop().time() - start_time
                logger.debug(f"Direct gRPC request completed in {duration:.2f}s")

                # Add duration information for consistency with HTTP response
                if "total_duration" not in result:
                    result["total_duration"] = int(
                        duration * 1_000_000_000
                    )  # Convert to nanoseconds

                return result

            except Exception as e:
                logger.error(f"Direct gRPC request failed: {str(e)}")
                return {"error": str(e), "success": False}

        # Fall back to HTTP if gRPC is not available or failed
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers={"Content-Type": "application/json"},
            )

        url = f"{self.base_url.rstrip('/')}/api/generate"

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {"temperature": temperature, "num_predict": max_tokens},
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
            return {"error": str(e), "success": False}
