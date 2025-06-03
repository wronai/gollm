#!/usr/bin/env python3
"""
Minimal test script for adaptive timeout calculation.

This script demonstrates the adaptive timeout calculation logic
without importing the full GoLLM modules.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from typing import Any, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("minimal_test")

# Test prompts with different lengths
TEST_PROMPTS = [
    {
        "name": "Very Short - Hello World",
        "prompt": "Write Hello World in Python",
        "language": "python",
        "output_file": "hello_world.py",
    },
    {
        "name": "Short - Add Numbers",
        "prompt": "Write a Python function to add two numbers",
        "language": "python",
        "output_file": "add_numbers.py",
    },
]


def calculate_adaptive_timeout(
    prompt_length: int, is_code_generation: bool = False, language: str = None
) -> int:
    """
    Calculate an adaptive timeout based on prompt length and task type.

    This is a simplified version of the adaptive timeout calculation
    implemented in the OllamaGenerator class.

    Args:
        prompt_length: Length of the prompt in characters
        is_code_generation: Whether this is a code generation task
        language: Programming language for code generation tasks

    Returns:
        Calculated timeout in seconds
    """
    # Base timeout
    base_timeout = 30

    # Calculate timeout based on prompt length
    # For very short prompts, use the base timeout
    if prompt_length < 100:
        timeout = base_timeout
    # For medium-length prompts, scale linearly
    elif prompt_length < 500:
        timeout = base_timeout + int(prompt_length * 0.05)
    # For long prompts, scale more conservatively
    else:
        timeout = base_timeout + 25 + int((prompt_length - 500) * 0.03)

    # Add extra time for code generation tasks
    if is_code_generation:
        # Ensure minimum timeout for code generation
        timeout = max(timeout, 15)

        # Add language-specific adjustments
        if language:
            language = language.lower()
            # Complex languages get more time
            if language in ["cpp", "c++", "java", "rust"]:
                timeout += 15
            # Medium complexity languages
            elif language in ["javascript", "typescript", "python"]:
                timeout += 10
            # Simple languages or scripts
            else:
                timeout += 5

    return timeout


def direct_api_call(prompt: str, language: str = None) -> Dict[str, Any]:
    """
    Make a direct API call to the Ollama server.

    Args:
        prompt: The prompt to send to the API
        language: Optional language for code generation

    Returns:
        API response as a dictionary
    """
    # Calculate adaptive timeout
    prompt_length = len(prompt)
    timeout = calculate_adaptive_timeout(
        prompt_length, is_code_generation=True, language=language
    )
    logger.info(f"Prompt length: {prompt_length}, Calculated timeout: {timeout}s")

    # Prepare the API request
    if language:
        # Format prompt for code generation
        formatted_prompt = f"Write {language} code for: {prompt}\n\nProvide ONLY the code without explanations."
    else:
        formatted_prompt = prompt

    # Prepare curl command
    curl_cmd = [
        "curl",
        "-s",
        "-X",
        "POST",
        "http://rock:8081/api/chat",
        "-H",
        "Content-Type: application/json",
        "-d",
        json.dumps(
            {
                "model": "qwen3:4b",
                "messages": [{"role": "user", "content": formatted_prompt}],
                "stream": False,
            }
        ),
    ]

    # Execute the curl command with timeout
    try:
        start_time = time.time()
        process = subprocess.run(
            curl_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,  # Use our adaptive timeout
            text=True,
        )
        duration = time.time() - start_time

        # Parse the response
        if process.returncode == 0 and process.stdout:
            try:
                response = json.loads(process.stdout)
                logger.info(f"API call successful in {duration:.2f}s")
                return {
                    "success": True,
                    "duration": duration,
                    "timeout": timeout,
                    "response": response,
                }
            except json.JSONDecodeError:
                logger.error("Failed to parse API response as JSON")
                return {
                    "success": False,
                    "duration": duration,
                    "timeout": timeout,
                    "error": "Invalid JSON response",
                    "raw_response": process.stdout,
                }
        else:
            logger.error(f"API call failed: {process.stderr}")
            return {
                "success": False,
                "duration": duration,
                "timeout": timeout,
                "error": "API call failed",
                "stderr": process.stderr,
            }
    except subprocess.TimeoutExpired:
        logger.error(f"API call timed out after {timeout}s")
        return {
            "success": False,
            "duration": timeout,
            "timeout": timeout,
            "error": "Timeout",
        }


def extract_code(response: Dict[str, Any], language: str) -> str:
    """
    Extract code from the API response.

    Args:
        response: API response dictionary
        language: Programming language to extract

    Returns:
        Extracted code as a string
    """
    if not response or not response.get("success", False):
        return ""

    # Get the response content
    api_response = response.get("response", {})
    if not api_response:
        return ""

    message = api_response.get("message", {})
    if not message:
        return ""

    content = message.get("content", "")
    if not content:
        return ""

    # Extract code blocks
    code = ""

    # Try to extract code between markdown code blocks
    import re

    pattern = f"```(?:{language})?\\s*([\\s\\S]*?)```"
    matches = re.findall(pattern, content)

    if matches:
        # Join all code blocks
        code = "\n\n".join(match.strip() for match in matches)
    else:
        # If no code blocks found, try to extract any code-like content
        lines = content.split("\n")
        code_lines = []
        in_code = False

        for line in lines:
            if (
                line.strip().startswith("def ")
                or line.strip().startswith("class ")
                or line.strip().startswith("import ")
            ):
                in_code = True

            if in_code:
                code_lines.append(line)

        if code_lines:
            code = "\n".join(code_lines)

    return code


def main():
    """
    Run the tests.
    """
    logger.info("Starting minimal test with adaptive timeout calculation")

    # Create output directory
    os.makedirs("test_output", exist_ok=True)

    results = []

    for test_case in TEST_PROMPTS:
        logger.info(f"\n\nTesting: {test_case['name']}")
        logger.info(f"Prompt: {test_case['prompt']}")

        # Make the API call
        result = direct_api_call(test_case["prompt"], test_case["language"])

        if result.get("success", False):
            # Extract code from the response
            code = extract_code(result, test_case["language"])

            if code and len(code.strip()) > 0:
                logger.info("Successfully extracted code!")

                # Save the code to a file
                output_path = os.path.join("test_output", test_case["output_file"])

                with open(output_path, "w") as f:
                    f.write(code)

                logger.info(f"Saved code to {output_path}")

                # Test if the code is valid Python
                if test_case["language"] == "python":
                    try:
                        compile(code, output_path, "exec")
                        logger.info("u2705 Code compiles successfully!")
                    except SyntaxError as e:
                        logger.error(f"u274c Code has syntax errors: {e}")

                result["code_extracted"] = True
                result["code_length"] = len(code)
            else:
                logger.error("Failed to extract valid code from response")
                result["code_extracted"] = False

        results.append(
            {
                "name": test_case["name"],
                "prompt": test_case["prompt"],
                "prompt_length": len(test_case["prompt"]),
                **result,
            }
        )

    # Generate a summary report
    logger.info("\n\nTest Summary:")
    logger.info("==============")

    for result in results:
        status = (
            "u2705 Success"
            if result.get("success", False) and result.get("code_extracted", False)
            else "u274c Failed"
        )
        logger.info(
            f"{result['name']}: {status} (Timeout: {result['timeout']}s, Duration: {result.get('duration', 'N/A')}s)"
        )

    # Save results to a JSON file
    with open("test_output/results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    logger.info("\nResults saved to test_output/results.json")


if __name__ == "__main__":
    main()
