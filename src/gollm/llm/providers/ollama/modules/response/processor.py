"""Response processing utilities for Ollama API requests."""

import logging
import re
from typing import Any, Dict, Optional, Tuple

from .json_handler import extract_code_from_json, is_error_json

logger = logging.getLogger("gollm.ollama.response")


async def process_llm_response(
    adapter, prompt: str, context: Optional[Dict[str, Any]], options: Dict[str, Any], model: str, api_type: str
) -> Tuple[Dict[str, Any], str, str, int, int]:
    """Process the LLM request and handle the response.
    
    Args:
        adapter: The adapter to use for the API request
        prompt: The prompt to send to the LLM
        context: Additional context for the generation
        options: API options for the request
        model: The model to use for generation
        api_type: The API type to use (chat or completion)
        
    Returns:
        Tuple containing (response, generated_text, model, prompt_tokens, completion_tokens)
    """
    from ..prompt.preparation import extract_response_content
    
    # Prepare messages or prompt based on API type
    if api_type == "chat":
        messages = [{"role": "user", "content": prompt}]
        if context and "messages" in context:
            messages = context["messages"] + messages

        logger.debug(f"Sending chat request with messages: {messages}")
        response = await adapter.chat(
            messages=messages,
            model=model,
            options=options,
            stream=False,
        )

        # Handle chat completion response format
        generated_text = response.get("message", {}).get("content", "")
        model_name = response.get("model", model)
        prompt_tokens = response.get("prompt_eval_count", len(prompt.split()))
        completion_tokens = response.get(
            "eval_count", len(generated_text.split())
        )
    else:
        # Handle completion response format
        response = await adapter.generate(
            prompt=prompt,
            model=model,
            options=options,
            stream=False,
        )

        # Extract the generated text from different possible response formats
        generated_text = extract_response_content(response)
        
        # Extract model and token information
        model_name = response.get("model", model)
        prompt_tokens = response.get("prompt_eval_count", len(prompt.split()))
        completion_tokens = response.get(
            "eval_count", len(generated_text.split())
        )

    # Check for empty responses
    if not generated_text or not generated_text.strip():
        logger.warning("Empty response received from Ollama API")
        error_message = "The model returned an empty response. This may indicate the model is overloaded or the request was too complex."
        return {
            "error": "EmptyResponse",
            "details": error_message,
            "success": False
        }, f"ERROR: {error_message}", model_name, prompt_tokens, 0
        
    # Log the raw response for debugging
    logger.debug(f"Raw response from Ollama API: {generated_text[:200]}...")
    if '```' in generated_text:
        logger.info("Response contains code blocks, will attempt to extract")
    else:
        logger.info("Response does not contain code blocks, will use as-is")
    
    # Store the original text before any processing
    original_text = generated_text
    
    # Clean up the generated text
    generated_text = clean_generated_text(generated_text)
    logger.debug(f"After cleaning, text length: {len(generated_text)}")
    logger.debug(f"Cleaned text preview: {generated_text[:100]}...")
    
    # Extract code blocks
    extracted_text = extract_code_blocks(generated_text)
    
    # Log the extraction results for debugging
    logger.debug(f"Original text length: {len(generated_text)}, Extracted text length: {len(extracted_text)}")
    if extracted_text != generated_text:
        logger.info(f"Extracted code from response: {extracted_text[:100]}...")
    
    # Use the extracted text if it's not empty
    if extracted_text and extracted_text.strip():
        logger.info(f"Using extracted code (length: {len(extracted_text)})")
        generated_text = extracted_text
    else:
        logger.warning(f"Code extraction returned empty result, using original text (length: {len(generated_text)})")
        
    # Final check for empty text after all processing
    if not generated_text or not generated_text.strip():
        logger.warning("Text is empty after processing, attempting to recover original content")
        # Try to recover by using the original text if available
        if original_text and original_text.strip():
            logger.info(f"Recovering using original unprocessed text (length: {len(original_text)})")
            generated_text = original_text
            logger.debug(f"Recovered text preview: {generated_text[:100]}...")
        else:
            logger.error("CRITICAL: Text is empty after all processing steps and recovery attempts")
    else:
        logger.info(f"Final text length: {len(generated_text)}, starts with: {generated_text[:50]}...")
    
    # Check if the response contains an error message after processing
    if generated_text.startswith("ERROR:"):
        logger.warning(f"Error in processed response: {generated_text}")
        error_details = generated_text[7:].strip()  # Remove 'ERROR: ' prefix
        return {
            "error": "ProcessingError",
            "details": error_details,
            "success": False
        }, generated_text, model_name, prompt_tokens, completion_tokens
    
    logger.debug(f"Processed response - model: {model_name}, tokens: {prompt_tokens + completion_tokens}")
    
    return response, generated_text, model_name, prompt_tokens, completion_tokens


def clean_generated_text(text: str) -> str:
    """Clean up the generated text by removing unwanted artifacts.
    
    Args:
        text: The text to clean
        
    Returns:
        The cleaned text
    """
    # Remove any leading/trailing whitespace
    text = text.strip()
    
    # Remove any leading/trailing backticks (outside of code blocks)
    if text.startswith('`') and not text.startswith('```'):
        text = text.lstrip('`')
    if text.endswith('`') and not text.endswith('```'):
        text = text.rstrip('`')
    
    # Remove any "CODE_ONLY: True" markers that might have been included
    text = re.sub(r'\s*CODE_ONLY:\s*True\s*', '', text)
    
    return text


def extract_code_blocks(text: str) -> str:
    """Extract code blocks from the generated text if present.
    
    Args:
        text: The text to extract code blocks from
        
    Returns:
        The extracted code or the original text if no code blocks found
    """
    # First, check if the response is JSON and try to extract code from it
    is_json, json_content = extract_code_from_json(text)
    if is_json:
        logger.info("Extracted content from JSON response")
        text = json_content  # Use the extracted content for further processing
    
    # Check if the text is an error JSON
    is_error, error_message = is_error_json(text)
    if is_error:
        logger.warning(f"Response contains error JSON: {error_message}")
        return f"ERROR: {error_message}"
    
    # Check if the text already looks like raw code (no markdown)
    if not re.search(r'```\w*\n|```\w*$', text):
        # If it doesn't contain markdown code blocks, return as is
        return text
    
    # Extract code blocks - handle various code block formats
    # First try with language specifier and newlines
    code_blocks = re.findall(r'```(?:\w*)\n(.+?)(?:\n```|$)', text, re.DOTALL)
    
    # Log the extraction attempt
    logger.debug(f"First extraction attempt found {len(code_blocks)} code blocks")
    if code_blocks:
        logger.debug(f"First code block content: {code_blocks[0][:100]}...")
    
    # If we found code blocks, join them with newlines
    if code_blocks:
        logger.info(f"Extracted {len(code_blocks)} code blocks from response")
        extracted_code = '\n\n'.join(code_blocks)
        logger.debug(f"Extracted code length: {len(extracted_code)}")
        return extracted_code
        
    # Try alternative pattern without requiring newline after opening backticks
    code_blocks = re.findall(r'```(?:\w*)\s*(.+?)(?:\n```|```|$)', text, re.DOTALL)
    
    # Log the alternative extraction attempt
    logger.debug(f"Alternative extraction attempt found {len(code_blocks)} code blocks")
    if code_blocks:
        logger.debug(f"Alternative code block content: {code_blocks[0][:100]}...")
    
    # If we found code blocks with the alternative pattern, join them
    if code_blocks:
        logger.info(f"Extracted {len(code_blocks)} code blocks with alternative pattern")
        extracted_code = '\n\n'.join(code_blocks)
        logger.debug(f"Extracted code length: {len(extracted_code)}")
        return extracted_code
    
    # If no code blocks found but we have backticks, try to extract anything between them
    if '```' in text:
        # Try a more lenient pattern
        code_blocks = re.findall(r'```(.+?)```', text, re.DOTALL)
        if code_blocks:
            logger.info(f"Extracted {len(code_blocks)} code blocks with lenient pattern")
            return '\n\n'.join(code_blocks)
    
    # If we still couldn't extract code blocks, return the original text
    logger.debug("No code blocks found in response, returning original text")
    return text
