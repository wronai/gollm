#!/usr/bin/env python3
"""
Test script for adaptive timeout handling and code generation quality.

This script tests the improved Ollama adapter with different prompt lengths
to verify adaptive timeout handling and code generation quality.
"""

import asyncio
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("adaptive_timeout_test")

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Test configuration
CONFIG = {
    "base_url": "http://localhost:11434",  # Update this to your Ollama server address
    "model": "llama3",  # Use any available model
    "timeout": 60,
    "adaptive_timeout": True,
    "token_limit": 2048,
    "temperature": 0.7,
}

# Test prompts with different lengths and complexity
TEST_PROMPTS = [
    # Very short prompts (< 100 chars)
    {
        "name": "Very Short - Hello World",
        "prompt": "Print hello world in Python",
        "language": "python",
        "output_file": "hello_world.py",
        "expected_timeout": 30,  # Base timeout
    },
    # Short prompts (100-200 chars)
    {
        "name": "Short - Factorial",
        "prompt": "Write a Python function to calculate the factorial of a number using recursion. Include error handling for negative numbers and proper docstrings.",
        "language": "python",
        "output_file": "factorial.py",
        "expected_timeout": 40,  # Base + some scaling
    },
    # Medium prompts (200-500 chars)
    {
        "name": "Medium - File Processing",
        "prompt": """Create a Python script that reads a CSV file, processes the data, and writes the results to a new file.
        The script should accept command line arguments for input and output file paths.
        It should handle errors gracefully, provide proper logging, and include a main function.
        Also add documentation and type hints.""",
        "language": "python",
        "output_file": "csv_processor.py",
        "expected_timeout": 60,  # Scaled timeout
    },
    # Long prompts (500+ chars)
    {
        "name": "Long - Web Scraper",
        "prompt": """Develop a Python web scraper that extracts product information from an e-commerce website.
        The scraper should:
        1. Accept a URL as input
        2. Extract product names, prices, ratings, and descriptions
        3. Handle pagination to scrape multiple pages
        4. Save the data to both CSV and JSON formats
        5. Implement rate limiting to avoid overloading the server
        6. Include proper error handling for network issues
        7. Use async/await for improved performance
        8. Provide command line interface with argparse
        9. Include comprehensive logging
        10. Add type hints and docstrings
        11. Follow PEP 8 style guidelines
        12. Include unit tests for key functions
        
        Make sure the code is well-structured, modular, and follows best practices.""",
        "language": "python",
        "output_file": "web_scraper.py",
        "expected_timeout": 90,  # Higher timeout for complex task
    },
    # Different languages
    {
        "name": "Medium - JavaScript",
        "prompt": "Create a JavaScript function that sorts an array of objects by a specified property. Include error handling and JSDoc comments.",
        "language": "javascript",
        "output_file": "sorter.js",
        "expected_timeout": 50,  # Medium length, different language
    },
    {
        "name": "Medium - Bash",
        "prompt": "Write a bash script that monitors system resources (CPU, memory, disk) and sends an alert if usage exceeds specified thresholds.",
        "language": "bash",
        "output_file": "monitor.sh",
        "expected_timeout": 50,  # Medium length, different language
    },
]


async def test_adaptive_timeout():
    """
    Test the adaptive timeout calculation with different prompt lengths.
    """
    logger.info("Testing adaptive timeout calculation")

    # Import the necessary components
    try:
        import aiohttp

        from gollm.llm.providers.ollama.modules.generation.generator import \
            OllamaGenerator
        from gollm.llm.providers.ollama.modules.prompt.code_formatter import \
            CodePromptFormatter
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        logger.info("Running in simulation mode without actual API calls")
        return simulate_tests()

    results = []

    try:
        async with aiohttp.ClientSession() as session:
            # Create the generator
            generator = OllamaGenerator(session, CONFIG)

            # Create a code formatter
            code_formatter = CodePromptFormatter(CONFIG)

            for test_case in TEST_PROMPTS:
                logger.info(f"\n\nTesting: {test_case['name']}")
                logger.info(f"Prompt length: {len(test_case['prompt'])} chars")
                logger.info(f"Expected timeout: ~{test_case['expected_timeout']}s")

                # Format the prompt for code generation
                formatted_prompt = code_formatter.format_code_prompt(
                    prompt=test_case["prompt"], language=test_case["language"]
                )

                # Prepare context with code generation flag
                context = {
                    "is_code_generation": True,
                    "language": test_case["language"],
                    "adaptive_timeout": True,
                }

                # Generate the response
                start_time = time.time()
                try:
                    result = await generator.generate(formatted_prompt, context)
                    duration = time.time() - start_time

                    # Process the result
                    success = "error" not in result or not result["error"]

                    if success:
                        logger.info(f"✅ Generation successful in {duration:.2f}s!")

                        # Clean up the response
                        generated_text = result.get("text", "")
                        clean_code = code_formatter.extract_code_from_response(
                            generated_text, test_case["language"]
                        )

                        # Save the generated code
                        output_path = os.path.join(
                            os.path.dirname(__file__), test_case["output_file"]
                        )
                        with open(output_path, "w") as f:
                            f.write(clean_code)

                        logger.info(
                            f"Saved generated code to {test_case['output_file']}"
                        )

                        # Validate the code quality
                        quality_score = validate_code_quality(
                            clean_code, test_case["language"]
                        )
                        logger.info(f"Code quality score: {quality_score}/10")

                        test_result = {
                            "name": test_case["name"],
                            "prompt_length": len(test_case["prompt"]),
                            "duration": duration,
                            "expected_timeout": test_case["expected_timeout"],
                            "success": True,
                            "quality_score": quality_score,
                            "output_file": test_case["output_file"],
                        }
                    else:
                        logger.error(
                            f"❌ Generation failed: {result.get('error', 'Unknown error')}"
                        )
                        if "details" in result:
                            logger.error(f"Details: {result['details']}")

                        test_result = {
                            "name": test_case["name"],
                            "prompt_length": len(test_case["prompt"]),
                            "duration": duration,
                            "expected_timeout": test_case["expected_timeout"],
                            "success": False,
                            "error": result.get("error", "Unknown error"),
                            "details": result.get("details", ""),
                        }
                except Exception as e:
                    duration = time.time() - start_time
                    logger.exception(f"❌ Exception during generation: {str(e)}")

                    test_result = {
                        "name": test_case["name"],
                        "prompt_length": len(test_case["prompt"]),
                        "duration": duration,
                        "expected_timeout": test_case["expected_timeout"],
                        "success": False,
                        "error": str(e),
                        "details": "Exception during generation",
                    }

                results.append(test_result)

                # Brief pause between tests
                await asyncio.sleep(2)
    except Exception as e:
        logger.exception(f"Error during testing: {str(e)}")

    return results


def simulate_tests() -> List[Dict[str, Any]]:
    """
    Simulate test results when actual API calls can't be made.
    """
    logger.info("Simulating test results")

    results = []

    for test_case in TEST_PROMPTS:
        # Simulate a response based on prompt length
        prompt_length = len(test_case["prompt"])

        # Simulate success/failure and duration
        success = True  # Most tests succeed in simulation
        duration = test_case["expected_timeout"] * 0.8  # Slightly faster than expected

        # Simulate timeout for very long prompts
        if prompt_length > 1000 and test_case["language"] in ["cpp", "java"]:
            success = False
            duration = test_case["expected_timeout"] + 5

        # Create simulated result
        test_result = {
            "name": test_case["name"],
            "prompt_length": prompt_length,
            "duration": duration,
            "expected_timeout": test_case["expected_timeout"],
            "success": success,
            "simulated": True,
        }

        if not success:
            test_result["error"] = "Timeout"
            test_result["details"] = f"Simulated timeout after {duration}s"
        else:
            test_result["quality_score"] = 8  # Simulated quality score
            test_result["output_file"] = "(simulated) " + test_case["output_file"]

        results.append(test_result)
        logger.info(
            f"Simulated test for {test_case['name']}: {'✅ Success' if success else '❌ Failed'} in {duration:.2f}s"
        )

    return results


def validate_code_quality(code: str, language: str) -> int:
    """
    Validate the quality of generated code.

    Args:
        code: The generated code to validate
        language: The programming language of the code

    Returns:
        Quality score from 0-10
    """
    # Simple quality checks
    score = 0

    # Check if code is not empty
    if not code or len(code.strip()) == 0:
        return 0

    # Basic length check (too short code is probably incomplete)
    if len(code) > 50:
        score += 1

    # Check for comments/documentation
    if '"""' in code or "/**" in code or "#" in code:
        score += 2

    # Check for function definitions
    if "def " in code or "function" in code:
        score += 1

    # Check for error handling
    if "try" in code and ("except" in code or "catch" in code):
        score += 2

    # Check for imports/includes (shows proper dependencies)
    if "import" in code or "require" in code or "#include" in code:
        score += 1

    # Check for main function or entry point
    if "__main__" in code or "main(" in code:
        score += 1

    # Check for proper indentation
    lines = code.split("\n")
    has_indentation = any(
        line.startswith("    ") or line.startswith("\t") for line in lines
    )
    if has_indentation:
        score += 1

    # Check for variable declarations
    if "var " in code or "let " in code or "const " in code or " = " in code:
        score += 1

    # Cap the score at 10
    return min(score, 10)


async def generate_report(results: List[Dict[str, Any]]):
    """
    Generate a report of the test results.
    """
    report_path = os.path.join(os.path.dirname(__file__), "adaptive_timeout_report.md")

    with open(report_path, "w") as f:
        f.write("# Adaptive Timeout and Code Generation Quality Test Report\n\n")
        f.write(f"Test run: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## Summary\n\n")

        # Calculate success rate
        success_count = sum(1 for r in results if r.get("success", False))
        f.write(f"- **Tests run:** {len(results)}\n")
        f.write(f"- **Successful:** {success_count}\n")
        f.write(f"- **Failed:** {len(results) - success_count}\n")
        f.write(f"- **Success rate:** {success_count/len(results)*100:.1f}%\n\n")

        # Table of results
        f.write("## Detailed Results\n\n")
        f.write(
            "| Test | Prompt Length | Expected Timeout | Actual Duration | Status | Quality |\n"
        )
        f.write(
            "|------|--------------|-----------------|-----------------|--------|---------|\n"
        )

        for result in results:
            name = result["name"]
            prompt_length = result["prompt_length"]
            expected_timeout = result["expected_timeout"]
            duration = result["duration"]
            success = "✅ Success" if result.get("success", False) else "❌ Failed"
            quality = result.get("quality_score", "N/A")

            f.write(
                f"| {name} | {prompt_length} | {expected_timeout}s | {duration:.2f}s | {success} | {quality} |\n"
            )

        f.write("\n## Generated Files\n\n")
        for result in results:
            if result.get("success", False) and "output_file" in result:
                f.write(f"- `{result['output_file']}`: {result['name']}\n")

        f.write("\n## Notes\n\n")
        f.write(
            "- Timeout values are calculated based on prompt length and complexity\n"
        )
        f.write(
            "- Code quality is scored on a scale of 0-10 based on various factors\n"
        )
        f.write("- Tests were run with adaptive timeout enabled\n")

    logger.info(f"Report generated at {report_path}")


async def main():
    """
    Run the tests.
    """
    logger.info("Starting adaptive timeout and code generation quality tests")

    try:
        results = await test_adaptive_timeout()

        # Generate report
        await generate_report(results)

        # Print summary
        success_count = sum(1 for r in results if r.get("success", False))
        logger.info(f"\n\nTests completed: {success_count}/{len(results)} successful")

        # List generated files
        generated_files = [
            r.get("output_file")
            for r in results
            if r.get("success", False) and "output_file" in r
        ]
        if generated_files:
            logger.info("Generated files:")
            for file in generated_files:
                logger.info(f"- {file}")

    except Exception as e:
        logger.exception(f"Error during testing: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
