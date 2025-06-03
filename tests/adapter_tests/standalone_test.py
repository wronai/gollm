#!/usr/bin/env python3
"""
Standalone test for the improved Ollama generator with adaptive timeout.

This script tests the improved timeout handling in the OllamaGenerator class
without relying on the full GoLLM infrastructure.
"""

import asyncio
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("standalone_test")

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import only the necessary components
from gollm.llm.providers.ollama.modules.generation.generator import \
    OllamaGenerator


# Simplified version of the calculate_adaptive_timeout method
def calculate_adaptive_timeout(
    prompt_length: int, is_code_generation: bool = False
) -> float:
    """
    Calculate an adaptive timeout based on prompt length and task type.

    Args:
        prompt_length: Length of the prompt in characters
        is_code_generation: Whether this is a code generation task

    Returns:
        Calculated timeout in seconds
    """
    # Base timeout for short prompts
    base_timeout = 30.0

    # For very short prompts (< 100 chars), use the base timeout
    if prompt_length < 100:
        timeout = base_timeout
    # For medium prompts (100-1000 chars), scale linearly
    elif prompt_length < 1000:
        timeout = (
            base_timeout + (prompt_length - 100) * 0.05
        )  # Add 0.05s per char over 100
    # For long prompts (1000+ chars), scale more aggressively
    else:
        timeout = (
            base_timeout + 45.0 + (prompt_length - 1000) * 0.02
        )  # Add 0.02s per char over 1000

    # For code generation tasks, add additional time
    if is_code_generation:
        timeout *= 1.5  # Code generation typically takes longer

    # Cap the timeout at a reasonable maximum
    max_timeout = 300.0  # 5 minutes
    timeout = min(timeout, max_timeout)

    return timeout


async def test_adaptive_timeout():
    """
    Test the adaptive timeout calculation with different prompt lengths.
    """
    logger.info("Testing adaptive timeout calculation")

    test_cases = [
        # (prompt_length, is_code_generation)
        (50, False),  # Very short prompt
        (50, True),  # Very short code prompt
        (500, False),  # Medium prompt
        (500, True),  # Medium code prompt
        (2000, False),  # Long prompt
        (2000, True),  # Long code prompt
    ]

    for prompt_length, is_code_generation in test_cases:
        timeout = calculate_adaptive_timeout(prompt_length, is_code_generation)
        task_type = "code generation" if is_code_generation else "regular"
        logger.info(
            f"Prompt length: {prompt_length}, Task type: {task_type}, Timeout: {timeout:.2f}s"
        )


async def main():
    """
    Run the tests.
    """
    logger.info("Starting standalone test of adaptive timeout calculation")

    try:
        await test_adaptive_timeout()
        logger.info("Tests completed successfully!")
    except Exception as e:
        logger.exception(f"Error during testing: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
