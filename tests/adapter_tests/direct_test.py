#!/usr/bin/env python3
"""
Direct test for the improved Ollama modular adapter with code generation capabilities.

This script directly tests the OllamaModularAdapter class with improved timeout handling.
"""

import asyncio
import logging
import os
import sys
import time
from typing import Any, Dict

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("direct_test")

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import the modular adapter directly
from gollm.llm.providers.ollama.modular_adapter import OllamaModularAdapter

# Test configuration
CONFIG = {
    "base_url": "http://localhost:11434",  # Update this to your Ollama server address
    "model": "llama3",  # Use any available model
    "timeout": 60,
    "adaptive_timeout": True,
    "token_limit": 2048,
    "temperature": 0.7,
}


async def test_code_generation():
    """Test code generation with adaptive timeout."""
    logger.info("Testing code generation with adaptive timeout")

    async with OllamaModularAdapter(CONFIG) as adapter:
        # Test with prompts of different lengths
        prompts = [
            # Very short prompt
            "Print hello world in Python",
            # Medium prompt
            "Write a Python function that calculates the factorial of a number recursively",
            # Longer prompt
            """Create a Python class called 'DataProcessor' with methods for loading data from CSV files,
            filtering rows based on conditions, calculating aggregate statistics, and saving the processed
            data back to a new CSV file. Include proper error handling and documentation.""",
        ]

        results = []

        for i, prompt in enumerate(prompts):
            logger.info(
                f"\n\nTesting prompt {i+1}/{len(prompts)} - Length: {len(prompt)}"
            )
            logger.info(f"Prompt: {prompt}")

            start_time = time.time()
            result = await adapter.generate(
                prompt=prompt, is_code_generation=True, language="python"
            )
            duration = time.time() - start_time

            if "error" not in result or not result["error"]:
                logger.info(f"Generation successful in {duration:.2f}s!")
                logger.info(f"Generated code:\n{result['text']}")
            else:
                logger.error(
                    f"Generation failed: {result.get('error', 'Unknown error')}"
                )
                if "details" in result:
                    logger.error(f"Details: {result['details']}")

            results.append((prompt, result, duration))

            # Brief pause between tests
            await asyncio.sleep(1)

        return results


async def test_chat_code_generation():
    """Test code generation using the chat method."""
    logger.info("\n\nTesting code generation with chat method")

    async with OllamaModularAdapter(CONFIG) as adapter:
        # Create a simple chat message
        messages = [
            {
                "role": "user",
                "content": "Write a Python function to check if a string is a palindrome",
            }
        ]

        logger.info(f"Chat message: {messages[0]['content']}")

        start_time = time.time()
        result = await adapter.chat(
            messages=messages, is_code_generation=True, language="python"
        )
        duration = time.time() - start_time

        if "error" not in result or not result["error"]:
            logger.info(f"Chat generation successful in {duration:.2f}s!")
            logger.info(f"Generated code:\n{result['text']}")
        else:
            logger.error(
                f"Chat generation failed: {result.get('error', 'Unknown error')}"
            )
            if "details" in result:
                logger.error(f"Details: {result['details']}")

        return result, duration


async def main():
    """Run all tests."""
    logger.info(
        "Starting direct test of Ollama modular adapter with improved code generation"
    )

    try:
        # Test code generation with different prompt lengths
        results = await test_code_generation()

        # Test chat-based code generation
        chat_result, chat_duration = await test_chat_code_generation()

        logger.info("\n\nAll tests completed!")

        # Summary of results
        logger.info("\nTest Summary:")
        for i, (prompt, result, duration) in enumerate(results):
            success = "error" not in result or not result["error"]
            logger.info(
                f"Prompt {i+1}: {'Success' if success else 'Failed'} in {duration:.2f}s"
            )

        chat_success = "error" not in chat_result or not chat_result["error"]
        logger.info(
            f"Chat test: {'Success' if chat_success else 'Failed'} in {chat_duration:.2f}s"
        )

    except Exception as e:
        logger.exception(f"Error during testing: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
