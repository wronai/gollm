#!/usr/bin/env python3
"""
Minimal test script for the improved Ollama generator with code generation capabilities.

This script directly tests the OllamaGenerator class with improved timeout handling.
"""

import asyncio
import json
import logging
import os
import sys
import time
from typing import Any, Dict

import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_minimal")

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import only the generator class to avoid dependencies
from gollm.llm.providers.ollama.modules.generation.generator import \
    OllamaGenerator
from gollm.llm.providers.ollama.modules.prompt.code_formatter import \
    CodePromptFormatter

# Test configuration
CONFIG = {
    "base_url": "http://localhost:11434",  # Update this to your Ollama server address
    "model": "llama3",  # Use any available model
    "timeout": 60,
    "show_prompt": True,
    "show_response": True,
    "adaptive_timeout": True,
}


async def test_hello_world():
    """Test simple Hello World code generation."""
    logger.info("Testing Hello World code generation")

    async with aiohttp.ClientSession() as session:
        # Create the generator
        generator = OllamaGenerator(session, CONFIG)

        # Create a code formatter
        code_formatter = CodePromptFormatter(CONFIG)

        # Format a prompt for code generation
        prompt = "Write a Python function that prints 'Hello, World!'"
        formatted_prompt = code_formatter.format_code_prompt(
            prompt=prompt, language="python"
        )

        # Prepare context with code generation flag
        context = {
            "is_code_generation": True,
            "language": "python",
            "adaptive_timeout": True,
        }

        # Generate the response
        logger.info(f"Sending request with prompt: {prompt}")
        start_time = time.time()
        result = await generator.generate(formatted_prompt, context)
        duration = time.time() - start_time

        # Process the result
        if result.get("success", False):
            logger.info(f"Generation successful in {duration:.2f}s!")

            # Clean up the response if needed
            generated_text = result.get("text", "")
            clean_code = code_formatter.extract_code_from_response(
                generated_text, "python"
            )

            logger.info(f"Original text length: {len(generated_text)}")
            logger.info(f"Cleaned code length: {len(clean_code)}")
            logger.info(f"Generated code:\n{clean_code}")
        else:
            logger.error(f"Generation failed: {result.get('error', 'Unknown error')}")
            if "details" in result:
                logger.error(f"Details: {result['details']}")

        return result, duration


async def main():
    """Run the test."""
    try:
        result, duration = await test_hello_world()
        logger.info(f"Test completed in {duration:.2f}s")
    except Exception as e:
        logger.exception(f"Error during testing: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
