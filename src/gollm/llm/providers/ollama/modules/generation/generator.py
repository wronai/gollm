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
            "model": self.model_name,
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
                        "generated_text": ""
                    }
                    
                result = await response.json()
                
                return {
                    "generated_text": result.get("message", {}).get("content", ""),
                    "raw_response": result,
                    "finish_reason": result.get("done", True)
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
        context = context or {}
        api_type = context.get('api_type', self.api_type)
        
        # Prepare request data
        data = self._prepare_request_data(prompt, context, api_type)
        
        # Determine endpoint based on API type
        endpoint = '/api/chat' if api_type == 'chat' else '/api/generate'
        
        # Calculate adaptive timeout if specified in context
        timeout = self.timeout
        if context.get('adaptive_timeout', False):
            prompt_length = len(prompt)
            if api_type == 'chat' and 'messages' in data:
                # For chat, calculate total content length of all messages
                prompt_length = sum(len(msg.get('content', '')) for msg in data['messages'])
            # Add 1 second per 500 characters with a minimum of base timeout
            additional_time = int(prompt_length / 500)
            timeout = max(self.timeout, self.timeout + additional_time)
            logger.debug(f"Using adaptive timeout of {timeout}s for request (prompt length: {prompt_length})")
        
        try:
            # Send the request with timeout
            start_time = time.time()
            async with self.session.post(
                f"{self.base_url}{endpoint}",
                json=data,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                response_time = time.time() - start_time
                
                # Process the response
                response_data = await response.json()
                logger.debug(f"Raw API response: {json.dumps(response_data, indent=2)}")
                
                # Add metadata
                if 'metadata' not in response_data:
                    response_data['metadata'] = {}
                response_data['metadata']['duration'] = response_time
                
                # Extract the generated text
                generated_text = ""
                if api_type == 'chat':
                    if 'message' in response_data and 'content' in response_data['message']:
                        generated_text = response_data['message']['content']
                    else:
                        logger.warning(f"Could not find 'message.content' in chat response: {response_data}")
                else:
                    if 'response' in response_data:
                        generated_text = response_data['response']
                    else:
                        logger.warning(f"Could not find 'response' in completion response: {response_data}")
                
                # Ensure we have a text field in the response
                response_data['text'] = generated_text
                response_data['generated_text'] = generated_text  # For backward compatibility
                
                logger.debug(f"Extracted text (length: {len(generated_text)}): {generated_text[:100]}...")
                return response_data
                
        except asyncio.TimeoutError:
            logger.error(f"Request timed out after {timeout}s")
            return {
                "success": False,
                "error": f"Request timed out after {timeout}s",
                "metadata": {"duration": timeout}
            }
        except Exception as e:
            logger.exception(f"Error in generate: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "details": f"Exception during generation: {str(e)}",
                "generated_text": ""
            }
    
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
    
    def _prepare_request_data(self, prompt: str, context: Dict[str, Any], api_type: str) -> Dict[str, Any]:
        """Prepare the request data for the Ollama API.
        
        Args:
            prompt: The prompt to generate a response for
            context: Additional context for the generation
            api_type: The API type ('chat' or 'completion')
            
        Returns:
            Dictionary containing the request data
        """
        # Get configuration values from context or use defaults
        temperature = context.get('temperature', self.temperature)
        max_tokens = context.get('max_tokens', self.token_limit)
        
        if api_type == 'chat':
            # Prepare chat request data
            messages = context.get('messages', [])
            
            # If no messages provided, create a simple user message
            if not messages:
                messages = [{"role": "user", "content": prompt}]
                
            data = {
                "model": context.get('model', self.model_name),
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            # Add system message if provided
            if 'system_message' in context:
                data['system'] = context['system_message']
        else:
            # Prepare completion request data
            data = {
                "model": context.get('model', self.model_name),
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            # Add system message if provided
            if 'system_message' in context:
                data['system'] = context['system_message']
                
        return data
    
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