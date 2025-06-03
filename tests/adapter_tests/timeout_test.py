#!/usr/bin/env python3
"""
Standalone test for the adaptive timeout calculation logic.

This script demonstrates the improved timeout handling without
relying on any GoLLM infrastructure or dependencies.
"""

import logging
import time
from typing import Any, Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("timeout_test")


def calculate_adaptive_timeout(
    prompt_length: int,
    is_code_generation: bool = False,
    language: str = None,
    base_timeout: float = 30.0,
) -> float:
    """
    Calculate an adaptive timeout based on prompt length and task type.

    Args:
        prompt_length: Length of the prompt in characters
        is_code_generation: Whether this is a code generation task
        language: Programming language for code generation tasks
        base_timeout: Base timeout value in seconds

    Returns:
        Calculated timeout in seconds
    """
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
        # Code generation typically takes longer
        timeout *= 1.5

        # Certain languages may need more time
        if language in ["cpp", "java", "rust"]:
            timeout *= 1.2  # These languages often require more complex code

    # Cap the timeout at a reasonable maximum
    max_timeout = 300.0  # 5 minutes
    timeout = min(timeout, max_timeout)

    return timeout


def test_adaptive_timeout():
    """
    Test the adaptive timeout calculation with different prompt lengths and task types.
    """
    logger.info("Testing adaptive timeout calculation")

    test_cases = [
        # (prompt_length, is_code_generation, language, description)
        (50, False, None, "Very short prompt"),
        (50, True, "python", "Very short Python code prompt"),
        (50, True, "cpp", "Very short C++ code prompt"),
        (500, False, None, "Medium prompt"),
        (500, True, "python", "Medium Python code prompt"),
        (500, True, "java", "Medium Java code prompt"),
        (2000, False, None, "Long prompt"),
        (2000, True, "python", "Long Python code prompt"),
        (2000, True, "rust", "Long Rust code prompt"),
        (5000, False, None, "Very long prompt"),
        (5000, True, "python", "Very long Python code prompt"),
    ]

    logger.info("-" * 80)
    logger.info(
        "| {:^20} | {:^15} | {:^10} | {:^10} |".format(
            "Description", "Prompt Length", "Code Gen?", "Timeout (s)"
        )
    )
    logger.info("-" * 80)

    for prompt_length, is_code_generation, language, description in test_cases:
        timeout = calculate_adaptive_timeout(
            prompt_length, is_code_generation, language
        )

        logger.info(
            "| {:20} | {:15} | {:^10} | {:10.2f} |".format(
                description,
                prompt_length,
                "Yes" if is_code_generation else "No",
                timeout,
            )
        )

    logger.info("-" * 80)


def main():
    """
    Run the tests.
    """
    logger.info("Starting test of adaptive timeout calculation")
    test_adaptive_timeout()
    logger.info("Tests completed successfully!")


if __name__ == "__main__":
    main()
