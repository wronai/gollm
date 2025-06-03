"""Ollama LLM Provider implementation for goLLM."""

import asyncio
import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple, Union

from ..base import BaseLLMProvider
from .config import OllamaConfig
from .factory import AdapterType, create_adapter, get_best_available_adapter

logger = logging.getLogger("gollm.ollama.provider")


class OllamaLLMProvider(BaseLLMProvider):
    """LLM Provider for Ollama - compatible with goLLM interface."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Ollama provider with configuration.

        Args:
            config: Dictionary containing provider configuration
        """
        super().__init__(config)
        self.config = OllamaConfig.from_dict(config)
        self.adapter = None
        self._model_available: Optional[bool] = None

        # Determine adapter type from environment variables first, then config
        import os

        self.adapter_type = (
            os.environ.get("OLLAMA_ADAPTER_TYPE")
            or os.environ.get("GOLLM_ADAPTER_TYPE")
            or config.get("adapter_type", "modular")
        )  # Default to modular adapter

        # Check if we should use gRPC for better performance
        self.use_grpc = (
            config.get("use_grpc", False)
            or os.environ.get("GOLLM_USE_GRPC", "").lower() == "true"
        )

        logger.info(
            f"Ollama configuration - URL: {self.config.base_url}, "
            f"Model: {self.config.model}, "
            f"Adapter: {self.adapter_type}, "
            f"Timeout: {self.config.timeout}"
        )

    async def __aenter__(self):
        """Async context manager entry."""
        # Create the appropriate adapter
        if self.use_grpc:
            try:
                self.adapter = create_adapter(self.config, AdapterType.GRPC)
            except (ImportError, ValueError):
                logger.warning("Failed to create gRPC adapter, falling back to HTTP")
                self.adapter = create_adapter(self.config, AdapterType.HTTP)
        else:
            self.adapter = create_adapter(self.config, self.adapter_type)

        await self.adapter.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.adapter:
            await self.adapter.__aexit__(exc_type, exc_val, exc_tb)

    async def is_available(self) -> bool:
        """Check if Ollama service is available.

        Returns:
            True if available, False otherwise
        """
        if not self.adapter:
            return False

        return await self.adapter.is_available()

    async def health_check(self) -> Dict[str, Any]:
        """Perform a comprehensive health check of the Ollama service.

        Returns:
            Dict containing health status information
        """
        if not self.adapter:
            return {
                "status": False,
                "available": False,
                "model_available": False,
                "error": "Adapter not initialized",
                "config": {
                    "base_url": self.config.base_url,
                    "model": self.config.model,
                    "adapter_type": self.adapter_type,
                },
            }

        # Check if service is available
        available = await self.adapter.is_available()

        # Check if model is available
        model_available = False
        if available:
            model_available = await self._ensure_valid_model()

        return {
            "status": available and model_available,
            "available": available,
            "model_available": model_available,
            "error": (
                None
                if (available and model_available)
                else (
                    "Service not available"
                    if not available
                    else f"Model '{self.config.model}' not available"
                )
            ),
            "config": {
                "base_url": self.config.base_url,
                "model": self.config.model,
                "adapter_type": self.adapter_type,
                "use_grpc": self.use_grpc,
            },
        }

    async def _ensure_valid_model(self) -> bool:
        """Ensure the configured model is available.

        Returns:
            bool: True if the model is available, False otherwise
        """
        if self._model_available is not None:
            return self._model_available

        try:
            result = await self.adapter.list_models()
            available_models = [model["name"] for model in result.get("models", [])]
            self._model_available = self.config.model in available_models

            if not self._model_available:
                logger.warning(
                    f"Model '{self.config.model}' not found in available models. "
                    f"Available models: {', '.join(available_models)}"
                )

            return self._model_available

        except Exception as e:
            logger.error(f"Failed to list models: {str(e)}")
            self._model_available = False
            return False

    def _prepare_generation_parameters(self, model: str, **kwargs) -> Dict[str, Any]:
        """Prepare generation parameters for the Ollama API.

        Args:
            model: The model name
            **kwargs: Additional generation parameters
                - temperature: Controls randomness (0.0 to 1.0)
                - max_tokens: Maximum number of tokens to generate
                - top_p: Nucleus sampling parameter (0.0 to 1.0)
                - top_k: Limit next token selection to top K (1-100)
                - repeat_penalty: Penalty for repeated tokens (1.0+)
                - stop: List of strings to stop generation

        Returns:
            Dictionary of prepared generation parameters
        """
        # Start with default parameters
        params = {
            "model": model,
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.1,
            "num_ctx": 4096,
            "num_predict": 500,
            "stop": ["```", "\n```", "\n#", "---", "==="],
        }

        # Update with any provided kwargs, filtering out None values
        params.update({k: v for k, v in kwargs.items() if v is not None})

        # Ensure parameter values are within valid ranges
        if "temperature" in params:
            params["temperature"] = max(0.0, min(1.0, float(params["temperature"])))

        if "top_p" in params:
            params["top_p"] = max(0.0, min(1.0, float(params["top_p"])))

        if "top_k" in params:
            params["top_k"] = max(1, min(100, int(params["top_k"])))

        if "repeat_penalty" in params:
            params["repeat_penalty"] = max(1.0, float(params["repeat_penalty"]))

        if "num_predict" in params:
            params["num_predict"] = max(1, int(params["num_predict"]))

        # Ensure stop is a list of strings
        if "stop" in params and params["stop"] is not None:
            if isinstance(params["stop"], str):
                params["stop"] = [params["stop"]]
            elif not isinstance(params["stop"], list):
                params["stop"] = list(map(str, params["stop"]))

        return params

    async def generate_response(
        self, prompt: str, context: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Dict[str, Any]:
        """Generate a response using the Ollama API.

        Args:
            prompt: The prompt to generate a response for
            context: Additional context for the generation
            **kwargs: Additional generation parameters (temperature, max_tokens, etc.)
                - temperature: Controls randomness (0.0 to 1.0)
                - max_tokens: Maximum number of tokens to generate
                - top_p: Nucleus sampling parameter (0.0 to 1.0)
                - top_k: Limit next token selection to top K (1-100)
                - repeat_penalty: Penalty for repeated tokens (1.0+)
                - stop: List of strings to stop generation
                - Any other Ollama API parameters

        Returns:
            Dictionary containing the generated response and metadata
                - success: Whether the generation was successful
                - generated_text: The generated text (if successful)
                - error: Error message (if unsuccessful)
                - model: The model used for generation
                - usage: Token usage information
        """
        # Import the generation module
        from .generation import generate_response as generate
        from .models import ensure_model_available
        from .prompt import extract_response_content

        # Ensure we have an adapter
        if not self.adapter:
            await self.__aenter__()

        # Ensure the model is available
        model_available = await ensure_model_available(self.adapter, self.config.model)
        if not model_available:
            return {
                "success": False,
                "error": f"Model '{self.config.model}' is not available",
                "generated_text": "",
            }

        try:
            # Default generation parameters - optimized for code generation
            default_params = {
                "temperature": 0.1,  # Very low for deterministic output
                "max_tokens": 500,  # Increased to allow for longer code blocks
                "top_p": 0.9,  # Focus on high probability tokens
                "top_k": 40,  # Limit sampling pool
                "repeat_penalty": 1.2,  # Penalize repetition more
                "num_ctx": 4096,  # Increased context window for code generation
                "stop": [
                    "```",
                    "\n\n",
                    "\n#",
                    "---",
                    "===",
                    "\n",
                ],  # Stop on formatting
            }

            # Log incoming parameters for debugging
            logger.debug("Original generation parameters: %s", kwargs)

            # Update defaults with any provided kwargs, filtering out None values
            generation_params = {
                **default_params,
                **{k: v for k, v in kwargs.items() if v is not None},
            }

            # Ensure temperature is within valid range
            if "temperature" in generation_params:
                generation_params["temperature"] = max(
                    0.0, min(1.0, float(generation_params["temperature"]))
                )

            # Modify the prompt to be extremely explicit about the expected output format
            if "CODE_ONLY" not in prompt:
                prompt = f"""
                {prompt}
                
                RULES:
                - Respond with ONLY the Python code, nothing else
                - No explanations, no markdown, no additional text
                - Just the raw Python code that can be executed directly
                
                Example of the ONLY acceptable response:
                print("Hello, World!")
                
                CODE_ONLY: True
                """.strip()

                # Add a system message to ensure the model understands the format
                if context and "messages" in context:
                    # If we have a chat context, insert a system message
                    context["messages"].insert(
                        0,
                        {
                            "role": "system",
                            "content": "You are a code generator. Respond with ONLY the requested code, no explanations, no markdown, just the raw code.",
                        },
                    )

            # Get generation parameters with overrides
            generation_params = self._prepare_generation_parameters(
                model=self.config.model, **kwargs
            )

            # Force specific parameters for code generation
            generation_params["temperature"] = 0.1
            generation_params["top_p"] = 0.9
            generation_params["top_k"] = 40
            generation_params["repeat_penalty"] = 1.1
            generation_params["num_ctx"] = 4096
            generation_params["num_predict"] = 500  # Override to allow longer responses

            # Ensure consistent stop sequences
            if "stop" not in generation_params or not generation_params["stop"]:
                generation_params["stop"] = ["```", "\n```", "\n#", "---", "==="]

            # Prepare the options dictionary with generation parameters
            options = {}

            # Map common parameter names to Ollama's expected names
            param_mapping = {
                "max_tokens": "num_predict",
                "frequency_penalty": "repeat_penalty",
                "presence_penalty": "repeat_penalty",
                "stop": "stop",
            }

            # Add all generation parameters to options with proper mapping
            for param, value in generation_params.items():
                # Skip None values to use Ollama defaults
                if value is None:
                    continue

                # Special handling for stop sequences
                if param == "stop" and value:
                    if not isinstance(value, list):
                        value = [str(value)]
                    options["stop"] = [str(s) for s in value]
                    continue

                # Map parameter names if needed
                mapped_param = param_mapping.get(param, param)

                # Ensure parameter values are within valid ranges
                if mapped_param == "temperature":
                    value = max(0.0, min(1.0, float(value)))
                elif mapped_param in ("top_p", "top_k"):
                    value = max(1, min(100, int(value)))
                elif mapped_param == "repeat_penalty":
                    value = max(1.0, float(value))
                elif mapped_param == "num_predict":
                    value = max(1, int(value))

                options[mapped_param] = value

            # Log the final options being sent to the API
            logger.debug(f"Sending to Ollama API with options: {options}")

            # Prepare messages or prompt based on API type
            if self.config.api_type == "chat":
                messages = [{"role": "user", "content": prompt}]
                if context and "messages" in context:
                    messages = context["messages"] + messages

                logger.debug(f"Sending chat request with messages: {messages}")
                response = await self.adapter.chat(
                    messages=messages,
                    model=self.config.model,
                    options=options,
                    stream=False,
                )

                # Handle chat completion response format
                generated_text = response.get("message", {}).get("content", "")
                model = response.get("model", self.config.model)
                prompt_tokens = response.get("prompt_eval_count", len(prompt.split()))
                completion_tokens = response.get(
                    "eval_count", len(generated_text.split())
                )
            else:
                # Handle completion response format
                response = await self.adapter.generate(
                    prompt=prompt,
                    model=self.config.model,
                    options=options,
                    stream=False,
                )

                # Extract the generated text from different possible response formats
                generated_text = ""
                if isinstance(response, str):
                    generated_text = response
                elif "response" in response:
                    generated_text = response["response"]
                elif (
                    "message" in response
                    and isinstance(response["message"], dict)
                    and "content" in response["message"]
                ):
                    generated_text = response["message"]["content"]
                elif (
                    "choices" in response
                    and len(response["choices"]) > 0
                    and "text" in response["choices"][0]
                ):
                    generated_text = response["choices"][0]["text"]
                elif (
                    "choices" in response
                    and len(response["choices"]) > 0
                    and "message" in response["choices"][0]
                ):
                    generated_text = response["choices"][0]["message"].get(
                        "content", ""
                    )
                elif "generated_text" in response:
                    generated_text = response["generated_text"]

                # Clean up the generated text
                if generated_text:
                    # Remove any leading/trailing whitespace and newlines
                    generated_text = generated_text.strip()

                    # Try to extract clean code from the response
                    original_text = generated_text

                    # First, try to find a code block
                    if "```" in generated_text:
                        parts = generated_text.split("```")
                        if len(parts) > 1:
                            # Find the first code block that might contain Python code
                            for i in range(1, len(parts), 2):
                                if i < len(parts):
                                    code_part = parts[i].strip()
                                    # Remove language specifier if present
                                    if code_part.startswith("python"):
                                        code_part = code_part[6:].lstrip("\n")

                                    # Clean up the code block
                                    cleaned_code = code_part.split("```")[0].strip()
                                    if cleaned_code:  # If we found valid code, use it
                                        generated_text = cleaned_code
                                        break

                    # If we still don't have a good match, try to find the first line that looks like Python code
                    if generated_text == original_text:
                        for line in generated_text.split("\n"):
                            line = line.strip()
                            # Look for lines that look like Python code
                            if (
                                line.startswith("print(")
                                or line.startswith("def ")
                                or line.startswith("import ")
                                or line.startswith("class ")
                                or line.startswith("from ")
                            ):
                                generated_text = line
                                break

                    # If we still have a long response, try to extract just the first line
                    if len(generated_text) > 100:
                        first_line = generated_text.split("\n")[0].strip()
                        if (
                            first_line and len(first_line) < 50
                        ):  # Only use if it's a reasonable length
                            generated_text = first_line

                model = response.get("model", self.config.model)
                prompt_tokens = response.get("prompt_eval_count", len(prompt.split()))
                completion_tokens = response.get(
                    "eval_count", len(generated_text.split())
                )

            # Log the final generated text
            logger.debug("Extracted generated text: %s", generated_text)

            # Return the response in the expected format
            return {
                "success": True,
                "generated_text": generated_text,
                "model": model,
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                },
                "raw_response": response,  # Include raw response for debugging
            }

        except Exception as e:
            logger.exception("Failed to generate response")
            return {
                "success": False,
                "error": f"Failed to generate response: {str(e)}",
                "generated_text": "",
            }

    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the Ollama service.

        Returns:
            Dict containing health check results
        """
        # Use the new comprehensive health check from the health module
        from .health import comprehensive_health_check

        # Ensure we have an adapter
        if not self.adapter:
            await self.__aenter__()

        # Perform the health check
        result = await comprehensive_health_check(self.adapter, self.config)

        # Convert to the expected format for backward compatibility
        return {
            "status": result["status"],
            "available": result["service"].get("available", False),
            "model_available": result["model"].get("available", False),
            "error": result.get("error")
            or result["service"].get("error")
            or result["model"].get("error"),
            "config": result["config"],
            "details": result,  # Include full details for advanced diagnostics
        }

    def is_available(self) -> bool:
        """Check if the Ollama service is available."""
        try:
            return asyncio.get_event_loop().run_until_complete(self.health_check())[
                "status"
            ]
        except Exception:
            return False

    async def generate_response_stream(
        self, prompt: str, context: Optional[Dict[str, Any]] = None, **kwargs
    ) -> AsyncIterator[Tuple[str, Dict[str, Any]]]:
        """Generate a streaming response using the Ollama API.

        Args:
            prompt: The prompt to generate a response for
            context: Additional context for the generation
            **kwargs: Additional generation parameters (temperature, max_tokens, etc.)
                - temperature: Controls randomness (0.0 to 1.0)
                - max_tokens: Maximum number of tokens to generate
                - top_p: Nucleus sampling parameter (0.0 to 1.0)
                - top_k: Limit next token selection to top K (1-100)
                - repeat_penalty: Penalty for repeated tokens (1.0+)
                - stop: List of strings to stop generation
                - Any other Ollama API parameters

        Yields:
            Tuples of (text_chunk, metadata) where:
                - text_chunk: A chunk of the generated text
                - metadata: Dictionary with generation metadata
        """
        # Import the generation module
        from .generation import extract_response_content
        from .models import ensure_model_available

        # Ensure we have an adapter
        if not self.adapter:
            await self.__aenter__()

        # Ensure the model is available
        model_available = await ensure_model_available(self.adapter, self.config.model)
        if not model_available:
            yield (
                "",
                {
                    "success": False,
                    "error": f"Model '{self.config.model}' is not available",
                    "generated_text": "",
                },
            )
            return

        try:
            # Default generation parameters - optimized for code generation
            default_params = {
                "temperature": 0.1,  # Very low for deterministic output
                "max_tokens": 500,  # Increased to allow for longer code blocks
                "top_p": 0.9,  # Focus on high probability tokens
                "top_k": 40,  # Limit sampling pool
                "repeat_penalty": 1.2,  # Penalize repetition more
                "num_ctx": 4096,  # Increased context window for code generation
                "stop": [
                    "```",
                    "\n\n",
                    "\n#",
                    "---",
                    "===",
                    "\n",
                ],  # Stop on formatting
            }

            # Update defaults with any provided kwargs, filtering out None values
            generation_params = {
                **default_params,
                **{k: v for k, v in kwargs.items() if v is not None},
            }

            # Ensure temperature is within valid range
            if "temperature" in generation_params:
                generation_params["temperature"] = max(
                    0.0, min(1.0, float(generation_params["temperature"]))
                )

            # Modify the prompt to be extremely explicit about the expected output format
            if "CODE_ONLY" not in prompt:
                prompt = f"""
                {prompt}
                
                RULES:
                - Respond with ONLY the Python code, nothing else
                - No explanations, no markdown, no additional text
                - Just the raw Python code that can be executed directly
                
                Example of the ONLY acceptable response:
                print("Hello, World!")
                
                CODE_ONLY: True
                """.strip()

                # Add a system message to ensure the model understands the format
                if context and "messages" in context:
                    # If we have a chat context, insert a system message
                    context["messages"].insert(
                        0,
                        {
                            "role": "system",
                            "content": "You are a code generator. Respond with ONLY the requested code, no explanations, no markdown, just the raw code.",
                        },
                    )

            # Get generation parameters with overrides
            generation_params = self._prepare_generation_parameters(
                model=self.config.model, **kwargs
            )

            # Force specific parameters for code generation
            generation_params["temperature"] = 0.1
            generation_params["top_p"] = 0.9
            generation_params["top_k"] = 40
            generation_params["repeat_penalty"] = 1.1
            generation_params["num_ctx"] = 4096
            generation_params["num_predict"] = 500  # Override to allow longer responses

            # Ensure consistent stop sequences
            if "stop" not in generation_params or not generation_params["stop"]:
                generation_params["stop"] = ["```", "\n```", "\n#", "---", "==="]

            # Prepare the options dictionary with generation parameters
            options = {}

            # Map common parameter names to Ollama's expected names
            param_mapping = {
                "max_tokens": "num_predict",
                "frequency_penalty": "repeat_penalty",
                "presence_penalty": "repeat_penalty",
                "stop": "stop",
            }

            # Add all generation parameters to options with proper mapping
            for param, value in generation_params.items():
                # Skip None values to use Ollama defaults
                if value is None:
                    continue

                # Special handling for stop sequences
                if param == "stop" and value:
                    if not isinstance(value, list):
                        value = [str(value)]
                    options["stop"] = [str(s) for s in value]
                    continue

                # Map parameter names if needed
                mapped_param = param_mapping.get(param, param)

                # Ensure parameter values are within valid ranges
                if mapped_param == "temperature":
                    value = max(0.0, min(1.0, float(value)))
                elif mapped_param in ("top_p", "top_k"):
                    value = max(1, min(100, int(value)))
                elif mapped_param == "repeat_penalty":
                    value = max(1.0, float(value))
                elif mapped_param == "num_predict":
                    value = max(1, int(value))

                options[mapped_param] = value

            # Log the final options being sent to the API
            logger.debug(f"Sending to Ollama API with options: {options}")

            # Prepare messages or prompt based on API type
            full_text = ""
            metadata = {
                "success": True,
                "model": self.config.model,
                "usage": {
                    "prompt_tokens": len(prompt.split()),
                    "completion_tokens": 0,
                    "total_tokens": len(prompt.split()),
                },
            }

            if self.config.api_type == "chat":
                messages = [{"role": "user", "content": prompt}]
                if context and "messages" in context:
                    messages = context["messages"] + messages

                logger.debug(
                    f"Sending streaming chat request with messages: {messages}"
                )

                # Use the adapter's streaming chat method
                if hasattr(self.adapter, "chat_stream"):
                    async for chunk in self.adapter.chat_stream(
                        messages=messages, model=self.config.model, options=options
                    ):
                        full_text += chunk
                        metadata["usage"]["completion_tokens"] = len(full_text.split())
                        metadata["usage"]["total_tokens"] = (
                            metadata["usage"]["prompt_tokens"]
                            + metadata["usage"]["completion_tokens"]
                        )
                        yield (chunk, metadata)
                else:
                    # Fallback to non-streaming if streaming not available
                    response = await self.adapter.chat(
                        messages=messages,
                        model=self.config.model,
                        options=options,
                        stream=False,
                    )

                    # Handle chat completion response format
                    generated_text = response.get("message", {}).get("content", "")
                    yield (
                        generated_text,
                        {
                            "success": True,
                            "model": response.get("model", self.config.model),
                            "usage": {
                                "prompt_tokens": response.get(
                                    "prompt_eval_count", len(prompt.split())
                                ),
                                "completion_tokens": response.get(
                                    "eval_count", len(generated_text.split())
                                ),
                                "total_tokens": response.get(
                                    "prompt_eval_count", len(prompt.split())
                                )
                                + response.get(
                                    "eval_count", len(generated_text.split())
                                ),
                            },
                        },
                    )
            else:
                # Use the adapter's streaming generate method
                if hasattr(self.adapter, "generate_stream"):
                    async for chunk in self.adapter.generate_stream(
                        prompt=prompt, model=self.config.model, options=options
                    ):
                        full_text += chunk
                        metadata["usage"]["completion_tokens"] = len(full_text.split())
                        metadata["usage"]["total_tokens"] = (
                            metadata["usage"]["prompt_tokens"]
                            + metadata["usage"]["completion_tokens"]
                        )
                        yield (chunk, metadata)
                else:
                    # Fallback to non-streaming if streaming not available
                    response = await self.adapter.generate(
                        prompt=prompt,
                        model=self.config.model,
                        options=options,
                        stream=False,
                    )

                    # Extract the generated text from different possible response formats
                    generated_text = ""
                    if isinstance(response, str):
                        generated_text = response
                    elif "response" in response:
                        generated_text = response["response"]
                    elif (
                        "message" in response
                        and isinstance(response["message"], dict)
                        and "content" in response["message"]
                    ):
                        generated_text = response["message"]["content"]
                    elif (
                        "choices" in response
                        and len(response["choices"]) > 0
                        and "text" in response["choices"][0]
                    ):
                        generated_text = response["choices"][0]["text"]
                    elif (
                        "choices" in response
                        and len(response["choices"]) > 0
                        and "message" in response["choices"][0]
                    ):
                        generated_text = response["choices"][0]["message"].get(
                            "content", ""
                        )
                    elif "generated_text" in response:
                        generated_text = response["generated_text"]

                    # Clean up the generated text
                    if generated_text:
                        # Remove any leading/trailing whitespace and newlines
                        generated_text = generated_text.strip()

                    yield (
                        generated_text,
                        {
                            "success": True,
                            "model": response.get("model", self.config.model),
                            "usage": {
                                "prompt_tokens": response.get(
                                    "prompt_eval_count", len(prompt.split())
                                ),
                                "completion_tokens": response.get(
                                    "eval_count", len(generated_text.split())
                                ),
                                "total_tokens": response.get(
                                    "prompt_eval_count", len(prompt.split())
                                )
                                + response.get(
                                    "eval_count", len(generated_text.split())
                                ),
                            },
                        },
                    )

        except Exception as e:
            logger.exception("Failed to generate streaming response")
            yield (
                "",
                {
                    "success": False,
                    "error": f"Failed to generate streaming response: {str(e)}",
                    "generated_text": "",
                },
            )
