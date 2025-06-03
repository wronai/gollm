#!/usr/bin/env python3
"""
Direct test of the OllamaModularAdapter with adaptive timeout.

This script bypasses the CLI and directly uses the OllamaModularAdapter
to test code generation with adaptive timeout.
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
logger = logging.getLogger("direct_modular_test")

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Configuration for the adapter
CONFIG = {
    "base_url": "http://rock:8081",  # Update this to your Ollama server address
    "model": "qwen3:4b",  # Use any available model
    "timeout": 60,
    "adaptive_timeout": True,
    "token_limit": 2048,
    "temperature": 0.7,
}

# Test prompts
TEST_PROMPTS = [
    {
        "name": "Simple Python Function",
        "prompt": "Write a Python function to add two numbers",
        "language": "python",
        "output_file": "add_numbers.py",
    },
    {
        "name": "Hello World",
        "prompt": "Write Hello World in Python",
        "language": "python",
        "output_file": "hello_world.py",
    },
]


async def test_modular_adapter():
    """
    Test the OllamaModularAdapter with adaptive timeout.
    """
    logger.info("Testing OllamaModularAdapter with adaptive timeout")

    try:
        # Import the necessary components
        import aiohttp

        from gollm.llm.providers.ollama.modular_adapter import \
            OllamaModularAdapter
        from gollm.llm.providers.ollama.modules.prompt.code_formatter import \
            CodePromptFormatter
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        return

    try:
        # Create the adapter
        adapter = OllamaModularAdapter(CONFIG)

        # Create a code formatter for extracting code
        code_formatter = CodePromptFormatter(CONFIG)

        for test_case in TEST_PROMPTS:
            logger.info(f"\n\nTesting: {test_case['name']}")
            logger.info(f"Prompt: {test_case['prompt']}")

            # Set up context for code generation
            context = {
                "is_code_generation": True,
                "language": test_case["language"],
                "adaptive_timeout": True,
            }

            # Generate the response
            start_time = time.time()
            try:
                # Use the adapter directly
                result = await adapter.generate(test_case["prompt"], context)
                duration = time.time() - start_time

                logger.info(f"Generation completed in {duration:.2f}s")
                logger.debug(f"Raw result: {result}")

                if result and "text" in result:
                    # Extract code from the response
                    generated_text = result["text"]
                    logger.debug(f"Generated text: {generated_text}")

                    # Extract code
                    code = code_formatter.extract_code_from_response(
                        generated_text, test_case["language"]
                    )

                    if code and len(code.strip()) > 0:
                        logger.info(f"Successfully extracted code!")

                        # Save the code to a file
                        output_path = os.path.join(
                            os.path.dirname(__file__),
                            "test_output",
                            test_case["output_file"],
                        )
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)

                        with open(output_path, "w") as f:
                            f.write(code)

                        logger.info(f"Saved code to {output_path}")

                        # Test if the code is valid Python
                        if test_case["language"] == "python":
                            try:
                                compile(code, output_path, "exec")
                                logger.info("✅ Code compiles successfully!")
                            except SyntaxError as e:
                                logger.error(f"❌ Code has syntax errors: {e}")
                    else:
                        logger.error("Failed to extract valid code from response")
                else:
                    logger.error(
                        f"Generation failed: {result.get('error', 'Unknown error')}"
                    )
            except Exception as e:
                duration = time.time() - start_time
                logger.exception(
                    f"Exception during generation after {duration:.2f}s: {str(e)}"
                )

            # Brief pause between tests
            await asyncio.sleep(2)
    except Exception as e:
        logger.exception(f"Error during testing: {str(e)}")


async def main():
    """
    Run the tests.
    """
    logger.info("Starting direct test of OllamaModularAdapter with adaptive timeout")

    try:
        await test_modular_adapter()
    except Exception as e:
        logger.exception(f"Error during testing: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
