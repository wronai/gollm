# src/gollm/llm/ollama_adapter.py
import asyncio
import json
import os
import aiohttp
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

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
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
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
                        return [model['name'] for model in data.get('models', [])]
        except Exception:
            pass
        return []
    
    async def generate_code(self, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate code using Ollama with enhanced error handling and logging
        
        Args:
            prompt: The prompt to generate code from
            context: Additional context for the prompt
            
        Returns:
            Dict containing the generated code and metadata
        """
        import logging
        import json
        from datetime import datetime
        
        # Configure logger with file handler
        logger = logging.getLogger('gollm.ollama')
        logger.setLevel(logging.DEBUG)
        
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
        
        # Add file handler if not already added
        if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
            log_file = f"logs/ollama_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            # Also add console handler for immediate feedback
            console = logging.StreamHandler()
            console.setLevel(logging.INFO)
            logger.addHandler(console)
        
        logger.debug(f"Generating code with Ollama model: {self.config.model}")
        
        # Format the prompt for the model
        formatted_prompt = self._format_prompt_for_ollama(prompt, context or {})
        
        # Prepare the request payload - enable streaming for better performance
        payload = {
            "model": self.config.model,
            "prompt": formatted_prompt,
            "stream": True,  # Enable streaming for better performance
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
                "stop": ["```", "\n"]  # Stop on code block end or newline
            },
            "system": (
                "You are a helpful coding assistant. Generate clean, well-documented Python code "
                "that follows best practices. Include type hints, docstrings, and error handling "
                "where appropriate. Only respond with the code, no explanations or additional text."
            )
        }
        
        # Log the request payload (without the full prompt to avoid cluttering logs)
        log_payload = payload.copy()
        log_payload["prompt"] = f"[PROMPT LENGTH: {len(formatted_prompt)} chars]"
        logger.debug(f"Sending request to Ollama API: {json.dumps(log_payload, indent=2)}")
        
        try:
            # Make the API request
            url = f"{self.config.base_url}/api/generate"
            headers = {"Content-Type": "application/json"}
            
            # Log the full URL and headers for debugging
            logger.debug(f"Sending POST request to: {url}")
            logger.debug(f"Request headers: {headers}")
            
            full_response = ""
            raw_response_text = ""
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    # Log response status and headers
                    logger.debug(f"Received response status: {response.status}")
                    logger.debug(f"Response headers: {dict(response.headers)}")
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ollama API error: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"Ollama API error: {response.status} - {error_text}",
                            "generated_code": "",
                            "raw_response": error_text
                        }
                    
                    # Process streaming response
                    async for line in response.content:
                        if line:
                            try:
                                chunk = json.loads(line)
                                if 'response' in chunk:
                                    full_response += chunk['response']
                                    
                                # Check if this is the final chunk
                                if chunk.get('done', False):
                                    logger.debug("Received final chunk from streaming response")
                                    break
                                    
                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse chunk: {line}")
                    
            # Log the full response for debugging
            logger.debug(f"Full response from Ollama API: {full_response}")
            
            if not full_response.strip():
                error_msg = f"Empty response from Ollama API. Model: {self.config.model}, Prompt length: {len(formatted_prompt)}"
                logger.warning(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "generated_code": "",
                    "raw_response": full_response
                }
            
            # Extract code from the response
            extracted_code = self._extract_code_from_response(full_response)
            
            # If no code was extracted, try to clean up the response
            if not extracted_code and full_response.strip():
                logger.warning("No code blocks found in response, using full response as code")
                extracted_code = full_response.strip()
            
            return {
                "success": True,
                "generated_code": extracted_code,
                "raw_response": full_response,
                "model": self.config.model
            }
            
        except asyncio.TimeoutError:
            error_msg = f"Ollama API request timed out after {self.config.timeout} seconds"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "generated_code": "",
                "raw_response": ""
            }
            
        except Exception as e:
            error_msg = f"Unexpected error in generate_code: {str(e)}"
            logger.exception(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "generated_code": "",
                "raw_response": str(e)
            }
    
    def _format_prompt_for_ollama(self, user_prompt: str, context: Dict[str, Any]) -> str:
        """Formats the prompt for Ollama with goLLM context and explicit instructions.
        
        Args:
            user_prompt: The user's original prompt
            context: Additional context for the task
            
        Returns:
            Formatted prompt string with clear instructions
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Build context string if available
        context_str = ""
        if context:
            context_str = "\n## Additional Context\n"
            for key, value in context.items():
                context_str += f"- {key}: {value}\n"
        
        # Format the prompt with explicit instructions
        # Using a list of lines to avoid string formatting issues
        prompt_lines = [
            "# PYTHON CODE ONLY - NO EXPLANATIONS, NO MARKDOWN, NO COMMENTS\n",
            "# Your response will be directly executed as Python code.\n",
            "# Only include valid Python code, nothing else.\n\n",
            "# TASK:",
            str(user_prompt),
            str(context_str) if context_str else "",
            "",
            "# INSTRUCTIONS:",
            "# 1. Write complete, working Python 3 code that solves the task",
            "# 2. Include all necessary imports at the top",
            "# 3. Add type hints for all function parameters and return values",
            "# 4. Include docstrings using Google-style format",
            "# 5. Add error handling with try/except blocks",
            "# 6. Include example usage in a `if __name__ == '__main__':` block\n\n"
        ]
        
        # Join the lines to create the final prompt
        formatted_prompt = "\n".join(line for line in prompt_lines if line is not None)
        
        logger.debug(f"Formatted prompt (first 200 chars): {formatted_prompt[:200]}...")
        return formatted_prompt
    
    def _extract_code_from_response(self, response_text: str) -> str:
        """Extracts Python code from Ollama's response, handling various formats.
        
        Args:
            response_text: The raw response text from Ollama
            
        Returns:
            Extracted Python code as a string
        """
        import re
        import logging
        logger = logging.getLogger(__name__)
        
        if not response_text or not isinstance(response_text, str):
            logger.warning("Received empty or invalid response text")
            return ""
            
        logger.debug(f"Extracting code from response. Response length: {len(response_text)} characters")
        logger.debug(f"Response content (first 500 chars): {response_text[:500]}...")
        
        # Try to extract code from markdown code blocks first
        code_blocks = re.findall(r'```(?:python)?\s*([\s\S]*?)\s*```', response_text, re.IGNORECASE)
        if code_blocks:
            logger.debug(f"Found {len(code_blocks)} code blocks in response")
            # Join all code blocks with double newlines in between
            return '\n\n'.join(block.strip() for block in code_blocks if block.strip())
            
        # If no code blocks found, try to extract any Python code between special markers
        if '[PYTHON]' in response_text and '[/PYTHON]' in response_text:
            logger.debug("Extracting code from [PYTHON] tags")
            code = re.search(r'\[PYTHON\]([\s\S]*?)\[/PYTHON\]', response_text, re.IGNORECASE)
            if code:
                return code.group(1).strip()
                
        # If no special markers, try to extract code between ```python and ```
        if '```python' in response_text and '```' in response_text:
            logger.debug("Extracting code from triple backticks")
            code = re.search(r'```python\s*([\s\S]*?)\s*```', response_text)
            if code:
                return code.group(1).strip()
                
        # If no code blocks found, try to find indented blocks that look like code
        logger.debug("No clear code blocks found, checking if entire response is code...")
        
        # Check if the response looks like code (contains Python keywords and proper indentation)
        python_keywords = [
            'def ', 'class ', 'import ', 'from ', 'return ', 'async def ', 
            'async with ', 'if ', 'for ', 'while ', 'try:', 'except ', 'with ',
            'def\n', 'class\n', 'import\n', 'from\n', 'return\n', 'async def\n',
            'async with\n', 'if\n', 'for\n', 'while\n', 'try:\n', 'except\n', 'with\n'
        ]
        
        # Check for Python shebang or common imports
        if (any(keyword in response_text for keyword in python_keywords) or
            response_text.lstrip().startswith('#!') or
            'import ' in response_text or 'def ' in response_text or 'class ' in response_text):
            logger.debug("Response appears to be raw Python code")
            return response_text.strip()
            
        # Try to extract any code-like content
        logger.debug("Trying to extract any code-like content...")
        # Look for lines that look like code (start with def, class, import, etc.)
        code_lines = []
        in_code_block = False
        
        for line in response_text.split('\n'):
            stripped = line.strip()
            if not stripped:
                continue
                
            # Check if this line starts a code block
            if any(stripped.startswith(keyword) for keyword in python_keywords):
                in_code_block = True
                
            # If we're in a code block, add the line
            if in_code_block:
                # Check if this looks like the end of a function/class
                if stripped == '```' or stripped == '```python' or stripped == '```py':
                    in_code_block = False
                else:
                    code_lines.append(line)
        
        if code_lines:
            logger.debug(f"Extracted {len(code_lines)} lines of potential code")
            return '\n'.join(code_lines).strip()
            
        # If all else fails, return the entire response
        logger.debug("No code found, returning entire response")
        return response_text.strip()
            
        logger.debug(f"Extracting code from response. Response length: {len(response_text)} characters")
        logger.debug(f"Response content (first 500 chars): {response_text[:500]}...")
        
        # Clean up the response text
        response_text = response_text.strip()
        
        # 1. First try to find markdown code blocks with optional language specifier
        code_blocks = re.findall(r'```(?:python\n)?(.*?)```', response_text, re.DOTALL)
        if code_blocks:
            logger.debug(f"Found {len(code_blocks)} code blocks in response")
            code = code_blocks[0].strip()
            logger.debug(f"Extracted code block (first 200 chars): {code[:200]}...")
            return code
            
        # 2. Try to find code blocks with [PYTHON]...[/PYTHON] tags
        python_blocks = re.findall(r'\[PYTHON\](.*?)\[/PYTHON\]', response_text, re.DOTALL | re.IGNORECASE)
        if python_blocks:
            logger.debug(f"Found {len(python_blocks)} Python blocks in response")
            code = python_blocks[0].strip()
            logger.debug(f"Extracted Python block (first 200 chars): {code[:200]}...")
            return code
            
        # 3. Try to find code blocks with [CODE]...[/CODE] tags
        code_blocks = re.findall(r'\[CODE\](.*?)\[/CODE\]', response_text, re.DOTALL | re.IGNORECASE)
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
            r'(^import\s+\w+(?:\s*,\s*\w+)*\s*$|^from\s+\w+\s+import\s+\w+(?:\s*,\s*\w+)*\s*$)',
            # Any line that looks like code (has indentation and ends with a colon)
            r'(^\s+\w+.*:\s*$\n(?:\s+.+\n)*)'
        ]
        
        for pattern in patterns:
            try:
                matches = re.findall(pattern, response_text, re.MULTILINE)
                if matches:
                    logger.debug(f"Found {len(matches)} matches with pattern: {pattern[:50]}...")
                    code = '\n'.join(match.strip() for match in matches if match.strip())
                    if code:
                        logger.debug(f"Extracted code (first 200 chars): {code[:200]}...")
                        return code
            except Exception as e:
                logger.warning(f"Error processing pattern {pattern}: {str(e)}")
        
        # 5. If we still don't have code, check if the whole response looks like code
        logger.debug("No clear code blocks found, checking if entire response is code...")
        lines = [line for line in response_text.split('\n') if line.strip()]
        
        if len(lines) > 2:
            # Check if first few lines contain Python keywords
            if any(any(kw in line for kw in python_keywords) for line in lines[:3]):
                logger.debug("Response appears to be raw Python code")
                return '\n'.join(lines)
                
            # Check for indented blocks that look like code
            if any(line.startswith(('    ', '\t')) for line in lines[1:5]):
                logger.debug("Found indented block that looks like code")
                return '\n'.join(lines)
                
            # Check for lines that look like code (contain Python keywords)
            python_code_lines = [line for line in lines if any(kw in line for kw in python_keywords)]
            if len(python_code_lines) > 1:
                logger.debug("Found multiple lines that look like Python code")
                return '\n'.join(lines)
            
        # 6. If all else fails, try to extract anything that looks like code
        logger.debug("Trying to extract any code-like content...")
        code_snippets = []
        in_code_block = False
        code_block = []
        
        for line in response_text.split('\n'):
            line = line.rstrip()
            
            # Check for code block start/end
            if line.strip().startswith('```'):
                if in_code_block and code_block:
                    code_snippets.append('\n'.join(code_block))
                    code_block = []
                in_code_block = not in_code_block
                continue
                
            if in_code_block:
                code_block.append(line)
            elif any(kw in line for kw in python_keywords):
                code_block.append(line)
                
        if code_block:
            code = '\n'.join(code_block).strip()
            if code:
                logger.debug(f"Extracted potential code (first 200 chars): {code[:200]}...")
                return code
        
        logger.warning("No valid Python code found in response")
        logger.debug(f"Full response that couldn't be parsed: {response_text}")
        return ""

class OllamaLLMProvider:
    """Provider LLM dla Ollama - kompatybilny z interfejsem goLLM"""
    
    def __init__(self, config: Dict[str, Any]):
        ollama_config = OllamaConfig(
            base_url=config.get('base_url', 'http://localhost:11434'),
            # Using llama3 as it's a capable model for code generation
            model=config.get('model_name', 'llama3:latest'),
            timeout=config.get('timeout', 120),  # Increased timeout for code generation
            max_tokens=config.get('token_limit', 4000),
            temperature=config.get('temperature', 0.1)
        )
        self.adapter = OllamaAdapter(ollama_config)
    
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generates a response compatible with the goLLM LLM interface"""
        import logging
        import json
        import traceback
        logger = logging.getLogger(__name__)
        
        try:
            if not context:
                context = {}
                
            logger.info(f"Generating response with prompt (truncated): {prompt[:200]}...")
            logger.debug(f"Full prompt: {prompt}")
            logger.debug(f"Context: {json.dumps(context, indent=2)}")
            logger.debug(f"Full prompt: {prompt}")
            logger.debug(f"Context keys: {list(context.keys())}")
            
            async with self.adapter as adapter:
                logger.info(f"Sending request to Ollama with model: {adapter.config.model}")
                logger.debug(f"Adapter config: {adapter.config}")
                
                # Log the full request payload for debugging
                request_payload = {
                    "prompt": prompt[:500] + "..." if len(prompt) > 500 else prompt,
                    "context_keys": list(context.keys())
                }
                logger.debug(f"Request payload: {json.dumps(request_payload, indent=2)}")
                
                # Make the actual API call
                result = await adapter.generate_code(prompt, context)
                
                # Log the raw response for debugging
                logger.debug(f"Raw response from Ollama: {json.dumps(result, indent=2) if isinstance(result, dict) else result}")
                
                if not result or not isinstance(result, dict):
                    raise ValueError(f"Invalid response format from Ollama: {result}")
                
                logger.info(f"Received response from Ollama, success: {result.get('success', False)}")
                logger.debug(f"Response keys: {list(result.keys())}")
                
                if not result.get("success", False):
                    error_msg = result.get("error", "Unknown error from Ollama")
                    logger.error(f"Ollama generation failed: {error_msg}")
                    return {
                        "generated_code": "",
                        "explanation": f"Error: {error_msg}",
                        "success": False,
                        "error": error_msg,
                        "model_info": {
                            "provider": "ollama",
                            "model": adapter.config.model,
                            "tokens_used": 0
                        }
                    }
                
                generated_code = result.get("generated_code", "")
                if not generated_code.strip():
                    logger.warning("Received empty generated code from Ollama")
                
                response = {
                    "generated_code": generated_code,
                    "explanation": "Code generated by Ollama",
                    "success": True,
                    "error": None,
                    "model_info": {
                        "provider": "ollama",
                        "model": adapter.config.model,
                        "tokens_used": result.get("tokens_used", 0)
                    }
                }
                
                logger.debug(f"Successfully generated response with {len(generated_code)} characters")
                return response
                
        except Exception as e:
            logger.exception("Error in OllamaLLMProvider.generate_response")
            return {
                "generated_code": "",
                "explanation": f"Error during code generation: {str(e)}",
                "success": False,
                "error": str(e),
                "model_info": {
                    "provider": "ollama",
                    "model": getattr(self.adapter, 'config', {}).get('model', 'unknown'),
                    "tokens_used": 0
                }
            }
    
    async def is_available(self) -> bool:
        """Sprawdza dostępność Ollama"""
        return await self.adapter.is_available()
