#!/usr/bin/env python3
"""
Test script for the Ollama code generation improvements.

This script tests the improved code generation capabilities of the Ollama modular adapter
with the new CodePromptFormatter.
"""

import asyncio
import logging
import os
import sys
from typing import Any, Dict, List

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from gollm.llm.providers.ollama.modular_adapter import OllamaModularAdapter
from gollm.llm.providers.ollama.modules.prompt.code_formatter import \
    CodePromptFormatter

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_code_generation")

# Test configuration
CONFIG = {
    "base_url": "http://localhost:11434",
    "model": "codellama",  # Use a code-focused model if available
    "timeout": 60,
    "show_prompt": True,
    "show_response": True,
    "show_metadata": True,
    "adaptive_timeout": True,
}


async def test_code_generation_completion():
    """Test code generation using the completion API."""
    logger.info("Testing code generation with completion API")

    async with OllamaModularAdapter(CONFIG) as adapter:
        # Test simple function generation
        prompt = (
            "Write a Python function to calculate the Fibonacci sequence up to n terms"
        )

        # Explicitly specify this is a code generation task
        result = await adapter.generate(
            prompt=prompt, is_code_generation=True, language="python"
        )

        if result.get("success", False):
            logger.info("Code generation successful!")
            if "original_text" in result:
                logger.info(
                    f"Response was cleaned up, removing {len(result['original_text']) - len(result['text'])} characters"
                )

            logger.info(f"Generated code:\n{result['text']}")
        else:
            logger.error(
                f"Code generation failed: {result.get('error', 'Unknown error')}"
            )

        return result


async def test_code_generation_chat():
    """Test code generation using the chat API."""
    logger.info("Testing code generation with chat API")

    async with OllamaModularAdapter(CONFIG) as adapter:
        # Test chat-based code generation
        messages = [
            {"role": "system", "content": "You are a helpful coding assistant."},
            {
                "role": "user",
                "content": "Write a JavaScript function to sort an array of objects by a specific property",
            },
        ]

        # Explicitly specify this is a code generation task
        result = await adapter.chat(
            messages=messages, is_code_generation=True, language="javascript"
        )

        if result.get("success", False):
            logger.info("Chat code generation successful!")
            if "original_text" in result:
                logger.info(
                    f"Response was cleaned up, removing {len(result['original_text']) - len(result['text'])} characters"
                )

            logger.info(f"Generated code:\n{result['text']}")
        else:
            logger.error(
                f"Chat code generation failed: {result.get('error', 'Unknown error')}"
            )

        return result


async def test_auto_detection():
    """Test automatic detection of code generation tasks."""
    logger.info("Testing automatic code generation detection")

    async with OllamaModularAdapter(CONFIG) as adapter:
        # This prompt should be automatically detected as a code request
        prompt = "Implement a function that checks if a string is a palindrome"

        result = await adapter.generate(prompt=prompt)

        if result.get("success", False):
            logger.info("Auto-detected code generation successful!")
            logger.info(f"Generated code:\n{result['text']}")
        else:
            logger.error(
                f"Auto-detected code generation failed: {result.get('error', 'Unknown error')}"
            )

        return result


async def test_with_context():
    """Test code generation with additional context."""
    logger.info("Testing code generation with context")

    async with OllamaModularAdapter(CONFIG) as adapter:
        # Provide code context to improve generation
        code_context = """
class DataProcessor:
    def __init__(self, data):
        self.data = data
        
    def filter_data(self, condition):
        return [item for item in self.data if condition(item)]
"""

        file_context = """
project/
├── main.py
├── data_processor.py  # Contains DataProcessor class
└── utils/
    └── helpers.py     # Where we want to add the new function
"""

        prompt = "Add a sort_by_key function to the DataProcessor class that sorts the data by a specified key"

        result = await adapter.generate(
            prompt=prompt,
            is_code_generation=True,
            language="python",
            code_context=code_context,
            file_context=file_context,
        )

        if result.get("success", False):
            logger.info("Code generation with context successful!")
            logger.info(f"Generated code:\n{result['text']}")
        else:
            logger.error(
                f"Code generation with context failed: {result.get('error', 'Unknown error')}"
            )

        return result


async def main():
    """Run all tests."""
    logger.info("Starting code generation tests")

    try:
        # Test completion API
        completion_result = await test_code_generation_completion()

        # Test chat API
        chat_result = await test_code_generation_chat()

        # Test auto-detection
        auto_result = await test_auto_detection()

        # Test with context
        context_result = await test_with_context()

        logger.info("All tests completed!")

    except Exception as e:
        logger.exception(f"Error during testing: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
