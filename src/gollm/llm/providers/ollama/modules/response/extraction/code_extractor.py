"""Code extraction utilities for Ollama API responses."""

import logging
import re
from typing import Tuple, List, Optional

logger = logging.getLogger("gollm.ollama.extraction")


def extract_code_blocks(text: str) -> str:
    """Extract code blocks from the generated text if present.
    
    Args:
        text: The text to extract code blocks from
        
    Returns:
        The extracted code or the original text if no code blocks found
    """
    if not text or not text.strip():
        logger.warning("Cannot extract code blocks from empty text")
        return text
        
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
        logger.debug("Text doesn't contain markdown code blocks, returning as is")
        return text
    
    # Try multiple extraction patterns with detailed logging
    extraction_patterns = [
        # Pattern 1: Standard markdown code blocks with language specifier and newlines
        (r'```(?:\w*)\n(.+?)(?:\n```|$)', "standard"),
        # Pattern 2: Code blocks without requiring newline after opening backticks
        (r'```(?:\w*)\s*(.+?)(?:\n```|```|$)', "flexible"),
        # Pattern 3: Anything between backticks (most lenient)
        (r'```(.+?)```', "lenient")
    ]
    
    for pattern, pattern_name in extraction_patterns:
        try:
            code_blocks = re.findall(pattern, text, re.DOTALL)
            
            logger.debug(f"{pattern_name.title()} extraction attempt found {len(code_blocks)} code blocks")
            
            if code_blocks:
                logger.info(f"Extracted {len(code_blocks)} code blocks with {pattern_name} pattern")
                for i, block in enumerate(code_blocks):
                    logger.debug(f"Code block {i+1} length: {len(block)}")
                    if block:
                        logger.debug(f"Code block {i+1} preview: {block[:100]}...")
                
                extracted_code = '\n\n'.join(code_blocks)
                if extracted_code and extracted_code.strip():
                    logger.info(f"Successfully extracted code with {pattern_name} pattern, total length: {len(extracted_code)}")
                    return extracted_code
                else:
                    logger.warning(f"Extraction with {pattern_name} pattern resulted in empty text")
        except Exception as e:
            logger.error(f"Error during {pattern_name} code extraction: {str(e)}")
    
    # If we still couldn't extract code blocks, return the original text
    logger.debug("No valid code blocks found in response, returning original text")
    return text


def clean_generated_text(text: str) -> str:
    """Clean up the generated text by removing unwanted artifacts.
    
    Args:
        text: The text to clean
        
    Returns:
        The cleaned text
    """
    if not text:
        return ""
        
    try:
        # Remove any leading/trailing whitespace and newlines
        cleaned_text = text.strip()
        
        # Remove any 'assistant:' or similar prefixes that might be in the response
        prefixes_to_remove = [
            r'^assistant:\s*',
            r'^\[assistant\]:\s*',
            r'^\*\*assistant:\*\*\s*',
            r'^\*assistant:\*\s*',
        ]
        
        for prefix in prefixes_to_remove:
            cleaned_text = re.sub(prefix, '', cleaned_text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Remove any trailing 'user:' or similar that might be in the response
        cleaned_text = re.sub(r'\s*\n\s*user:\s*$', '', cleaned_text, flags=re.IGNORECASE)
        
        # Log cleaning results
        if cleaned_text != text:
            logger.debug(f"Text cleaned: removed {len(text) - len(cleaned_text)} characters")
            
        return cleaned_text
    except Exception as e:
        logger.error(f"Error cleaning generated text: {str(e)}")
        # Return original text if cleaning fails
        return text


def extract_code_from_json(text: str) -> Tuple[bool, str]:
    """Extract code from JSON response if the response is in JSON format.
    
    Args:
        text: The text to check for JSON format
        
    Returns:
        Tuple of (is_json, extracted_content)
    """
    import json
    
    try:
        # Check if the text is valid JSON
        if not (text.strip().startswith('{') and text.strip().endswith('}')):
            return False, text
            
        data = json.loads(text)
        
        # Check for common JSON response formats that might contain code
        if 'code' in data and isinstance(data['code'], str):
            logger.info("Found 'code' field in JSON response")
            return True, data['code']
        elif 'content' in data and isinstance(data['content'], str):
            logger.info("Found 'content' field in JSON response")
            return True, data['content']
        elif 'message' in data and isinstance(data['message'], dict) and 'content' in data['message']:
            logger.info("Found 'message.content' field in JSON response")
            return True, data['message']['content']
        elif 'choices' in data and isinstance(data['choices'], list) and len(data['choices']) > 0:
            if 'text' in data['choices'][0]:
                logger.info("Found 'choices[0].text' field in JSON response")
                return True, data['choices'][0]['text']
            elif 'message' in data['choices'][0] and 'content' in data['choices'][0]['message']:
                logger.info("Found 'choices[0].message.content' field in JSON response")
                return True, data['choices'][0]['message']['content']
                
        # If we didn't find any code fields, return the original text
        return True, text
    except json.JSONDecodeError:
        # Not valid JSON
        return False, text
    except Exception as e:
        logger.error(f"Error extracting code from JSON: {str(e)}")
        return False, text


def is_error_json(text: str) -> Tuple[bool, str]:
    """Check if the text is a JSON error response.
    
    Args:
        text: The text to check for JSON error
        
    Returns:
        Tuple of (is_error, error_message)
    """
    import json
    
    try:
        # Check if the text is valid JSON
        if not (text.strip().startswith('{') and text.strip().endswith('}')):
            return False, ""
            
        data = json.loads(text)
        
        # Check for common error fields in JSON responses
        if 'error' in data and isinstance(data['error'], str):
            return True, data['error']
        elif 'error' in data and isinstance(data['error'], dict) and 'message' in data['error']:
            return True, data['error']['message']
        elif 'message' in data and ('error' in data['message'].lower() or 'exception' in data['message'].lower()):
            return True, data['message']
            
        return False, ""
    except json.JSONDecodeError:
        # Not valid JSON
        return False, ""
    except Exception as e:
        logger.error(f"Error checking for JSON error: {str(e)}")
        return False, ""


def extract_all_text_content(response: dict) -> str:
    """Extract all possible text content from a response dictionary.
    
    This function tries multiple paths in the response dictionary to find text content,
    prioritizing the most likely locations based on the API format.
    
    Args:
        response: The response dictionary to extract content from
        
    Returns:
        The extracted text content or empty string if none found
    """
    if not isinstance(response, dict):
        logger.warning(f"Response is not a dictionary, type: {type(response)}")
        return str(response) if response else ""
    
    # Log the response keys for debugging
    logger.debug(f"Response keys: {response.keys()}")
    
    # Define extraction paths in order of priority
    extraction_paths = [
        # Chat API format
        ("message.content", lambda r: r.get("message", {}).get("content", "") if isinstance(r.get("message"), dict) else ""),
        # Completion API format
        ("response", lambda r: r.get("response", "")),
        # OpenAI-style format
        ("choices[0].message.content", lambda r: r.get("choices", [{}])[0].get("message", {}).get("content", "") 
            if r.get("choices") and isinstance(r.get("choices"), list) and len(r.get("choices")) > 0 
            and isinstance(r.get("choices")[0].get("message", {}), dict) else ""),
        ("choices[0].text", lambda r: r.get("choices", [{}])[0].get("text", "") 
            if r.get("choices") and isinstance(r.get("choices"), list) and len(r.get("choices")) > 0 else ""),
        # Other common formats
        ("content", lambda r: r.get("content", "")),
        ("text", lambda r: r.get("text", "")),
        ("generated_text", lambda r: r.get("generated_text", ""))
    ]
    
    # Try each extraction path
    for path_name, extractor in extraction_paths:
        try:
            content = extractor(response)
            if content and isinstance(content, str) and content.strip():
                logger.info(f"Successfully extracted content from {path_name}, length: {len(content)}")
                return content
        except Exception as e:
            logger.error(f"Error extracting from {path_name}: {str(e)}")
    
    # If all extraction paths failed, return empty string
    logger.warning("Failed to extract content from any known response format")
    return ""
