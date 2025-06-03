"""Prompt logging module for Ollama adapter."""

import json
import logging
import time
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger('gollm.ollama.prompt')

class PromptLogger:
    """Handles detailed logging of prompts, responses, and metadata."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the prompt logger.
        
        Args:
            config: Configuration dictionary with logging options
        """
        self.config = config
        self.show_prompt = config.get('show_prompt', False)
        self.show_response = config.get('show_response', False)
        self.show_metadata = config.get('show_metadata', False)
    
    def log_request(self, 
                   prompt: Union[str, List[Dict[str, str]]], 
                   model: str,
                   metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log details about an LLM request.
        
        Args:
            prompt: The prompt or messages sent to the LLM
            model: The model being used
            metadata: Additional metadata about the request
        """
        if not any([self.show_prompt, self.show_metadata]):
            # Basic logging if detailed logging is disabled
            if isinstance(prompt, str):
                truncated = prompt[:50] + "..." if len(prompt) > 50 else prompt
                logger.info(f"Sending request to model {model}: {truncated}")
            else:
                logger.info(f"Sending {len(prompt)} messages to model {model}")
            return
            
        # Detailed logging
        log_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model": model,
            "request_type": "completion" if isinstance(prompt, str) else "chat"
        }
        
        # Add metadata if available
        if metadata and self.show_metadata:
            log_data["metadata"] = metadata
            
        # Log the prompt content if enabled
        if self.show_prompt:
            if isinstance(prompt, str):
                log_data["prompt"] = prompt
            else:
                log_data["messages"] = prompt
                
        # Log the formatted data
        logger.info(f"LLM Request: {json.dumps(log_data, indent=2, ensure_ascii=False)}")
    
    def log_response(self, 
                    response: Dict[str, Any],
                    duration: float) -> None:
        """Log details about an LLM response.
        
        Args:
            response: The response from the LLM
            duration: Time taken for the request in seconds
        """
        # Always log basic timing information
        logger.info(f"Received response in {duration:.2f}s")
        
        if not any([self.show_response, self.show_metadata]):
            return
            
        # Detailed logging
        log_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": duration
        }
        
        # Add metadata if available and enabled
        if self.show_metadata and "metadata" in response:
            log_data["metadata"] = response["metadata"]
            
        # Add response content if enabled
        if self.show_response:
            # Extract the actual response content based on response structure
            if "response" in response:
                log_data["response"] = response["response"]
            elif "text" in response:
                log_data["response"] = response["text"]
            elif "content" in response:
                log_data["response"] = response["content"]
            elif "message" in response and "content" in response["message"]:
                log_data["response"] = response["message"]["content"]
            else:
                # Include the full response if we can't extract the content
                log_data["full_response"] = response
                
        # Log the formatted data
        logger.info(f"LLM Response: {json.dumps(log_data, indent=2, ensure_ascii=False)}")
    
    def log_error(self, 
                 error: Union[str, Exception],
                 prompt: Optional[Union[str, List[Dict[str, str]]]] = None,
                 model: Optional[str] = None) -> None:
        """Log details about an error during LLM request.
        
        Args:
            error: The error message or exception
            prompt: The prompt that caused the error (if available)
            model: The model being used (if available)
        """
        error_msg = str(error)
        
        # Basic error logging
        logger.error(f"Error in LLM request: {error_msg}")
        
        if not any([self.show_prompt, self.show_metadata]):
            return
            
        # Detailed error logging
        log_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "error": error_msg
        }
        
        # Add model information if available
        if model:
            log_data["model"] = model
            
        # Add prompt information if available and enabled
        if prompt and self.show_prompt:
            if isinstance(prompt, str):
                log_data["prompt"] = prompt
            else:
                log_data["messages"] = prompt
                
        # Log the formatted data
        logger.error(f"LLM Error Details: {json.dumps(log_data, indent=2, ensure_ascii=False)}")
