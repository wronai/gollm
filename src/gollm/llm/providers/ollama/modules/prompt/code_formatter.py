"""Code-specific prompt formatting module for Ollama adapter."""

import logging
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger('gollm.ollama.prompt.code')

class CodePromptFormatter:
    """Specialized prompt formatter for code generation tasks.
    
    This formatter is designed to produce prompts that result in high-quality
    code generation with minimal explanatory text or "thinking" style outputs.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the code prompt formatter.
        
        Args:
            config: Configuration dictionary with formatting options
        """
        self.config = config
        self.show_prompt = config.get('show_prompt', False)
        self.language_defaults = {
            'python': {
                'comment_style': '#',
                'docstring_style': '"""',
                'function_prefix': 'def',
                'class_prefix': 'class',
            },
            'javascript': {
                'comment_style': '//',
                'docstring_style': '/**',
                'function_prefix': 'function',
                'class_prefix': 'class',
            },
            'typescript': {
                'comment_style': '//',
                'docstring_style': '/**',
                'function_prefix': 'function',
                'class_prefix': 'class',
            },
            'java': {
                'comment_style': '//',
                'docstring_style': '/**',
                'function_prefix': 'public',
                'class_prefix': 'public class',
            },
            'go': {
                'comment_style': '//',
                'docstring_style': '//',
                'function_prefix': 'func',
                'class_prefix': 'type',
            },
            'rust': {
                'comment_style': '//',
                'docstring_style': '///',
                'function_prefix': 'fn',
                'class_prefix': 'struct',
            },
        }
    
    def format_code_prompt(self, 
                          prompt: str, 
                          language: str = 'python',
                          code_context: Optional[str] = None,
                          file_context: Optional[str] = None,
                          system_message: Optional[str] = None) -> str:
        """Format a prompt specifically for code generation.
        
        Args:
            prompt: The user prompt requesting code generation
            language: The target programming language
            code_context: Optional related code for context
            file_context: Optional file structure context
            system_message: Optional system message to prepend
            
        Returns:
            Formatted prompt string optimized for code generation
        """
        # Normalize language name
        language = language.lower()
        
        # Get language-specific formatting
        lang_format = self.language_defaults.get(
            language, 
            self.language_defaults['python']  # Default to Python if language not found
        )
        
        # Build the system message if not provided
        if not system_message:
            system_message = self._build_code_system_message(language, lang_format)
        
        # Start building the prompt
        parts = []
        
        # Add system message
        parts.append(system_message)
        
        # Add file context if provided
        if file_context:
            parts.append(f"FILE CONTEXT:\n{file_context}")
        
        # Add code context if provided
        if code_context:
            parts.append(f"CODE CONTEXT:\n```{language}\n{code_context}\n```")
        
        # Add the task with direct code generation instructions
        parts.append(f"TASK: {prompt}")
        
        # Add explicit instructions to generate only code
        parts.append(self._get_code_instructions(language))
        
        # Join all parts with double newlines
        formatted_prompt = "\n\n".join(parts)
        
        # Log the prompt if enabled
        if self.show_prompt:
            logger.info(f"Formatted code prompt:\n{formatted_prompt}")
        else:
            # Log a truncated version
            truncated = formatted_prompt[:100] + "..." if len(formatted_prompt) > 100 else formatted_prompt
            logger.debug(f"Code prompt (truncated): {truncated}")
            
        return formatted_prompt
    
    def format_code_chat_messages(self,
                                 prompt: str,
                                 language: str = 'python',
                                 code_context: Optional[str] = None,
                                 file_context: Optional[str] = None,
                                 chat_history: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
        """Format chat messages specifically for code generation.
        
        Args:
            prompt: The user prompt requesting code generation
            language: The target programming language
            code_context: Optional related code for context
            file_context: Optional file structure context
            chat_history: Optional previous conversation history
            
        Returns:
            List of formatted chat messages optimized for code generation
        """
        # Normalize language name
        language = language.lower()
        
        # Get language-specific formatting
        lang_format = self.language_defaults.get(
            language, 
            self.language_defaults['python']  # Default to Python if language not found
        )
        
        # Start with system message
        messages = [{
            "role": "system",
            "content": self._build_code_system_message(language, lang_format)
        }]
        
        # Add chat history if provided
        if chat_history:
            messages.extend(chat_history)
        
        # Build context message
        context_parts = []
        
        if file_context:
            context_parts.append(f"FILE CONTEXT:\n{file_context}")
        
        if code_context:
            context_parts.append(f"CODE CONTEXT:\n```{language}\n{code_context}\n```")
        
        # Add context as assistant message if available
        if context_parts:
            context_content = "\n\n".join(context_parts)
            messages.append({
                "role": "assistant",
                "content": f"I'll help you with your {language} code. Here's the context I'm working with:\n\n{context_content}"
            })
        
        # Add the user prompt with explicit instructions
        user_prompt = f"{prompt}\n\n{self._get_code_instructions(language)}"
        messages.append({
            "role": "user",
            "content": user_prompt
        })
        
        # Log the messages if enabled
        if self.show_prompt:
            logger.info(f"Formatted code chat messages:\n{messages}")
        else:
            # Log a summary
            logger.debug(f"Code chat messages: {len(messages)} messages prepared for {language} code generation")
            
        return messages
    
    def _build_code_system_message(self, language: str, lang_format: Dict[str, str]) -> str:
        """Build a system message optimized for code generation.
        
        Args:
            language: The target programming language
            lang_format: Dictionary with language-specific formatting
            
        Returns:
            System message string
        """
        return f"""You are an expert {language} developer focused on writing clean, efficient, and well-documented code.
        
IMPORTANT INSTRUCTIONS:
1. Generate ONLY code without explanations or commentary
2. Do not include markdown code block markers (```) in your response
3. Do not preface your response with any text like "Here's the code:" or "Solution:"
4. Include appropriate {lang_format['docstring_style']} docstrings for functions and classes
5. Use {lang_format['comment_style']} for brief inline comments only when necessary
6. Follow best practices for {language} code style and conventions
7. Ensure the code is complete and runnable
8. Include necessary imports or dependencies at the top of the file
9. Do not explain your thought process or reasoning

YOUR RESPONSE MUST CONTAIN ONLY THE CODE IMPLEMENTATION."""
    
    def _get_code_instructions(self, language: str) -> str:
        """Get explicit instructions for code generation.
        
        Args:
            language: The target programming language
            
        Returns:
            Instructions string
        """
        return f"""RESPONSE FORMAT:
1. Provide ONLY the {language} code implementation
2. Do not include explanations, comments about your approach, or markdown formatting
3. Include necessary imports and dependencies
4. Make sure the code is complete and ready to run
5. Do not include any text before or after the code

EXAMPLE OF WHAT I WANT:
import math

def calculate_area(radius):
    \"\"\"Calculate the area of a circle.\"\"\"
    return math.pi * radius * radius

# Usage
print(calculate_area(5))"""

    def extract_code_from_response(self, response: str, language: str = 'python') -> str:
        """Extract clean code from a potentially verbose LLM response.
        
        Args:
            response: The raw LLM response text
            language: The target programming language
            
        Returns:
            Extracted clean code
        """
        # Remove markdown code blocks if present
        code = response
        
        # Remove markdown code block markers
        code = code.replace(f"```{language}", "").replace("```", "")
        
        # Remove common prefixes that LLMs tend to add
        prefixes_to_remove = [
            "Here's the code:",
            "Here is the code:",
            "Here's the implementation:",
            "Here is the implementation:",
            "Solution:",
            "Here's a solution:",
            "Here is a solution:",
            "Code:",
        ]
        
        for prefix in prefixes_to_remove:
            if code.startswith(prefix):
                code = code[len(prefix):].lstrip()
        
        # Remove trailing explanations
        explanations = [
            "This code works by",
            "In this implementation",
            "The code above",
            "This implementation",
            "Let me explain",
            "To explain",
        ]
        
        for explanation in explanations:
            if explanation in code:
                code = code.split(explanation)[0].rstrip()
        
        return code.strip()
