"""Anthropic LLM Provider implementation for goLLM."""

import os
import logging
from typing import Dict, Any, Optional, List

import anthropic
from ..base import BaseLLMProvider

logger = logging.getLogger('gollm.anthropic.provider')

class AnthropicLLMProvider(BaseLLMProvider):
    """LLM Provider for Anthropic's Claude models."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Anthropic provider.
        
        Args:
            config: Configuration dictionary with Anthropic settings
        """
        super().__init__(config)
        self.api_key = config.get('api_key', os.environ.get('ANTHROPIC_API_KEY'))
        self.model = config.get('model', 'claude-2')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 2000)
        
        if not self.api_key:
            raise ValueError("Anthropic API key is required")
        
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
        logger.info(f"Initialized Anthropic provider with model: {self.model}")
    
    async def generate_response(
        self, 
        prompt: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a response using the Anthropic API.
        
        Args:
            prompt: The prompt to generate a response for
            context: Additional context for the generation
            
        Returns:
            Dictionary containing the generated response and metadata
        """
        try:
            # Prepare messages
            messages = [{"role": "user", "content": prompt}]
            
            # Add conversation history if provided
            if context and 'messages' in context:
                messages = context['messages'] + messages
            
            # Convert to Anthropic message format
            system_prompt = ""
            if context and 'system_prompt' in context:
                system_prompt = context['system_prompt']
            
            # Make the API call
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=messages,
                **context.get('generation_params', {}) if context else {}
            )
            
            return {
                "success": True,
                "generated_text": response.content[0].text if response.content else "",
                "model": response.model,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                }
            }
            
        except Exception as e:
            logger.exception("Failed to generate response with Anthropic")
            return {
                "success": False,
                "error": f"Anthropic API error: {str(e)}"
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if the Anthropic API is available.
        
        Returns:
            Dictionary with health check results
        """
        try:
            # Simple API call to check if the service is available
            await self.client.messages.create(
                model=self.model,
                max_tokens=1,
                messages=[{"role": "user", "content": "Hello"}]
            )
            return {
                'status': True,
                'model_available': True,
                'error': None
            }
        except Exception as e:
            return {
                'status': False,
                'model_available': False,
                'error': str(e)
            }
    
    def is_available(self) -> bool:
        """Check if the Anthropic API is available."""
        try:
            import asyncio
            return asyncio.get_event_loop().run_until_complete(
                self.health_check()
            )['status']
        except Exception:
            return False
