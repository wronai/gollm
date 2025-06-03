"""HTTP client for Ollama API requests."""

import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional

import aiohttp

from .config import OllamaConfig

logger = logging.getLogger("gollm.ollama.http_client")


class OllamaHttpClient:
    """HTTP client for Ollama API with connection pooling and request tracing."""

    def __init__(self, config: OllamaConfig):
        """Initialize the Ollama HTTP client.

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
                "Request #%d: %s %s",
                trace_config_ctx.request_id,
                params.method,
                params.url,
            )

        async def on_request_end(session, trace_config_ctx, params):
            """Log the completion of a request."""
            try:
                if not hasattr(trace_config_ctx, "start") or not hasattr(
                    trace_config_ctx, "request_id"
                ):
                    logger.debug(
                        "Request end logging: Missing trace context attributes"
                    )
                    return

                duration = time.time() - trace_config_ctx.start
                status_code = getattr(params, "response", None)
                status_code = getattr(status_code, "status", 0) if status_code else 0

                logger.debug(
                    "Request #%d finished with status %s in %.2fs",
                    getattr(trace_config_ctx, "request_id", 0),
                    status_code,
                    duration,
                )
            except Exception as e:
                logger.warning(
                    "Error in request end logging: %s", str(e), exc_info=True
                )

        trace_config.on_request_start.append(on_request_start)
        trace_config.on_request_end.append(on_request_end)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **(self.config.headers or {}),
        }

        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        self.session = aiohttp.ClientSession(
            base_url=self.config.base_url,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            headers=headers,
            trace_configs=[trace_config],
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request to the Ollama API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional request parameters
                - json: JSON payload
                - params: Query parameters
                - headers: Additional headers

        Returns:
            Dictionary containing the response data
        """
        if not self.session:
            raise RuntimeError(
                "HTTP client not initialized. Use 'async with' context manager."
            )

        url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        # Log the request
        logger.debug("Making %s request to %s", method, url)
        if "json" in kwargs:
            logger.debug("Request payload: %s", json.dumps(kwargs["json"], indent=2))

        try:
            async with self.session.request(method, url, **kwargs) as response:
                response.raise_for_status()

                # Log response status
                logger.debug("Response status: %d", response.status)

                # Handle no content
                if response.status == 204:
                    return {}

                # Parse JSON response
                try:
                    response_data = await response.json()
                    logger.debug(
                        "Response data: %s", json.dumps(response_data, indent=2)
                    )
                    return response_data
                except Exception as json_err:
                    # If JSON parsing fails, try to get text response
                    text_response = await response.text()
                    logger.debug("Non-JSON response: %s", text_response)
                    return {
                        "success": False,
                        "error": f"Invalid JSON response: {str(json_err)}",
                        "raw_response": text_response,
                    }

        except aiohttp.ClientResponseError as e:
            error_msg = f"HTTP error: {e.status} - {e.message}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg, "status_code": e.status}
        except aiohttp.ClientError as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"success": False, "error": error_msg}
        except asyncio.TimeoutError:
            error_msg = f"Request timed out after {self.config.timeout} seconds"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
