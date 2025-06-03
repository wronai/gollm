#!/usr/bin/env python3
"""
Test script for the improved Ollama adapter with code generation capabilities.

This script tests the improved timeout handling, code formatting, and response
post-processing in the Ollama modular adapter.
"""

import asyncio
import logging
import os
import sys
import time
from typing import Any, Dict, List

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from gollm.llm.providers.ollama.modular_adapter import OllamaModularAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_ollama_improved")

# Test configuration
CONFIG = {
    "base_url": "http://localhost:11434",  # Update this to your Ollama server address
    "model": "codellama",  # Use a code-focused model if available, or any other model
    "timeout": 60,
    "show_prompt": True,
    "show_response": True,
    "show_metadata": True,
    "adaptive_timeout": True,
}


async def test_simple_code_generation():
    """Test simple code generation with improved timeout handling."""
    logger.info("Testing simple code generation")

    async with OllamaModularAdapter(CONFIG) as adapter:
        # Test with a simple "Hello World" prompt
        prompt = "Write a Python function that prints 'Hello, World!'"

        # Explicitly specify this is a code generation task
        start_time = time.time()
        result = await adapter.generate(
            prompt=prompt, is_code_generation=True, language="python"
        )
        duration = time.time() - start_time

        if result.get("success", False):
            logger.info(f"Code generation successful in {duration:.2f}s!")
            logger.info(f"Generated code:\n{result['text']}")
        else:
            logger.error(
                f"Code generation failed: {result.get('error', 'Unknown error')}"
            )

        return result, duration


async def test_timeout_handling():
    """Test adaptive timeout handling with different prompt lengths."""
    logger.info("Testing adaptive timeout handling")

    results = []

    async with OllamaModularAdapter(CONFIG) as adapter:
        # Test with prompts of different lengths
        prompts = [
            # Very short prompt
            "Print hello world",
            # Medium prompt
            "Create a function that calculates the factorial of a number using recursion",
            # Longer prompt
            """Create a Python class called 'DataProcessor' with methods for loading data from CSV files,
            filtering rows based on conditions, calculating aggregate statistics, and saving the processed
            data back to a new CSV file. Include proper error handling and documentation.""",
        ]

        for i, prompt in enumerate(prompts):
            logger.info(f"Testing prompt {i+1}/{len(prompts)} - Length: {len(prompt)}")

            start_time = time.time()
            result = await adapter.generate(
                prompt=prompt, is_code_generation=True, language="python"
            )
            duration = time.time() - start_time

            if result.get("success", False):
                logger.info(f"Generation successful in {duration:.2f}s!")
                logger.info(f"Generated code length: {len(result['text'])}")
            else:
                logger.error(
                    f"Generation failed: {result.get('error', 'Unknown error')}"
                )

            results.append((prompt, result, duration))

            # Brief pause between tests
            await asyncio.sleep(1)

        return results


async def test_code_formatting():
    """Test the code formatting capabilities."""
    logger.info("Testing code formatting and post-processing")

    async with OllamaModularAdapter(CONFIG) as adapter:
        # Test with a prompt that might generate explanatory text
        prompt = "Write a function to check if a string is a palindrome and explain how it works"

        # First without code generation flag
        logger.info("Testing without code generation flag")
        regular_result = await adapter.generate(prompt=prompt)

        # Then with code generation flag
        logger.info("Testing with code generation flag")
        code_result = await adapter.generate(
            prompt=prompt, is_code_generation=True, language="python"
        )

        # Compare results
        if regular_result.get("success", False) and code_result.get("success", False):
            regular_text = regular_result.get("text", "")
            code_text = code_result.get("text", "")

            logger.info(f"Regular response length: {len(regular_text)}")
            logger.info(f"Code response length: {len(code_text)}")

            # Check if code formatting removed explanations
            if "original_text" in code_result:
                original = code_result["original_text"]
                cleaned = code_result["text"]
                reduction = len(original) - len(cleaned)
                logger.info(
                    f"Code formatting removed {reduction} characters ({reduction/len(original)*100:.1f}%)"
                )

        return regular_result, code_result


async def main():
    """Run all tests."""
    logger.info("Starting Ollama adapter tests with improved code generation")

    try:
        # Test simple code generation
        simple_result, simple_duration = await test_simple_code_generation()
        logger.info(f"Simple code generation completed in {simple_duration:.2f}s")

        # Test timeout handling
        timeout_results = await test_timeout_handling()
        for i, (prompt, result, duration) in enumerate(timeout_results):
            logger.info(f"Prompt {i+1} completed in {duration:.2f}s")

        # Test code formatting
        regular_result, code_result = await test_code_formatting()
        logger.info("Code formatting test completed")

        logger.info("All tests completed!")

    except Exception as e:
        logger.exception(f"Error during testing: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
