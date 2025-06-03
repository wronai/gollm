"""Generator module for Ollama LLM operations."""

import asyncio
import json
import logging
import time
from typing import Any, AsyncIterator, Dict, List, Optional

import aiohttp

logger = logging.getLogger("gollm.ollama.generation")


class OllamaGenerator:
    """Handles generation operations for Ollama models."""

    def __init__(self, session: aiohttp.ClientSession, config: Dict[str, Any]):
        """Initialize the generator.

        Args:
            session: aiohttp client session
            config: Configuration dictionary
        """
        self.session = session
        self.config = config
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.model_name = config.get("model", "codellama:7b")
        self.timeout = config.get("timeout", 60)
        self.token_limit = config.get("max_tokens", 4000)
        self.temperature = config.get("temperature", 0.1)
        self.api_type = config.get("api_type", "chat")

    def _calculate_adaptive_timeout(self, prompt: str, context: Dict[str, Any]) -> int:
        """Calculate an adaptive timeout based on prompt length and task type.

        Args:
            prompt: The prompt to generate a response for
            context: Additional context for the generation

        Returns:
            Calculated timeout in seconds
        """
        # Start with the base timeout
        timeout = self.timeout

        # If adaptive timeout is disabled, return the base timeout
        if not context.get("adaptive_timeout", True):
            return timeout

        # Calculate based on prompt length
        prompt_length = len(prompt)

        # For very short prompts (e.g., "hello world"), use a shorter timeout
        if prompt_length < 50:
            timeout = min(timeout, 30)  # Cap at 30 seconds for very short prompts

        # For medium-length prompts, scale linearly
        elif prompt_length < 500:
            # Scale from 30s to base timeout based on length
            timeout = max(30, min(timeout, 30 + (prompt_length / 500) * (timeout - 30)))

        # For longer prompts, increase the timeout
        else:
            # Add 5 seconds for every 1000 chars over 500, up to 2x base timeout
            additional_time = min((prompt_length - 500) / 1000 * 5, timeout)
            timeout = min(timeout * 2, timeout + additional_time)

        # Adjust for code generation tasks which may need less time
        if context.get("is_code_generation", False):
            # Code generation often needs less time than creative text generation
            code_factor = 0.8  # 20% reduction for code tasks
            timeout = max(20, timeout * code_factor)  # But never less than 20 seconds

            # Further adjust based on language complexity
            language = context.get("language", "python").lower()
            if language in ["python", "javascript", "typescript"]:
                # These languages are typically faster to generate
                timeout = max(15, timeout * 0.9)
            elif language in ["c++", "rust", "java"]:
                # These languages may need more time
                timeout = timeout * 1.1

        # Round to nearest second
        return round(timeout)

    async def generate(self, prompt, context=None):
        """
        Generate text using the appropriate API based on the current api_type.

        Args:
            prompt: The text prompt to generate from
            context: Additional context for generation

        Returns:
            Dictionary with generated text and metadata
        """
        import logging

        logger = logging.getLogger("gollm.ollama.generator")

        logger.info(f"===== OLLAMA GENERATOR STARTING =====")
        logger.info(f"API type: {self.api_type}")
        logger.info(f"Model: {self.model_name}")
        logger.info(f"Prompt length: {len(prompt) if prompt else 0}")
        logger.info(f"Context keys: {list(context.keys()) if context else []}")

        if not context:
            context = {}
        context = context or {}

        # Record start time for metrics
        start_time = time.time()

        # Calculate adaptive timeout before generation
        timeout = self._calculate_adaptive_timeout(prompt, context)
        if timeout != self.timeout:
            logger.info(f"Using adaptive timeout: {timeout}s (base: {self.timeout}s)")
            # Store the calculated timeout in the context for use in generation methods
            context["calculated_timeout"] = timeout

        # Determine which API endpoint to use
        if self.api_type == "chat":
            result = await self._generate_chat(prompt, context)
        else:
            result = await self._generate_completion(prompt, context)

        # Calculate metrics
        end_time = time.time()
        duration = end_time - start_time

        # Add metadata to result
        result["metadata"] = {
            "duration": duration,
            "model": self.model_name,
            "api_type": self.api_type,
            "timestamp": end_time,
        }

        return result

    async def _generate_chat(
        self, prompt: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a response using the chat endpoint"""
        import logging

        logger = logging.getLogger("gollm.ollama.generator")
        logger.info(f"===== OLLAMA GENERATOR CHAT REQUEST STARTED =====")
        logger.info(f"Context keys: {list(context.keys())}")
        logger.info(f"Using model: {context.get('model', self.model_name)}")
        logger.info(f"Max tokens: {context.get('max_tokens', self.token_limit)}")
        logger.info(f"Temperature: {context.get('temperature', self.temperature)}")
        logger.info(f"Is code generation: {context.get('is_code_generation', False)}")
        logger.info(f"API type: {self.api_type}")

        # Prepare the payload
        messages = context.get("messages", [])
        if not messages and prompt:
            # If no messages provided but we have a prompt, create a simple message
            messages = [{"role": "user", "content": prompt}]

            # Add system message if provided
            if "system_message" in context:
                messages.insert(
                    0, {"role": "system", "content": context["system_message"]}
                )

        # Build the request payload
        max_tokens = context.get("max_tokens", self.token_limit)
        # Increase token limit to ensure we get complete code responses
        if context.get("is_code_generation", False):
            # For code generation, use a higher token limit to avoid truncation
            max_tokens = max(max_tokens, 2000)  # Ensure at least 2000 tokens for code
            logger.info(
                f"Using increased token limit for code generation: {max_tokens}"
            )

        payload = {
            "model": context.get("model", self.model_name),
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": context.get("temperature", self.temperature),
                "num_predict": max_tokens,
            },
        }

        # Add optional parameters if present
        for param in ["top_p", "top_k", "repeat_penalty", "stop"]:
            if param in context:
                payload["options"][param] = context[param]

        logger.debug(f"Chat API request payload: {json.dumps(payload, indent=2)}")

        # Use the calculated adaptive timeout if available, otherwise use the default
        timeout = context.get("calculated_timeout", self.timeout)

        # For code generation tasks, add a small buffer for very short prompts
        if context.get("is_code_generation", False) and len(prompt) < 100:
            # Ensure at least 15 seconds for even the simplest code tasks
            timeout = max(15, timeout)

        logger.debug(f"Using timeout of {timeout}s for chat request")

        try:
            async with self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        f"Ollama chat API error: {response.status} - {error_text}"
                    )
                    return {
                        "error": f"API error: {response.status}",
                        "details": error_text,
                        "generated_text": "",
                        "text": "",
                    }

                result = await response.json()
                logger.debug(f"Chat API raw response: {json.dumps(result, indent=2)}")
                # Log the response in a more visible way for debugging
                logger.info(f"===== OLLAMA RESPONSE RECEIVED =====")
                logger.info(f"Response status: {response.status}")
                logger.info(f"Response keys: {list(result.keys())}")
                logger.info(f"Done reason: {result.get('done_reason', 'unknown')}")
                logger.info(f"Total tokens: {result.get('eval_count', 0)}")
                logger.debug(f"Full response: {json.dumps(result, indent=2)}")

                # Extract the response content - the API might return different formats
                generated_text = ""

                logger.info(f"===== EXTRACTING CONTENT FROM OLLAMA RESPONSE =====")

                # Try to extract from standard chat format first
                if "message" in result and "content" in result["message"]:
                    generated_text = result["message"]["content"]
                    logger.info(
                        f"Extracted content from message.content (length: {len(generated_text)})"
                    )
                    logger.debug(f"Content first 200 chars: {generated_text[:200]}...")
                    logger.debug(
                        f"Content last 200 chars: {generated_text[-200:] if len(generated_text) > 200 else generated_text}"
                    )

                    # Check for code blocks in the content
                    import re

                    code_blocks = re.findall(
                        r"```(?:\w*)?\n(.+?)(?:\n```|$)", generated_text, re.DOTALL
                    )
                    logger.info(f"Found {len(code_blocks)} code blocks in content")
                    for i, block in enumerate(code_blocks):
                        logger.info(f"Code block {i+1} length: {len(block)}")
                        logger.debug(
                            f"Code block {i+1} first 100 chars: {block[:100]}..."
                        )
                        logger.debug(
                            f"Code block {i+1} last 100 chars: {block[-100:] if len(block) > 100 else block}"
                        )

                # If not found, try to extract from response field (some Ollama versions)
                elif "response" in result:
                    generated_text = result["response"]
                    logger.info(
                        f"Extracted content from response (length: {len(generated_text)})"
                    )
                    logger.debug(f"Content first 200 chars: {generated_text[:200]}...")
                    logger.debug(
                        f"Content last 200 chars: {generated_text[-200:] if len(generated_text) > 200 else generated_text}"
                    )

                else:
                    logger.warning(
                        f"Could not find content in Ollama response. Keys: {list(result.keys())}"
                    )
                    # Try to extract from any field that might contain text
                    for key, value in result.items():
                        if (
                            isinstance(value, str) and len(value) > 50
                        ):  # Likely to be content
                            logger.info(
                                f"Found potential content in key '{key}' (length: {len(value)})"
                            )
                            logger.debug(f"Content first 200 chars: {value[:200]}...")
                            generated_text = value
                            break

                logger.debug(
                    f"Extracted chat text (length: {len(generated_text)}): {generated_text[:100]}..."
                )

                return {
                    "generated_text": generated_text,
                    "text": generated_text,  # For consistency with the _generate_completion method
                    "raw_response": result,
                    "finish_reason": result.get("done", True),
                    "success": True,
                }
        except asyncio.TimeoutError:
            logger.error(f"Timeout during chat generation after {timeout}s")
            return {
                "error": "Timeout",
                "details": f"Request timed out after {timeout} seconds",
                "generated_text": "",
                "text": "",
            }
        except Exception as e:
            logger.exception(f"Error during chat generation: {str(e)}")
            return {"error": "Exception", "details": str(e), "generated_text": ""}

    async def _generate_completion(
        self, prompt: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate using the completion API.

        Args:
            prompt: The prompt to generate a response for
            context: Additional context for the generation

        Returns:
            Dictionary containing the generated text and metadata
        """
        # Prepare request payload
        payload = {
            "model": context.get("model", self.model_name),
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": context.get("temperature", self.temperature),
                "num_predict": context.get("max_tokens", self.token_limit),
            },
        }

        # Add system message if provided
        if "system_message" in context:
            payload["system"] = context["system_message"]

        # Add optional parameters if present
        for param in ["top_p", "top_k", "repeat_penalty", "stop"]:
            if param in context:
                payload["options"][param] = context[param]

        # Use the calculated adaptive timeout if available, otherwise use the default
        timeout = context.get("calculated_timeout", self.timeout)

        # For code generation tasks, add a small buffer for very short prompts
        if context.get("is_code_generation", False) and len(prompt) < 100:
            # Ensure at least 15 seconds for even the simplest code tasks
            timeout = max(15, timeout)

        logger.debug(f"Using timeout of {timeout}s for completion request")
        logger.debug(
            f"Sending completion request to Ollama API: {json.dumps(payload, indent=2)}"
        )

        # Make the API request
        try:
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        f"Ollama completion API error: {response.status} - {error_text}"
                    )
                    return {}
        except Exception as e:
            logger.exception(f"Error during completion generation: {str(e)}")
            return {
                "error": "Exception",
                "details": str(e),
                "generated_text": "",
                "text": "",
            }

        # Apply adaptive timeout if specified in context
        if context.get("adaptive_timeout", False):
            prompt_length = len(prompt)
            if api_type == "chat" and context.get("messages"):
                # For chat, calculate total content length of all messages
                prompt_length = sum(
                    len(msg.get("content", "")) for msg in context["messages"]
                )
            # Add 1 second per 500 characters with a minimum of base timeout
            additional_time = int(prompt_length / 500)
            timeout = max(self.timeout, self.timeout + additional_time)
            logger.debug(
                f"Using adaptive timeout of {timeout}s for request (prompt length: {prompt_length})"
            )
            context["timeout"] = (
                timeout  # Pass the adjusted timeout to the generation methods
            )

        # Call the appropriate generation method based on API type
        start_time = time.time()

        if api_type == "chat":
            result = await self._generate_chat(prompt, context)
        else:
            result = await self._generate_completion(prompt, context)

        # Add metadata
        end_time = time.time()
        duration = end_time - start_time

        if "metadata" not in result:
            result["metadata"] = {}

        result["metadata"].update(
            {
                "duration": duration,
                "model": self.model_name,
                "api_type": api_type,
                "timestamp": end_time,
            }
        )

        return result

    async def generate_stream(
        self, prompt: str, context: Dict[str, Any] = None
    ) -> AsyncIterator[str]:
        """Generate a streaming response using the Ollama API.

        Args:
            prompt: The prompt to generate a response for
            context: Additional context for the generation

        Yields:
            Text chunks as they are generated
        """
        context = context or {}

        # Determine which API endpoint to use
        if self.api_type == "chat":
            async for chunk in self._generate_chat_stream(prompt, context):
                yield chunk
        else:
            async for chunk in self._generate_completion_stream(prompt, context):
                yield chunk

    async def _generate_chat_stream(
        self, prompt: str, context: Dict[str, Any]
    ) -> AsyncIterator[str]:
        """Generate using the streaming chat API.

        Args:
            prompt: The prompt to generate a response for
            context: Additional context for the generation

        Yields:
            Text chunks as they are generated
        """
        messages = context.get("messages", [])

        # If no messages provided, create a simple user message
        if not messages:
            messages = [{"role": "user", "content": prompt}]

        # Prepare request payload
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": context.get("temperature", self.temperature),
                "num_predict": context.get("max_tokens", self.token_limit),
            },
        }

        # Add system message if provided
        if "system_message" in context:
            payload["system"] = context["system_message"]

        # Make the API request
        try:
            async with self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        f"Ollama chat stream API error: {response.status} - {error_text}"
                    )
                    yield f"Error: {error_text}"
                    return

                # Process the streaming response
                async for line in response.content.iter_lines():
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSON from stream: {line}")
                        continue
        except asyncio.TimeoutError:
            logger.error(
                f"Timeout during streaming chat generation after {self.timeout}s"
            )
            yield "\n[Error: Generation timed out]"
        except Exception as e:
            logger.exception(f"Error during streaming chat generation: {str(e)}")
            yield f"\n[Error: {str(e)}]"

    # Method _prepare_request_data removed as it's no longer needed -
    # Request payload preparation is now done directly in _generate_chat and _generate_completion

    async def _generate_completion_stream(
        self, prompt: str, context: Dict[str, Any]
    ) -> AsyncIterator[str]:
        """Generate using the streaming completion API.

        Args:
            prompt: The prompt to generate a response for
            context: Additional context for the generation

        Yields:
            Text chunks as they are generated
        """
        # Prepare request payload
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": context.get("temperature", self.temperature),
                "num_predict": context.get("max_tokens", self.token_limit),
            },
        }

        # Add system message if provided
        if "system_message" in context:
            payload["system"] = context["system_message"]

        # Make the API request
        try:
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        f"Ollama generate stream API error: {response.status} - {error_text}"
                    )
                    yield f"Error: {error_text}"
                    return

                # Process the streaming response
                async for line in response.content.iter_lines():
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSON from stream: {line}")
                        continue
        except asyncio.TimeoutError:
            logger.error(
                f"Timeout during streaming completion generation after {self.timeout}s"
            )
            yield "\n[Error: Generation timed out]"
        except Exception as e:
            logger.exception(f"Error during streaming completion generation: {str(e)}")
            yield f"\n[Error: {str(e)}]"
