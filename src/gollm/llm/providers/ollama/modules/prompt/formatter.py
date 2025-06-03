"""Prompt formatting module for Ollama adapter."""

import logging
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger('gollm.ollama.prompt')

class PromptFormatter:
    """Handles formatting of prompts for different model types and use cases."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the prompt formatter.
        
        Args:
            config: Configuration dictionary with formatting options
        """
        self.config = config
        self.show_prompt = config.get('show_prompt', False)
    
    def format_completion_prompt(self, prompt: str, system_message: Optional[str] = None) -> str:
        """Format a prompt for completion-style models.
        
        Args:
            prompt: The user prompt
            system_message: Optional system message to prepend
            
        Returns:
            Formatted prompt string
        """
        formatted_prompt = prompt
        
        # Add system message if provided
        if system_message:
            formatted_prompt = f"{system_message}\n\n{formatted_prompt}"
        
        # Log the prompt if enabled
        if self.show_prompt:
            logger.info(f"Formatted completion prompt:\n{formatted_prompt}")
        else:
            # Log a truncated version
            truncated = formatted_prompt[:100] + "..." if len(formatted_prompt) > 100 else formatted_prompt
            logger.debug(f"Prompt (truncated): {truncated}")
            
        return formatted_prompt
    
    def format_chat_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Format chat messages for chat-style models.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            
        Returns:
            Formatted list of message dictionaries
        """
        # Ensure all messages have the required fields
        formatted_messages = []
        for msg in messages:
            if 'role' not in msg or 'content' not in msg:
                logger.warning(f"Skipping malformed message: {msg}")
                continue
                
            # Normalize role names
            role = msg['role'].lower()
            if role not in ['system', 'user', 'assistant']:
                logger.warning(f"Converting unknown role '{role}' to 'user'")
                role = 'user'
                
            formatted_messages.append({
                'role': role,
                'content': msg['content']
            })
        
        # Log the messages if enabled
        if self.show_prompt:
            logger.info(f"Formatted chat messages:\n{formatted_messages}")
        else:
            # Log a summary
            roles = [msg['role'] for msg in formatted_messages]
            logger.debug(f"Chat messages: {len(formatted_messages)} messages with roles {roles}")
            
        return formatted_messages
    
    def get_prompt_metadata(self, prompt: Union[str, List[Dict[str, str]]]) -> Dict[str, Any]:
        """Extract metadata from a prompt for logging and analysis.
        
        Args:
            prompt: Either a string prompt or a list of chat messages
            
        Returns:
            Dictionary of metadata about the prompt
        """
        metadata = {}
        
        if isinstance(prompt, str):
            # Text completion prompt
            metadata['type'] = 'completion'
            metadata['length'] = len(prompt)
            metadata['token_estimate'] = len(prompt.split()) * 1.3  # Rough estimate
        else:
            # Chat messages
            metadata['type'] = 'chat'
            metadata['message_count'] = len(prompt)
            metadata['roles'] = [msg.get('role', 'unknown') for msg in prompt]
            
            # Calculate total content length
            total_length = sum(len(msg.get('content', '')) for msg in prompt)
            metadata['length'] = total_length
            metadata['token_estimate'] = total_length / 4  # Rough estimate
            
        return metadata
