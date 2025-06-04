#!/usr/bin/env python3
"""
Test script to debug Ollama provider's code extraction.
This script simulates a response from the Ollama API and tests the extraction logic.
"""

import logging
import re
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_extraction")

# Sample response from Ollama API (simulating what might be returned)
SAMPLE_RESPONSE = """
Here's a Python function that securely hashes passwords using bcrypt and includes verification functionality:

```python
import bcrypt
import re
from typing import Tuple, Optional

def validate_password(password: str) -> Tuple[bool, str]:
    \"\"\"
    Validate a password against security requirements.
    
    Args:
        password: The password to validate
        
    Returns:
        Tuple of (is_valid, message)
    \"\"\"
    if not isinstance(password, str):
        return False, "Password must be a string"
        
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
        
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
        
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
        
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one digit"
        
    return True, "Password is valid"

def hash_password(password: str, rounds: int = 12) -> Optional[bytes]:
    \"\"\"
    Hash a password using bcrypt.
    
    Args:
        password: The password to hash
        rounds: The number of rounds to use (default: 12)
        
    Returns:
        Hashed password or None if hashing fails
    \"\"\"
    try:
        # Validate password first
        is_valid, message = validate_password(password)
        if not is_valid:
            print(f"Password validation failed: {message}")
            return None
            
        # Convert password to bytes
        password_bytes = password.encode('utf-8')
        
        # Generate salt and hash password
        salt = bcrypt.gensalt(rounds=rounds)
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        return hashed
    except Exception as e:
        print(f"Error hashing password: {e}")
        return None

def verify_password(password: str, hashed_password: bytes) -> bool:
    \"\"\"
    Verify a password against a hash.
    
    Args:
        password: The password to verify
        hashed_password: The hashed password to check against
        
    Returns:
        True if the password matches, False otherwise
    \"\"\"
    try:
        # Convert password to bytes
        password_bytes = password.encode('utf-8')
        
        # Verify the password
        return bcrypt.checkpw(password_bytes, hashed_password)
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False
```

You can use these functions like this:

```python
# Example usage
password = "SecureP@ss123"
hashed = hash_password(password)
if hashed:
    print("Password hashed successfully")
    
    # Verify correct password
    if verify_password(password, hashed):
        print("Password is correct")
    else:
        print("Password is incorrect")
```
"""

def extract_code_blocks(text: str) -> str:
    """Extract code blocks from the generated text if present."""
    if not text or not text.strip():
        logger.warning("Cannot extract code blocks from empty text")
        return text
    
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

def main():
    """Test the code extraction logic with the sample response."""
    print("Testing code extraction from Ollama API response...")
    print("-" * 80)
    
    # Extract code blocks from the sample response
    extracted_code = extract_code_blocks(SAMPLE_RESPONSE)
    
    # Print the extracted code
    print("\nExtracted code:")
    print("-" * 80)
    print(extracted_code)
    print("-" * 80)
    
    # Save the extracted code to a file
    output_file = "extracted_code.py"
    with open(output_file, "w") as f:
        f.write(extracted_code)
    
    print(f"\nExtracted code saved to {output_file}")
    
    # Try to run the extracted code
    print("\nTrying to validate the extracted code...")
    try:
        # Check if the code is valid Python
        import ast
        ast.parse(extracted_code)
        print("✅ Extracted code is valid Python syntax")
    except SyntaxError as e:
        print(f"❌ Extracted code has syntax errors: {e}")
    
    # Save the original response for comparison
    with open("original_response.txt", "w") as f:
        f.write(SAMPLE_RESPONSE)
    
    print(f"Original response saved to original_response.txt")
    
    # Compare the number of lines
    original_lines = len(SAMPLE_RESPONSE.splitlines())
    extracted_lines = len(extracted_code.splitlines())
    print(f"\nOriginal response: {original_lines} lines")
    print(f"Extracted code: {extracted_lines} lines")

if __name__ == "__main__":
    main()
