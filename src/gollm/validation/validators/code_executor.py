"""Code execution and testing module.

This module provides functionality to execute and test generated code to ensure it runs without errors.
"""

import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger("gollm.validation.code.executor")


def execute_python_code(code: str, filename: Optional[str] = None) -> Tuple[bool, str]:
    """Execute Python code in a subprocess and capture any errors.
    
    Args:
        code: The Python code to execute
        filename: Optional filename to use for the temporary file
        
    Returns:
        Tuple of (success, error_message)
    """
    # Create a temporary file to store the code
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as temp_file:
        temp_file.write(code)
        temp_path = temp_file.name
    
    try:
        # Execute the code
        result = subprocess.run(
            ["python", temp_path],
            capture_output=True,
            text=True,
            timeout=10  # Timeout after 10 seconds to prevent hanging
        )
        
        # Check if execution was successful
        if result.returncode == 0:
            return True, ""
        else:
            # Return the error message
            return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, "Execution timed out after 10 seconds"
    except Exception as e:
        return False, f"Error executing code: {str(e)}"
    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_path)
        except Exception:
            pass


def format_error_for_completion(code: str, error_message: str) -> str:
    """Format the error message for LLM completion.
    
    Args:
        code: The original code
        error_message: The error message from execution
        
    Returns:
        Formatted prompt for LLM to fix the code
    """
    prompt = f"""The following Python code has errors when executed:

```python
{code}
```

When executed, it produced the following error:

```
{error_message}
```

Please fix the code to make it run without errors. Provide the complete fixed code without explanations.
"""
    return prompt


def test_and_fix_code(code: str, max_attempts: int = 3) -> Tuple[bool, str, List[str]]:
    """Test and fix code by executing it and fixing any errors.
    
    Args:
        code: The code to test and fix
        max_attempts: Maximum number of fix attempts
        
    Returns:
        Tuple of (success, fixed_code, error_messages)
    """
    current_code = code
    error_messages = []
    
    for attempt in range(max_attempts):
        # Execute the code
        success, error = execute_python_code(current_code)
        
        if success:
            # Code executed successfully
            logger.info(f"Code executed successfully after {attempt + 1} attempts")
            return True, current_code, error_messages
        
        # Log the error
        error_messages.append(f"Attempt {attempt + 1}: {error}")
        logger.warning(f"Code execution failed (attempt {attempt + 1}): {error}")
        
        # If we've reached the maximum number of attempts, give up
        if attempt >= max_attempts - 1:
            logger.error(f"Failed to fix code after {max_attempts} attempts")
            return False, current_code, error_messages
        
        # Format the error for LLM completion
        # This would be implemented in a real system to send to LLM for fixing
        # For now, we'll just return the current code and errors
    
    return False, current_code, error_messages
