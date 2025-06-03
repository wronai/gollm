"""Generator module for Ollama LLM operations."""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, AsyncIterator, List

import aiohttp

logger = logging.getLogger('gollm.ollama.generation')

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
        self.base_url = config.get('base_url', 'http://localhost:11434')
        self.model_name = config.get('model', 'codellama:7b')
        self.timeout = config.get('timeout', 60)
        self.token_limit = config.get('max_tokens', 4000)
        self.temperature = config.get('temperature', 0.1)
        self.api_type = config.get('api_type', 'chat')
    
    async def generate(self, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a response using the Ollama API.
        
        Args:
            prompt: The prompt to generate a response for
            context: Additional context for the generation
            
        Returns:
            Dictionary containing the generated response and metadata
        """
        start_time = time.time()
        context = context or {}
        
        # Determine which API endpoint to use
        if self.api_type == 'chat':
            result = await self._generate_chat(prompt, context)
        else:
            result = await self._generate_completion(prompt, context)
            
        # Calculate metrics
        end_time = time.time()
        duration = end_time - start_time
        
        # Add metadata to result
        result['metadata'] = {
            'duration': duration,
            'model': self.model_name,
            'api_type': self.api_type,
            'timestamp': end_time
        }
        
        return result
    
    async def _generate_chat(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate using the chat API.
        
        Args:
            prompt: The prompt to generate a response for
            context: Additional context for the generation
            
        Returns:
            Dictionary with the generated response
        """
        messages = context.get('messages', [])
        
        # If no messages provided, create a simple user message
        if not messages:
            messages = [{"role": "user", "content": prompt}]
        
        # Prepare request payload
        payload = {
            "model": context.get('model', self.model_name),
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": context.get('temperature', self.temperature),
                "num_predict": context.get('max_tokens', self.token_limit)
            }
        }
        
        # Add system message if provided
        if 'system_message' in context:
            payload['system'] = context['system_message']
            
        # Make the API request
        try:
            logger.debug(f"Sending chat request to Ollama API: {json.dumps(payload, indent=2)}")
            
            async with self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Ollama chat API error: {response.status} - {error_text}")
                    return {
                        "error": f"API error: {response.status}",
                        "details": error_text,
                        "generated_text": "",
                        "text": ""
                    }
                    
                result = await response.json()
                logger.debug(f"Chat API raw response: {json.dumps(result, indent=2)}")
                
                # Extract the response content - the API might return different formats
                generated_text = ""
                
                # Try to extract from standard chat format first
                if "message" in result and "content" in result["message"]:
                    generated_text = result["message"]["content"]
                # If not found, try to extract from response field (some Ollama versions)
                elif "response" in result:
                    generated_text = result["response"]
                
                logger.debug(f"Extracted chat text (length: {len(generated_text)}): {generated_text[:100]}...")
                
                return {
                    "generated_text": generated_text,
                    "text": generated_text,  # For consistency with the _generate_completion method
                    "raw_response": result,
                    "finish_reason": result.get("done", True),
                    "success": True
                }
        except asyncio.TimeoutError:
            logger.error(f"Timeout during chat generation after {self.timeout}s")
            return {
                "error": "Timeout",
                "details": f"Request timed out after {self.timeout} seconds",
                "generated_text": ""
            }
        except Exception as e:
            logger.exception(f"Error during chat generation: {str(e)}")
            return {
                "error": "Exception",
                "details": str(e),
                "generated_text": ""
            }
    
    async def _generate_completion(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate using the completion API.
        
        Args:
            prompt: The prompt to generate a response for
            context: Additional context for the generation
            
        Returns:
            Dictionary containing the generated text and metadata
        """
        # Prepare request payload
        payload = {
            "model": context.get('model', self.model_name),
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": context.get('temperature', self.temperature),
                "num_predict": context.get('max_tokens', self.token_limit)
            }
        }
        
        # Add system message if provided
        if 'system_message' in context:
            payload['system'] = context['system_message']
            
        # Make the API request
        try:
            logger.debug(f"Sending completion request to Ollama API: {json.dumps(payload, indent=2)}")
            
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Ollama completion API error: {response.status} - {error_text}")
                    return {
                        "error": f"API error: {response.status}",
                        "details": error_text,
                        "generated_text": "",
                        "text": ""
                    }
                    
                result = await response.json()
                logger.debug(f"Completion API raw response: {json.dumps(result, indent=2)}")
                
                # Extract the response content
                generated_text = result.get("response", "")
                logger.debug(f"Extracted completion text (length: {len(generated_text)}): {generated_text[:100]}...")
                
                return {
                    "generated_text": generated_text,
                    "text": generated_text,
                    "raw_response": result,
                    "finish_reason": result.get("done", True),
                    "success": True
                }
        except asyncio.TimeoutError:
            logger.error(f"Timeout during completion generation after {self.timeout}s")
            return {
                "error": "Timeout",
                "details": f"Request timed out after {self.timeout} seconds",
                "generated_text": "",
                "text": ""
            }
        except Exception as e:
            logger.exception(f"Error during completion generation: {str(e)}")
            return {
                "error": "Exception",
                "details": str(e),
                "generated_text": "",
                "text": ""
            }
        
        # Apply adaptive timeout if specified in context
        if context.get('adaptive_timeout', False):
            prompt_length = len(prompt)
            if api_type == 'chat' and context.get('messages'):
                # For chat, calculate total content length of all messages
                prompt_length = sum(len(msg.get('content', '')) for msg in context['messages'])
            # Add 1 second per 500 characters with a minimum of base timeout
            additional_time = int(prompt_length / 500)
            timeout = max(self.timeout, self.timeout + additional_time)
            logger.debug(f"Using adaptive timeout of {timeout}s for request (prompt length: {prompt_length})")
            context['timeout'] = timeout  # Pass the adjusted timeout to the generation methods
        
        # Call the appropriate generation method based on API type
        start_time = time.time()
        
        if api_type == 'chat':
            result = await self._generate_chat(prompt, context)
        else:
            result = await self._generate_completion(prompt, context)
        
        # Add metadata
        end_time = time.time()
        duration = end_time - start_time
        
        if 'metadata' not in result:
            result['metadata'] = {}
            
        result['metadata'].update({
            'duration': duration,
            'model': self.model_name,
            'api_type': api_type,
            'timestamp': end_time
        })
        
        return result
    
    async def generate_stream(self, prompt: str, context: Dict[str, Any] = None) -> AsyncIterator[str]:
        """Generate a streaming response using the Ollama API.
        
        Args:
            prompt: The prompt to generate a response for
            context: Additional context for the generation
            
        Yields:
            Text chunks as they are generated
        """
        context = context or {}
        
        # Determine which API endpoint to use
        if self.api_type == 'chat':
            async for chunk in self._generate_chat_stream(prompt, context):
                yield chunk
        else:
            async for chunk in self._generate_completion_stream(prompt, context):
                yield chunk
    
    async def _generate_chat_stream(self, prompt: str, context: Dict[str, Any]) -> AsyncIterator[str]:
        """Generate using the streaming chat API.
        
        Args:
            prompt: The prompt to generate a response for
            context: Additional context for the generation
            
        Yields:
            Text chunks as they are generated
        """
        messages = context.get('messages', [])
        
        # If no messages provided, create a simple user message
        if not messages:
            messages = [{"role": "user", "content": prompt}]
        
        # Prepare request payload
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": context.get('temperature', self.temperature),
                "num_predict": context.get('max_tokens', self.token_limit)
            }
        }
        
        # Add system message if provided
        if 'system_message' in context:
            payload['system'] = context['system_message']
            
        # Make the API request
        try:
            async with self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Ollama chat stream API error: {response.status} - {error_text}")
                    yield f"Error: {error_text}"
                    return
                
                # Process the streaming response
                async for line in response.content.iter_lines():
                    if not line:
                        continue
                        
                    try:
                        data = json.loads(line)
                        if 'message' in data and 'content' in data['message']:
                            yield data['message']['content']
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSON from stream: {line}")
                        continue
        except asyncio.TimeoutError:
            logger.error(f"Timeout during streaming chat generation after {self.timeout}s")
            yield "\n[Error: Generation timed out]"
        except Exception as e:
            logger.exception(f"Error during streaming chat generation: {str(e)}")
            yield f"\n[Error: {str(e)}]"
    
    # Method _prepare_request_data removed as it's no longer needed - 
    # Request payload preparation is now done directly in _generate_chat and _generate_completion
    
    async def _generate_completion_stream(self, prompt: str, context: Dict[str, Any]) -> AsyncIterator[str]:
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
                "temperature": context.get('temperature', self.temperature),
                "num_predict": context.get('max_tokens', self.token_limit)
            }
        }
        
        # Add system message if provided
        if 'system_message' in context:
            payload['system'] = context['system_message']
            
        # Make the API request
        try:
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Ollama generate stream API error: {response.status} - {error_text}")
                    yield f"Error: {error_text}"
                    return
                
                # Process the streaming response
                async for line in response.content.iter_lines():
                    if not line:
                        continue
                        
                    try:
                        data = json.loads(line)
                        if 'response' in data:
                            yield data['response']
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSON from stream: {line}")
                        continue
        except asyncio.TimeoutError:
            logger.error(f"Timeout during streaming completion generation after {self.timeout}s")
            yield "\n[Error: Generation timed out]"
        except Exception as e:
            logger.exception(f"Error during streaming completion generation: {str(e)}")
            yield f"\n[Error: {str(e)}]"