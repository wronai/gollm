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
        """Generates code using Ollama with enhanced error handling and logging"""
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
        
        if not self.session:
            error_msg = "OllamaAdapter not properly initialized. Use 'async with' context manager."
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "generated_code": "",
                "raw_response": ""
            }
            
        try:
            # Simplify the prompt to match what worked in curl test
            # Extract just the core instruction from the prompt, removing any metadata
            import re
            core_instruction = re.sub(r'goLLM.*?OUTPUT FORMAT:.*?```python\s*', '', prompt, flags=re.DOTALL).strip()
            simplified_prompt = f"Write a Python function that {core_instruction}"
            logger.debug(f"Using simplified prompt: {simplified_prompt}")
            
            # Prepare the request payload - simplified to match working curl example
            payload = {
                "model": self.config.model,
                "prompt": simplified_prompt,
                "stream": False,
                "options": {
                    "temperature": min(max(0.1, float(self.config.temperature)), 1.0),
                    "num_predict": min(int(self.config.max_tokens), 4000),
                    "stop": ["```", "\n"]
                }
            }
            
            # Remove any None values to avoid sending null in JSON
            payload["options"] = {k: v for k, v in payload["options"].items() if v is not None}
            logger.debug(f"Sending request to Ollama with payload: {json.dumps(payload, indent=2)}")
            
            # Make the API request with a timeout
            try:
                async with asyncio.timeout(self.config.timeout):
                    logger.debug(f"Sending POST request to: {self.config.base_url}/api/generate")
                    logger.debug(f"Request headers: {dict(self.session._default_headers) if hasattr(self.session, '_default_headers') else 'No default headers'}")
                    
                    async with self.session.post(
                        f"{self.config.base_url}/api/generate",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                    ) as response:
                        logger.debug(f"Received response status: {response.status}")
                        logger.debug(f"Response headers: {dict(response.headers)}")
                        
                        # Get raw response text first for debugging
                        raw_response_text = await response.text()
                        logger.debug(f"Raw response text (first 500 chars): {raw_response_text[:500]}")
                        
                        if response.status != 200:
                            error_msg = f"Ollama API error: {response.status} - {raw_response_text}"
                            logger.error(error_msg)
                            return {
                                "success": False,
                                "error": error_msg,
                                "generated_code": "",
                                "raw_response": raw_response_text
                            }
                        
                        try:
                            result = await response.json()
                            logger.debug(f"Parsed Ollama response type: {type(result)}")
                            logger.debug(f"Response keys: {list(result.keys())}")
                            
                            # Log the full response structure
                            logger.debug("Response structure:")
                            for key, value in result.items():
                                logger.debug(f"  {key}: {type(value)} (length: {len(str(value)) if hasattr(value, '__len__') else 'N/A'})")
                                if key == 'response':
                                    logger.debug(f"  Response content (first 500 chars): {str(value)[:500]}")
                            
                            logger.debug(f"Full response (first 1000 chars): {str(result)[:1000]}")
                            
                            # Extract the generated text from the response
                            generated_text = result.get('response', '')
                            if not generated_text:
                                error_msg = "Empty 'response' field in Ollama API response. "
                                error_msg += f"This might be due to the model not generating any output. "
                                error_msg += f"Model: {self.config.model}, Prompt length: {len(simplified_prompt)}"
                                logger.error(error_msg)
                                logger.debug(f"Full response: {result}")
                                
                                # Try to get more detailed error information
                                if 'error' in result:
                                    error_msg += f"\nError details: {result['error']}"
                                    
                                return {
                                    "success": False,
                                    "error": error_msg,
                                    "generated_code": "",
                                    "raw_response": raw_response_text,
                                    "debug_info": {
                                        "model": self.config.model,
                                        "prompt_length": len(simplified_prompt),
                                        "response_keys": list(result.keys()) if isinstance(result, dict) else ""
                                    }
                                }
                                
                            # Try to extract code from the response
                            extracted_code = self._extract_code_from_response(generated_text)
                            if not extracted_code:
                                logger.warning("No code could be extracted from the response")
                                extracted_code = generated_text  # Fall back to full response
                                
                            return {
                                "success": True,
                                "generated_code": extracted_code,
                                "raw_response": generated_text,
                                "model_info": {
                                    "provider": "ollama",
                                    "model": self.config.model,
                                    "tokens_used": result.get("eval_count", 0)
                                }
                            }
                            
                        except json.JSONDecodeError as e:
                            error_msg = f"Failed to parse Ollama API response: {e}"
                            logger.error(f"{error_msg}. Response: {raw_response_text}")
                            return {
                                "success": False,
                                "error": error_msg,
                                "generated_code": "",
                                "raw_response": raw_response_text
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
        """Formatuje prompt dla Ollama z kontekstem goLLM"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Build context string if available
        context_str = ""
        if context:
            context_str = "\nAdditional context for this task:\n"
            for key, value in context.items():
                context_str += f"- {key}: {value}\n"
        
        # Format the prompt with explicit instructions using a raw string
        example_code = (
            '# Example function with type hints and docstring\n'
            'def example_function(param1: str, param2: int) -> bool:\n'
            '    \"\"\"Example function with proper documentation.\n\n'
            '    Args:\n'
            '        param1: Description of param1\n'
            '        param2: Description of param2\n\n'
            '    Returns:\n'
            '        bool: Description of return value\n'
            '    \"\"\"\n'
            '    try:\n'
            '        # Function implementation\n'
            '        return True\n'
            '    except Exception as e:\n'
            '        import logging\n'
            '        logging.error(f\"An error occurred: {e}\")\n'
            '        return False'
        )

        prompt = (
            f"You are an expert Python developer. Your task is to generate "
            f"high-quality, production-ready Python code based on the following request.\n\n"
            f"TASK:\n{user_prompt}\n\n{context_str}\n"
            f"INSTRUCTIONS:\n"
            f"1. Generate complete, working Python code that solves the task.\n"
            f"2. Include all necessary imports, functions, and classes.\n"
            f"3. Follow these coding standards:\n"
            f"   - PEP 8 style guidelines\n"
            f"   - Type hints for all function parameters and return values\n"
            f"   - Comprehensive docstrings for all functions and classes\n"
            f"   - Proper error handling\n"
            f"   - Logging instead of print statements\n"
            f"   - Keep functions focused and under 50 lines\n\n"
            f"IMPORTANT: Your response MUST be a markdown code block starting with ```python and "
            f"ending with ```. Do not include any explanations or text outside the code block.\n\n"
            f"Here's an example of the expected format:\n\n"
            f"```python\n{example_code}\n```\n\n"
            f"Now, please provide the Python code for: {user_prompt}"
        )
        
        logger.debug(f"Formatted prompt (first 200 chars): {prompt[:200]}...")
        return prompt
    
    def _extract_code_from_response(self, response_text: str) -> str:
        """Extracts Python code from Ollama's response, handling various formats."""
        import re
        import logging
        logger = logging.getLogger(__name__)
        
        if not response_text or not isinstance(response_text, str):
            logger.warning("Received empty or invalid response text")
            return ""
            
        logger.debug(f"Extracting code from response. Response length: {len(response_text)} characters")
        logger.debug(f"Response content (first 500 chars): {response_text[:500]}...")
        
        # First, try to find markdown code blocks with optional language specifier
        code_blocks = re.findall(r'```(?:python\n)?(.*?)```', response_text, re.DOTALL)
        if code_blocks:
            logger.debug(f"Found {len(code_blocks)} code blocks in response")
            code = code_blocks[0].strip()
            logger.debug(f"Extracted code block (first 200 chars): {code[:200]}...")
            return code
            
        # Try to find code blocks without backticks (sometimes Ollama returns just the code)
        logger.debug("No fenced code blocks found, looking for indented code...")
        
        # Try to find function or class definitions
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
        
        # If we still don't have code, check if the whole response looks like code
        logger.debug("No clear code blocks found, checking if entire response is code...")
        lines = [line.strip() for line in response_text.strip().split('\n') if line.strip()]
        if len(lines) > 2:
            # Check if first few lines contain Python keywords
            python_keywords = ['def ', 'class ', 'import ', 'from ', 'return ']
            if any(any(kw in line for kw in python_keywords) for line in lines[:3]):
                logger.debug("Response appears to be raw Python code")
                return '\n'.join(lines)
                
            # Check for indented blocks that look like code
            if any(line.startswith(('    ', '\t')) for line in lines[1:5]):
                logger.debug("Found indented block that looks like code")
                return '\n'.join(lines)
            
        logger.warning("No valid Python code found in response")
        logger.debug(f"Full response that couldn't be parsed: {response_text}")
        return ""

class OllamaLLMProvider:
    """Provider LLM dla Ollama - kompatybilny z interfejsem goLLM"""
    
    def __init__(self, config: Dict[str, Any]):
        ollama_config = OllamaConfig(
            base_url=config.get('base_url', 'http://localhost:11434'),
            model=config.get('model_name', 'codellama:7b'),
            timeout=config.get('timeout', 60),
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
