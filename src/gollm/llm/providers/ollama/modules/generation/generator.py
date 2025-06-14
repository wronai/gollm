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

    def _calculate_timeout(self, prompt: str, context: Dict[str, Any]) -> int:
        """Calculate an appropriate timeout based on prompt length and complexity.

        Args:
            prompt: The prompt to generate a response for
            context: Additional context for the generation

        Returns:
            Timeout in seconds
        """
        # Start with the base timeout
        timeout = self.timeout
        prompt_length = len(prompt)
        
        # For chat, calculate total content length of all messages
        if context.get("messages"):
            prompt_length = sum(len(msg.get("content", "")) for msg in context.get("messages", []))
        
        # Always ensure a minimum timeout regardless of other factors
        min_timeout = 60  # At least 60 seconds for any request
        
        # For code generation, ensure a substantial minimum timeout
        if context.get("is_code_generation", False):
            min_timeout = 180  # At least 3 minutes for code generation
            logger.info(f"Using increased minimum timeout for code generation: {min_timeout}s")
        
        # Calculate adaptive timeout if enabled
        if context.get("adaptive_timeout", True):
            # For longer prompts, add additional time
            if prompt_length > 500:
                # Add 10 seconds for every 1000 chars over 500, up to 2x base timeout
                additional_time = min((prompt_length - 500) / 1000 * 10, timeout)
                timeout = min(timeout * 2, timeout + additional_time)
            
            # Ensure we never go below the minimum timeout
            timeout = max(timeout, min_timeout)
        else:
            # If adaptive timeout is disabled, use the base timeout but ensure minimum
            timeout = max(timeout, min_timeout)
        
        # Add the calculated timeout to the context for logging
        context["calculated_timeout"] = timeout
        logger.info(f"Using timeout: {timeout}s (base: {self.timeout}s, minimum: {min_timeout}s)")
        
        # Round to nearest second and return
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

        # Calculate appropriate timeout before generation
        timeout = self._calculate_timeout(prompt, context)
        # The timeout is already stored in context by _calculate_timeout

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
        logger.info("===== OLLAMA GENERATOR CHAT REQUEST STARTED =====")
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

        # Create a new ClientSession if one wasn't provided
        session = self.session or aiohttp.ClientSession()
        session_created = self.session is None
        
        try:
            # Use the session directly without async context manager
            response = await session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout)
            )
            
            try:
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
                        "success": False
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
                # If not found, try to extract from response field (some Ollama versions)
                elif "response" in result:
                    generated_text = result["response"]
                    logger.info(
                        f"Extracted content from response (length: {len(generated_text)})"
                    )
                else:
                    logger.warning(
                        f"Could not find content in Ollama response. Keys: {list(result.keys())}"
                    )
                    # Try to extract from any field that might contain text
                    for key, value in result.items():
                        if isinstance(value, str) and len(value) > 50:
                            logger.info(
                                f"Found potential content in key '{key}' (length: {len(value)})"
                            )
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
                
            finally:
                # Ensure response is closed
                if not response.closed:
                    await response.release()
                    
        except asyncio.TimeoutError as e:
            logger.error(f"Request to Ollama API timed out after {timeout} seconds")
            return {
                "error": "Timeout",
                "details": f"Request timed out after {timeout} seconds",
                "generated_text": "",
                "text": "",
                "success": False
            }
            
        except Exception as e:
            logger.exception("Unexpected error during Ollama API request")
            return {
                "error": "Exception",
                "details": str(e),
                "generated_text": "",
                "text": "",
                "success": False
            }
            
        finally:
            # Close the session if we created it
            if session_created and not session.closed:
                await session.close()
                


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

        # Create a new ClientSession if one wasn't provided
        session = self.session or aiohttp.ClientSession()
        session_created = self.session is None
        
        try:
            # Make the API request
            response = await session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout),
            )
            
            try:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        f"Ollama completion API error: {response.status} - {error_text}"
                    )
                    return {
                        "error": f"API error: {response.status}",
                        "details": error_text,
                        "generated_text": "",
                        "text": "",
                        "success": False
                    }
                    
                result = await response.json()
                logger.debug(f"Completion API raw response: {json.dumps(result, indent=2)}")
                
                # Extract the response text
                response_text = result.get("response", "")
                
                return {
                    "generated_text": response_text,
                    "text": response_text,
                    "model": result.get("model", self.model_name),
                    "usage": {k: v for k, v in result.items() if k in ["prompt_eval_count", "eval_count"]},
                    "finish_reason": result.get("done", True),
                    "success": True,
                }
                
            finally:
                # Ensure response is closed
                if not response.closed:
                    await response.release()
                    
        except asyncio.TimeoutError as e:
            logger.error(f"Request to Ollama API timed out after {timeout} seconds")
            return {
                "error": "Timeout",
                "details": f"Request timed out after {timeout} seconds",
                "generated_text": "",
                "text": "",
                "success": False
            }
            
        except Exception as e:
            logger.exception("Unexpected error during Ollama API request")
            return {
                "error": "Exception",
                "details": str(e),
                "generated_text": "",
                "text": "",
                "success": False
            }
            
        finally:
            # Close the session if we created it
            if session_created and not session.closed:
                await session.close()

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
