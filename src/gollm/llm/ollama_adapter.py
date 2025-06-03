# src/gollm/llm/ollama_adapter.py
import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger("gollm.ollama")


@dataclass
class OllamaConfig:
    base_url: str = "http://localhost:11434"
    model: str = "codellama:7b"
    timeout: int = 60
    max_tokens: int = 4000
    temperature: float = 0.1


class OllamaAdapter:
    """Adapter dla integracji z Ollama LLM"""

    def __init__(self, config: OllamaConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        trace_config = aiohttp.TraceConfig()

        async def on_request_start(session, trace_config_ctx, params):
            logger.debug(f"Starting request: {params.method} {params.url}")
            trace_config_ctx.start = time.time()

        async def on_request_end(session, trace_config_ctx, params):
            duration = time.time() - trace_config_ctx.start
            logger.debug(
                f"Request finished: {params.method} {params.url} - {params.response.status} in {duration:.2f}s"
            )

        trace_config.on_request_start.append(on_request_start)
        trace_config.on_request_end.append(on_request_end)

        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            trace_configs=[trace_config],
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def is_available(self) -> bool:
        """Sprawdza czy Ollama jest dostępne"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.config.base_url}/api/tags") as response:
                    return response.status == 200
        except Exception:
            return False

    async def list_models(self) -> List[str]:
        """Zwraca listę dostępnych modeli"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.config.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        return [model["name"] for model in data.get("models", [])]
        except Exception:
            pass
        return []

    async def generate_code(
        self, prompt: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate code using Ollama with enhanced error handling and logging

        Args:
            prompt: The prompt to generate code from
            context: Additional context for the prompt

        Returns:
            Dict containing the generated code and metadata
        """
        start_time = time.time()
        logger.debug(f"Starting code generation with model: {self.config.model}")
        logger.debug(f"Prompt (first 200 chars): {prompt[:200]}...")

        # Set timeout from config, with a minimum of 30 seconds
        timeout = aiohttp.ClientTimeout(total=max(30, self.config.timeout))

        # Prepare the payload for completion API
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            },
        }

        # Log the request payload
        logger.debug(f"Sending request to Ollama API with model: {self.config.model}")

        # Send the request to the Ollama API
        url = f"{self.config.base_url}/api/generate"
        headers = {"Content-Type": "application/json"}

        try:
            logger.debug(f"Sending POST request to: {url}")

            # Create a new session for this request
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    response_text = await response.text()
                    logger.debug(f"Received response status: {response.status}")

                    if response.status != 200:
                        try:
                            error_data = await response.json()
                            error_msg = error_data.get("error", "Unknown error")
                            logger.error(
                                f"Ollama API request failed with status {response.status}. Response: {error_msg}"
                            )
                            return {
                                "success": False,
                                "error": f"Ollama API error: {response.status} - {error_msg}",
                                "generated_code": "",
                                "raw_response": str(error_data),
                            }
                        except (json.JSONDecodeError, aiohttp.ContentTypeError) as e:
                            error_text = await response.text()
                            logger.error(
                                f"Failed to parse Ollama API error response: {str(e)}. Raw: {error_text}"
                            )
                            return {
                                "success": False,
                                "error": f"Ollama API error: {response.status} - {error_text}",
                                "generated_code": "",
                                "raw_response": error_text,
                            }

                    result = await response.json()
                    logger.debug(
                        f"Raw response from Ollama: {json.dumps(result, indent=2, ensure_ascii=False)}"
                    )

                    # Extract the generated text from the response
                    generated_text = result.get("response", "")

                    if not generated_text:
                        error_msg = f"Empty response from Ollama API. Model: {self.config.model}"
                        logger.warning(error_msg)
                        return {
                            "success": False,
                            "error": error_msg,
                            "generated_code": "",
                            "raw_response": result,
                        }

                    logger.debug(
                        f"Generated text (first 500 chars): {generated_text[:500]}..."
                    )

                    return {
                        "success": True,
                        "generated_code": generated_text.strip(),
                        "raw_response": result,
                        "model": self.config.model,
                    }

        except asyncio.TimeoutError:
            error_msg = f"Ollama API request timed out after {timeout.total} seconds"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "generated_code": "",
                "raw_response": "",
            }
        except Exception as e:
            error_msg = f"Unexpected error in generate_code: {str(e)}"
            logger.exception(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "generated_code": "",
                "raw_response": "",
            }

    def _format_prompt_for_ollama(
        self, user_prompt: str, context: Dict[str, Any]
    ) -> str:
        """Formats the prompt for Ollama with minimal instructions.

        Args:
            user_prompt: The user's original prompt
            context: Additional context for the task

        Returns:
            Formatted prompt string
        """
        import logging

        logger = logging.getLogger(__name__)

        # Build context string if available
        context_str = ""
        if context:
            context_str = (
                "\n" + "\n".join(f"# {k}: {v}" for k, v in context.items()) + "\n"
            )

        # Simple prompt with just the task and context
        formatted_prompt = f"""{context_str}
# Task:
{user_prompt}

# Python code only:"""

        logger.debug(f"Formatted prompt (first 200 chars): {formatted_prompt[:200]}...")
        return formatted_prompt

    def _extract_code_from_response(self, response_text: str) -> str:
        """Extracts Python code from Ollama's response, handling various formats.

        Args:
            response_text: The raw response text from Ollama

        Returns:
            Extracted Python code as a string
        """
        import logging
        import re

        logger = logging.getLogger(__name__)

        if not response_text or not isinstance(response_text, str):
            logger.warning("Received empty or invalid response text")
            return ""

        logger.debug(
            f"Extracting code from response. Response length: {len(response_text)} characters"
        )
        logger.debug(f"Response content (first 500 chars): {response_text[:500]}...")

        # Try to extract code from markdown code blocks first
        code_blocks = re.findall(
            r"```(?:python)?\s*([\s\S]*?)\s*```", response_text, re.IGNORECASE
        )
        if code_blocks:
            logger.debug(f"Found {len(code_blocks)} code blocks in response")
            # Join all code blocks with double newlines in between
            return "\n\n".join(block.strip() for block in code_blocks if block.strip())

        # If no code blocks found, try to extract any Python code between special markers
        if "[PYTHON]" in response_text and "[/PYTHON]" in response_text:
            logger.debug("Extracting code from [PYTHON] tags")
            code = re.search(
                r"\[PYTHON\]([\s\S]*?)\[/PYTHON\]", response_text, re.IGNORECASE
            )
            if code:
                return code.group(1).strip()

        # If no special markers, try to extract code between ```python and ```
        if "```python" in response_text and "```" in response_text:
            logger.debug("Extracting code from triple backticks")
            code = re.search(r"```python\s*([\s\S]*?)\s*```", response_text)
            if code:
                return code.group(1).strip()

        # If no code blocks found, try to find indented blocks that look like code
        logger.debug(
            "No clear code blocks found, checking if entire response is code..."
        )

        # Check if the response looks like code (contains Python keywords and proper indentation)
        python_keywords = [
            "def ",
            "class ",
            "import ",
            "from ",
            "return ",
            "async def ",
            "async with ",
            "if ",
            "for ",
            "while ",
            "try:",
            "except ",
            "with ",
            "def\n",
            "class\n",
            "import\n",
            "from\n",
            "return\n",
            "async def\n",
            "async with\n",
            "if\n",
            "for\n",
            "while\n",
            "try:\n",
            "except\n",
            "with\n",
        ]

        # Check for Python shebang or common imports
        if (
            any(keyword in response_text for keyword in python_keywords)
            or response_text.lstrip().startswith("#!")
            or "import " in response_text
            or "def " in response_text
            or "class " in response_text
        ):
            logger.debug("Response appears to be raw Python code")
            return response_text.strip()

        # Try to extract any code-like content
        logger.debug("Trying to extract any code-like content...")
        # Look for lines that look like code (start with def, class, import, etc.)
        code_lines = []
        in_code_block = False

        for line in response_text.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue

            # Check if this line starts a code block
            if any(stripped.startswith(keyword) for keyword in python_keywords):
                in_code_block = True

            # If we're in a code block, add the line
            if in_code_block:
                # Check if this looks like the end of a function/class
                if stripped == "```" or stripped == "```python" or stripped == "```py":
                    in_code_block = False
                else:
                    code_lines.append(line)

        if code_lines:
            logger.debug(f"Extracted {len(code_lines)} lines of potential code")
            return "\n".join(code_lines).strip()

        # If all else fails, return the entire response
        logger.debug("No code found, returning entire response")
        return response_text.strip()

        logger.debug(
            f"Extracting code from response. Response length: {len(response_text)} characters"
        )
        logger.debug(f"Response content (first 500 chars): {response_text[:500]}...")

        # Clean up the response text
        response_text = response_text.strip()

        # 1. First try to find markdown code blocks with optional language specifier
        code_blocks = re.findall(r"```(?:python\n)?(.*?)```", response_text, re.DOTALL)
        if code_blocks:
            logger.debug(f"Found {len(code_blocks)} code blocks in response")
            code = code_blocks[0].strip()
            logger.debug(f"Extracted code block (first 200 chars): {code[:200]}...")
            return code

        # 2. Try to find code blocks with [PYTHON]...[/PYTHON] tags
        python_blocks = re.findall(
            r"\[PYTHON\](.*?)\[/PYTHON\]", response_text, re.DOTALL | re.IGNORECASE
        )
        if python_blocks:
            logger.debug(f"Found {len(python_blocks)} Python blocks in response")
            code = python_blocks[0].strip()
            logger.debug(f"Extracted Python block (first 200 chars): {code[:200]}...")
            return code

        # 3. Try to find code blocks with [CODE]...[/CODE] tags
        code_blocks = re.findall(
            r"\[CODE\](.*?)\[/CODE\]", response_text, re.DOTALL | re.IGNORECASE
        )
        if code_blocks:
            logger.debug(f"Found {len(code_blocks)} code blocks in response")
            code = code_blocks[0].strip()
            logger.debug(f"Extracted code block (first 200 chars): {code[:200]}...")
            return code

        # 4. Try to find function or class definitions directly in the response
        patterns = [
            # Function with docstring
            r'(def\s+\w+\s*\([^)]*\)\s*:[^\n]*\n(?:\s*"""(?:.|\n)*?"""\n)?(?:\s*#.*\n)*\s+(?:[^\n]*(?:\n|$))+)',
            # Class with docstring
            r'(class\s+\w+\s*(?:\([^)]*\))?\s*:[^\n]*\n(?:\s*"""(?:.|\n)*?"""\n)?(?:\s*#.*\n)*\s+(?:[^\n]*(?:\n|$))+)',
            # Import statements
            r"(^import\s+\w+(?:\s*,\s*\w+)*\s*$|^from\s+\w+\s+import\s+\w+(?:\s*,\s*\w+)*\s*$)",
            # Any line that looks like code (has indentation and ends with a colon)
            r"(^\s+\w+.*:\s*$\n(?:\s+.+\n)*)",
        ]

        for pattern in patterns:
            try:
                matches = re.findall(pattern, response_text, re.MULTILINE)
                if matches:
                    logger.debug(
                        f"Found {len(matches)} matches with pattern: {pattern[:50]}..."
                    )
                    code = "\n".join(
                        match.strip() for match in matches if match.strip()
                    )
                    if code:
                        logger.debug(
                            f"Extracted code (first 200 chars): {code[:200]}..."
                        )
                        return code
            except Exception as e:
                logger.warning(f"Error processing pattern {pattern}: {str(e)}")

        # 5. If we still don't have code, check if the whole response looks like code
        logger.debug(
            "No clear code blocks found, checking if entire response is code..."
        )
        lines = [line for line in response_text.split("\n") if line.strip()]

        if len(lines) > 2:
            # Check if first few lines contain Python keywords
            if any(any(kw in line for kw in python_keywords) for line in lines[:3]):
                logger.debug("Response appears to be raw Python code")
                return "\n".join(lines)

            # Check for indented blocks that look like code
            if any(line.startswith(("    ", "\t")) for line in lines[1:5]):
                logger.debug("Found indented block that looks like code")
                return "\n".join(lines)

            # Check for lines that look like code (contain Python keywords)
            python_code_lines = [
                line for line in lines if any(kw in line for kw in python_keywords)
            ]
            if len(python_code_lines) > 1:
                logger.debug("Found multiple lines that look like Python code")
                return "\n".join(lines)

        # 6. If all else fails, try to extract anything that looks like code
        logger.debug("Trying to extract any code-like content...")
        code_snippets = []
        in_code_block = False
        code_block = []

        for line in response_text.split("\n"):
            line = line.rstrip()

            # Check for code block start/end
            if line.strip().startswith("```"):
                if in_code_block and code_block:
                    code_snippets.append("\n".join(code_block))
                    code_block = []
                in_code_block = not in_code_block
                continue

            if in_code_block:
                code_block.append(line)
            elif any(kw in line for kw in python_keywords):
                code_block.append(line)

        if code_block:
            code = "\n".join(code_block).strip()
            if code:
                logger.debug(
                    f"Extracted potential code (first 200 chars): {code[:200]}..."
                )
                return code

        logger.warning("No valid Python code found in response")
        logger.debug(f"Full response that couldn't be parsed: {response_text}")
        return ""


class OllamaLLMProvider:
    """LLM Provider for Ollama - compatible with goLLM interface"""

    def __init__(self, config):
        """Initialize the Ollama provider with configuration.

        Args:
            config: Dictionary containing provider configuration
        """
        self.config = config

        # Set default values from config
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.model_name = config.get("model", "deepseek-coder:latest")
        self.timeout = config.get("timeout", 180)
        self.token_limit = config.get("max_tokens", 4000)
        self.temperature = config.get("temperature", 0.1)
        self.api_type = config.get("api_type", "chat")
        self.interactive = config.get("interactive", True)

        logger.debug(f"Initializing OllamaLLMProvider with config: {config}")

        # Initialize the adapter
        self._update_adapter()

        logger.info(
            f"Ollama configuration - URL: {self.base_url}, "
            f"Model: {self.model_name}, "
            f"API Type: {self.api_type}, "
            f"Timeout: {self.timeout}"
        )

    def _update_adapter(self):
        """Update the Ollama adapter with current configuration"""
        ollama_config = OllamaConfig(
            base_url=self.base_url,
            model=self.model_name,
            timeout=self.timeout,
            max_tokens=self.token_limit,
            temperature=self.temperature,
        )
        self.adapter = OllamaAdapter(ollama_config)

    async def _ensure_valid_model(self) -> bool:
        """Ensure the configured model is available.

        Returns:
            bool: True if the model is available, False otherwise
        """
        try:
            models = await self.adapter.list_models()
            if not models:
                logger.error("No models found on the Ollama server")
                return False

            # Check if model exists (with or without tag)
            model_found = any(
                m == self.model_name or m.startswith(f"{self.model_name}:")
                for m in models
            )

            if not model_found:
                logger.warning(
                    f"Configured model '{self.model_name}' not found. "
                    f"Available models: {', '.join(models)}"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating model: {e}", exc_info=True)
            return False

    async def generate_response(
        self, prompt: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generates a response using the Ollama API.

        Args:
            prompt: The prompt to generate a response for
            context: Additional context for the generation

        Returns:
            Dictionary containing the generated response and metadata
        """
        import json
        import logging
        import traceback

        logger = logging.getLogger(__name__)

        # Ensure we have a valid model before proceeding
        if not await self._ensure_valid_model():
            return {
                "success": False,
                "error": "No valid model available. Please check your configuration.",
                "generated_code": "",
                "explanation": "Failed to find a valid model to use for generation.",
                "model_info": {
                    "provider": "ollama",
                    "model": self.model_name,
                    "tokens_used": 0,
                },
            }

            # Use the appropriate API based on configuration
            logger.error(error_msg)

            return {
                "generated_code": "",
                "explanation": f"Ollama service is not available: {health.get('error', 'Unknown error')}",
                "success": False,
                "error": error_msg,
                "model_info": {
                    "provider": "ollama",
                    "model": config_info.get("model", "unknown"),
                    "tokens_used": 0,
                },
            }

        try:
            if not context:
                context = {}

            logger.info(
                f"Generating response with prompt (truncated): {prompt[:200]}..."
            )
            logger.debug(f"Full prompt: {prompt}")
            logger.debug(f"Context: {json.dumps(context, indent=2)}")

            # Get the API type from config (default to 'generate' for backward compatibility)
            api_type = "generate"  # Default
            if hasattr(self, "config"):
                if hasattr(self.config, "get"):  # Dict-like config
                    llm_config = self.config.get("llm_integration", {})
                    providers = llm_config.get("providers", {})
                    provider_config = providers.get("ollama", {})
                    api_type = provider_config.get("api_type", "generate")
                elif hasattr(self.config, "llm_integration"):  # Object-style config
                    llm_config = self.config.llm_integration
                    if hasattr(llm_config, "providers") and hasattr(
                        llm_config.providers, "get"
                    ):
                        provider_config = llm_config.providers.get("ollama", {})
                        if hasattr(provider_config, "get"):
                            api_type = provider_config.get("api_type", "generate")

            logger.debug(f"Using Ollama API type: {api_type}")
            logger.debug(f"Using model: {self.adapter.config.model}")

            # Use the adapter to generate code
            if api_type == "generate":
                response = await self.adapter.generate_code(prompt, context)
            elif api_type == "chat":
                response = await self.adapter.chat(prompt, context)
            else:
                raise ValueError(f"Unsupported API type: {api_type}")

            # Log the response for debugging
            logger.debug(
                f"Raw response from Ollama: {json.dumps(response, indent=2) if isinstance(response, dict) else response}"
            )

            if not response or not isinstance(response, dict):
                error_msg = f"Invalid response format from Ollama: {response}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            if not response.get("success", False):
                error_msg = response.get("error", "Unknown error from Ollama")
                logger.error(f"Ollama generation failed: {error_msg}")
                return {
                    "generated_code": "",
                    "explanation": f"Error: {error_msg}",
                    "success": False,
                    "error": error_msg,
                    "model_info": {
                        "provider": "ollama",
                        "model": self.adapter.config.model,
                        "tokens_used": 0,
                    },
                }

            # Extract the generated code and explanation
            generated_code = response.get("generated_code", "")
            explanation = response.get("explanation", "")

            # If no explanation was provided, create a default one
            if not explanation and generated_code:
                explanation = "Here's the generated code:"

            return {
                "generated_code": generated_code,
                "explanation": explanation,
                "success": True,
                "model_info": {
                    "provider": "ollama",
                    "model": self.adapter.config.model,
                    "tokens_used": response.get("tokens_used", 0),
                },
                "raw_response": response.get("raw_response", ""),
            }

        except Exception as e:
            logger.exception("Error in OllamaLLMProvider.generate_response")
            return {
                "generated_code": "",
                "explanation": f"Error during code generation: {str(e)}",
                "success": False,
                "error": str(e),
                "model_info": {
                    "provider": "ollama",
                    "model": getattr(self.adapter, "config", {}).get(
                        "model", "unknown"
                    ),
                    "tokens_used": 0,
                },
            }

    async def health_check(self) -> Dict[str, Any]:
        """
        Performs a comprehensive health check of the Ollama service.

        Returns:
            Dict containing:
            - status (bool): Overall health status
            - available (bool): If the service is reachable
            - model_available (bool): If the configured model is available
            - error (str): Error message if any
            - config (dict): Current configuration
        """
        # Safely get config values with defaults
        config = getattr(self, "adapter", {}).config
        base_url = getattr(config, "base_url", "http://localhost:11434")
        model = getattr(config, "model", "deepseek-coder:latest")
        timeout = getattr(config, "timeout", 120)

        result = {
            "status": False,
            "available": False,
            "model_available": False,
            "error": None,
            "config": {"base_url": base_url, "model": model, "timeout": timeout},
        }

        try:
            # Check basic connectivity
            try:
                # First check if we can reach the base URL
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{base_url}/api/tags", timeout=5
                    ) as response:
                        if response.status != 200:
                            result["error"] = (
                                f"Ollama API returned status {response.status}"
                            )
                            return result

                        # If we got here, the service is available
                        result["available"] = True

                        # Check if model is available
                        data = await response.json()
                        available_models = [m["name"] for m in data.get("models", [])]

                        # Check for exact match or prefix match
                        model_found = any(
                            m == model or m.startswith(f"{model}:")
                            for m in available_models
                        )

                        if not model_found:
                            result["error"] = (
                                f"Model '{model}' not found in available models. "
                                f"Available models: {', '.join(available_models)}"
                            )
                            return result

                        result["model_available"] = True

            except aiohttp.ClientError as e:
                result["error"] = (
                    f"Failed to connect to Ollama service at {base_url}: {str(e)}"
                )
                return result
            except json.JSONDecodeError as e:
                result["error"] = f"Invalid JSON response from Ollama API: {str(e)}"
                return result
            except Exception as e:
                result["error"] = f"Unexpected error during health check: {str(e)}"
                return result

            # Test a simple request
            try:
                test_prompt = "Respond with just the word 'pong'"
                if hasattr(self.adapter, "chat"):
                    response = await self.adapter.chat(test_prompt, {})
                else:
                    response = await self.adapter.generate_code(test_prompt, {})

                if (
                    not response
                    or not response.get("success")
                    or "pong" not in str(response).lower()
                ):
                    result["error"] = f"Unexpected test response: {response}"
                    return result

            except Exception as e:
                result["error"] = f"Test request failed: {str(e)}"
                return result

            # If we got here, everything is working
            result["status"] = True
            return result

        except Exception as e:
            result["error"] = f"Health check failed: {str(e)}"
            return result

    async def is_available(self):
        """Sprawdza dostępność Ollama"""
        health = await self.health_check()
        return health.get("status", False)
