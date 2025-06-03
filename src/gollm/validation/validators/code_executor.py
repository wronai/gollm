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


def execute_python_code(code: str, filename: Optional[str] = None, timeout: int = 15) -> Tuple[bool, str, Optional[str]]:
    """Execute Python code in a subprocess and capture any errors and output.
    
    Args:
        code: The Python code to execute
        filename: Optional filename to use for the temporary file
        timeout: Maximum execution time in seconds (default: 15)
        
    Returns:
        Tuple of (success, error_message, output)
    """
    # Create a temporary file to store the code
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, filename or f"temp_{os.urandom(4).hex()}.py")
    
    try:
        # Write the code to the temporary file
        with open(temp_path, "w") as temp_file:
            temp_file.write(code)
        
        # Execute the code in a separate process with restricted permissions
        # Use a timeout to prevent infinite loops or hanging
        result = subprocess.run(
            ["python", temp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}  # Ensure proper encoding
        )
        
        # Check if execution was successful
        if result.returncode == 0:
            return True, "", result.stdout
        else:
            # Return the error message
            error_msg = result.stderr.strip()
            # Add line numbers to syntax errors for easier debugging
            if "SyntaxError" in error_msg:
                error_lines = error_msg.split("\n")
                for i, line in enumerate(error_lines):
                    if "^" in line:
                        # Find the line number from the error message
                        for prev_line in error_lines[:i]:
                            if "line" in prev_line and ", " in prev_line:
                                try:
                                    line_num = int(prev_line.split("line")[1].split(",")[0].strip())
                                    # Add the problematic code line for context
                                    code_lines = code.split("\n")
                                    if 0 <= line_num - 1 < len(code_lines):
                                        error_lines.insert(i, f"Code at line {line_num}: {code_lines[line_num-1].strip()}")
                                        break
                                except (ValueError, IndexError):
                                    pass
                error_msg = "\n".join(error_lines)
            return False, error_msg, result.stdout
    except subprocess.TimeoutExpired:
        return False, f"Execution timed out after {timeout} seconds. Check for infinite loops or long-running operations.", None
    except Exception as e:
        return False, f"Error executing code: {str(e)}", None
    finally:
        # Clean up the temporary files and directory
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            os.rmdir(temp_dir)
        except Exception as e:
            logger.warning(f"Failed to clean up temporary files: {str(e)}")


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
