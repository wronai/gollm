"""HTTP adapter for Ollama API."""

import asyncio
import json
import logging
import time
from typing import Any, AsyncIterator, Dict, Optional

import aiohttp

logger = logging.getLogger("gollm.ollama.adapter")


class OllamaAdapter:
    """HTTP client adapter for Ollama API with connection pooling and retries."""

    def __init__(self, config: "OllamaConfig"):
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

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request to the Ollama API."""
        if not self.session:
            raise RuntimeError(
                "Adapter not initialized. Use 'async with' context manager."
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

        except aiohttp.ClientError as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"success": False, "error": error_msg}

    async def generate(
        self, prompt: str, model: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """Generate text using the completion endpoint."""
        # Extract options from kwargs
        options = kwargs.pop("options", {})

        # Set default options if not provided
        if "temperature" not in options:
            options["temperature"] = self.config.temperature
        if "num_predict" not in options and "max_tokens" in kwargs:
            options["num_predict"] = kwargs.pop("max_tokens")
        elif "num_predict" not in options:
            options["num_predict"] = self.config.max_tokens

        # Add any other generation parameters to options
        for param in ["top_p", "top_k", "repeat_penalty", "stop"]:
            if param in kwargs and param not in options:
                options[param] = kwargs.pop(param)

        data = {
            "model": model or self.config.model,
            "prompt": prompt,
            "options": options,
            **kwargs,  # Include any remaining kwargs at the top level
        }

        logger.debug(
            f"Sending generate request with data: {json.dumps(data, indent=2)}"
        )
        return await self._request("POST", "/api/generate", json=data)

    async def chat(
        self, messages: list, model: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """Generate chat completion.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            model: Model to use for generation (defaults to config model)
            **kwargs: Additional generation parameters
                - options: Dictionary of model options
                - stream: Whether to stream the response
                - format: Response format (e.g., 'json')
                - Any other Ollama API parameters

        Returns:
            Dictionary containing the generated response and metadata
        """
        # Extract options from kwargs
        options = kwargs.pop("options", {})

        # Set default options if not provided
        if "temperature" not in options:
            if hasattr(self.config, "temperature"):
                options["temperature"] = self.config.temperature
            else:
                options["temperature"] = 0.1  # Default to very low temperature for code

        # Handle max_tokens/num_predict
        if "num_predict" not in options:
            if "max_tokens" in kwargs:
                options["num_predict"] = kwargs.pop("max_tokens")
            elif hasattr(self.config, "max_tokens"):
                options["num_predict"] = self.config.max_tokens
            else:
                options["num_predict"] = 500  # Default to 500 tokens for code

        # Ensure num_ctx is set
        if "num_ctx" not in options and hasattr(self.config, "num_ctx"):
            options["num_ctx"] = self.config.num_ctx

        # Copy any remaining generation parameters to options
        generation_params = [
            "top_p",
            "top_k",
            "repeat_penalty",
            "stop",
            "num_ctx",
            "num_predict",
            "frequency_penalty",
            "presence_penalty",
            "echo",
            "seed",
            "tfs_z",
            "typical_p",
            "mirostat",
            "mirostat_eta",
            "mirostat_tau",
            "numa",
            "num_keep",
            "penalize_nl",
            "presence_penalty",
            "repeat_last_n",
            "seed",
        ]

        for param in generation_params:
            if param in kwargs and param not in options:
                options[param] = kwargs.pop(param)

        # Ensure stop sequences are properly formatted
        if "stop" in options and options["stop"] is not None:
            if not isinstance(options["stop"], list):
                options["stop"] = [options["stop"]]
            # Ensure all stop sequences are strings
            options["stop"] = [str(s) for s in options["stop"] if s is not None]
            # Remove any empty strings
            options["stop"] = [s for s in options["stop"] if s.strip()]
        else:
            options["stop"] = ["```", "\n```", "\n#", "---", "==="]

        # Ensure required parameters are set
        if "temperature" not in options:
            options["temperature"] = 0.1
        if "num_predict" not in options:
            options["num_predict"] = 100

        # Log the request details
        logger.debug(
            "Sending chat request to model %s with %d messages and options: %s",
            model or self.config.model,
            len(messages),
            json.dumps(options, indent=2) if options else "{}",
        )

        # Prepare the request data
        data = {
            "model": model or self.config.model,
            "messages": messages,
            "options": options,
            "stream": False,
        }

        # Add any additional parameters
        for k, v in kwargs.items():
            if k not in data and v is not None:
                data[k] = v

        # Log the full request data for debugging
        logger.debug("Full request data: %s", json.dumps(data, indent=2))

        data = {
            "model": model or self.config.model,
            "messages": messages,
            "options": options,
            **kwargs,  # Include any remaining kwargs at the top level
        }

        logger.debug(f"Sending chat request with data: {json.dumps(data, indent=2)}")
        return await self._request("POST", "/api/chat", json=data)

    async def list_models(self) -> Dict[str, Any]:
        """List available models."""
        return await self._request("GET", "/api/tags")

    async def show_model_info(self, name: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        return await self._request("POST", "/api/show", json={"name": name})

    async def create_model(self, name: str, modelfile: str) -> Dict[str, Any]:
        """Create a new model from a Modelfile.

        Args:
            name: The name to give to the new model
            modelfile: The content of the Modelfile to use for creating the model

        Returns:
            Dict containing the creation status and model information

        Example:
            ```python
            response = await adapter.create_model(
                name="my-model",
                modelfile="FROM llama2\nPARAMETER temperature 0.7"
            )
            ```
        """
        return await self._request(
            "POST", "/api/create", json={"name": name, "modelfile": modelfile}
        )

    async def delete_model(self, name: str) -> Dict[str, Any]:
        """Delete a model from the Ollama instance.

        Args:
            name: The name of the model to delete

        Returns:
            Dict containing the deletion status

        Example:
            ```python
            response = await adapter.delete_model("my-model")
            ```
        """
        return await self._request("DELETE", "/api/delete", json={"name": name})

    async def pull_model(
        self, name: str, insecure: bool = False
    ) -> AsyncIterator[Dict[str, Any]]:
        """Pull a model from the registry with progress updates.

        This method streams the download progress of the model. Each chunk of the
        response contains status information about the download progress.

        Args:
            name: The name of the model to pull (e.g., "llama2:latest")
            insecure: If True, use insecure connections for pulling the model

        Yields:
            Dict containing progress information about the download

        Raises:
            RuntimeError: If the adapter is not initialized
            aiohttp.ClientError: If the request fails

        Example:
            ```python
            async for progress in adapter.pull_model("llama2:latest"):
                print(f"Status: {progress.get('status')}")
            ```
        """
        if not self.session:
            raise RuntimeError(
                "Adapter not initialized. Use 'async with' context manager."
            )

        url = f"{self.config.base_url.rstrip('/')}/api/pull"
        data = {"name": name, "insecure": insecure}

        async with self.session.post(url, json=data) as response:
            response.raise_for_status()
            async for line in response.content:
                if line:
                    yield json.loads(line)
