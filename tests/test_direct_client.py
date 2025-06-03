#!/usr/bin/env python3
"""
Test the DirectLLMClient with both HTTP and gRPC adapters.

This script tests the DirectLLMClient's ability to generate text and chat completions
using both HTTP and gRPC adapters, with timing information for comparison.
"""

import asyncio
import logging
# Add the src directory to the path so we can import gollm
import sys
import time
from pathlib import Path

src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from gollm.llm.direct_api import DirectLLMClient

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def test_generate(use_grpc=False):
    """Test the generate method with HTTP or gRPC."""
    adapter_type = "gRPC" if use_grpc else "HTTP"
    print(f"\n=== Testing generate with {adapter_type} ===\n")

    start_time = time.time()
    async with DirectLLMClient(
        base_url="http://localhost:11434", use_grpc=use_grpc
    ) as client:
        result = await client.generate(
            model="deepseek-coder:1.3b",
            prompt="Write a simple Python function to calculate the factorial of a number.",
            temperature=0.1,
            max_tokens=500,
        )
    end_time = time.time()

    # Print result and timing
    print(f"\nGenerated response ({adapter_type}):")
    if "response" in result:
        print(
            result["response"][:500] + "..."
            if len(result["response"]) > 500
            else result["response"]
        )
    elif "message" in result and isinstance(result["message"], dict):
        content = result["message"].get("content", "")
        print(content[:500] + "..." if len(content) > 500 else content)

    print(f"\nTime taken: {end_time - start_time:.2f} seconds")

    # Print API-reported timing if available
    if "total_duration" in result:
        duration_ms = (
            result["total_duration"] / 1_000_000
        )  # Convert nanoseconds to milliseconds
        print(f"API-reported duration: {duration_ms:.2f}ms")


async def test_chat(use_grpc=False):
    """Test the chat_completion method with HTTP or gRPC."""
    adapter_type = "gRPC" if use_grpc else "HTTP"
    print(f"\n=== Testing chat with {adapter_type} ===\n")

    start_time = time.time()
    async with DirectLLMClient(
        base_url="http://localhost:11434", use_grpc=use_grpc
    ) as client:
        result = await client.chat_completion(
            model="deepseek-coder:1.3b",
            messages=[
                {
                    "role": "user",
                    "content": "Explain the difference between HTTP and gRPC in 3 sentences.",
                }
            ],
            temperature=0.1,
            max_tokens=500,
        )
    end_time = time.time()

    # Print result and timing
    print(f"\nChat response ({adapter_type}):")
    if "message" in result and isinstance(result["message"], dict):
        content = result["message"].get("content", "")
        print(content[:500] + "..." if len(content) > 500 else content)

    print(f"\nTime taken: {end_time - start_time:.2f} seconds")

    # Print API-reported timing if available
    if "total_duration" in result:
        duration_ms = (
            result["total_duration"] / 1_000_000
        )  # Convert nanoseconds to milliseconds
        print(f"API-reported duration: {duration_ms:.2f}ms")


async def run_tests():
    """Run all tests."""
    # Test with HTTP
    await test_generate(use_grpc=False)
    await test_chat(use_grpc=False)

    # Test with gRPC
    await test_generate(use_grpc=True)
    await test_chat(use_grpc=True)


if __name__ == "__main__":
    asyncio.run(run_tests())
