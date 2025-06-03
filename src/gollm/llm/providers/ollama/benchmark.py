#!/usr/bin/env python3
"""
Benchmark script to compare HTTP and gRPC performance for Ollama API.

This script measures and compares the performance of HTTP and gRPC clients
for communicating with the Ollama API.
"""

import argparse
import asyncio
import json
import logging
import os
import statistics
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("gollm.ollama.benchmark")

# Add the parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import Ollama modules
try:
    from gollm.llm.providers.ollama.config import OllamaConfig
    from gollm.llm.providers.ollama.http import OllamaHttpAdapter

    # Try to import gRPC modules
    try:
        from gollm.llm.providers.ollama.grpc import (GRPC_AVAILABLE,
                                                     OllamaGrpcAdapter)
    except ImportError:
        GRPC_AVAILABLE = False
except ImportError:
    logger.error(
        "Failed to import Ollama modules. Make sure you're running this script from the correct directory."
    )
    sys.exit(1)

# Test prompts of varying complexity
TEST_PROMPTS = {
    "simple": "Write a function to calculate the factorial of a number.",
    "medium": "Create a Python class for a binary search tree with methods for insert, delete, and search.",
    "complex": """Implement a RESTful API using FastAPI with the following endpoints:
    - GET /users: List all users
    - GET /users/{id}: Get user by ID
    - POST /users: Create a new user
    - PUT /users/{id}: Update user
    - DELETE /users/{id}: Delete user
    
    Include proper error handling, validation, and database integration with SQLAlchemy.
    """,
}


async def benchmark_http(
    config: OllamaConfig, prompt: str, iterations: int = 3
) -> Dict[str, Any]:
    """Benchmark HTTP adapter performance.

    Args:
        config: Ollama configuration
        prompt: Prompt to use for benchmarking
        iterations: Number of iterations to run

    Returns:
        Dictionary with benchmark results
    """
    adapter = OllamaHttpAdapter(config)
    durations = []
    tokens = []
    errors = 0

    async with adapter:
        for i in range(iterations):
            logger.info(f"HTTP Iteration {i+1}/{iterations}")
            start_time = time.time()

            try:
                result = await adapter.generate(prompt=prompt, model=config.model)
                duration = time.time() - start_time
                durations.append(duration)

                # Extract token count if available
                if "usage" in result:
                    tokens.append(result["usage"].get("total_tokens", 0))

                logger.info(f"HTTP Iteration {i+1} completed in {duration:.2f}s")
            except Exception as e:
                logger.error(f"HTTP Iteration {i+1} failed: {str(e)}")
                errors += 1

    # Calculate statistics
    stats = {
        "adapter": "http",
        "iterations": iterations,
        "successful": iterations - errors,
        "errors": errors,
    }

    if durations:
        stats.update(
            {
                "min_duration": min(durations),
                "max_duration": max(durations),
                "avg_duration": statistics.mean(durations),
                "median_duration": statistics.median(durations),
            }
        )

    if tokens:
        stats.update(
            {
                "avg_tokens": statistics.mean(tokens),
            }
        )

    return stats


async def benchmark_grpc(
    config: OllamaConfig, prompt: str, iterations: int = 3
) -> Dict[str, Any]:
    """Benchmark gRPC adapter performance.

    Args:
        config: Ollama configuration
        prompt: Prompt to use for benchmarking
        iterations: Number of iterations to run

    Returns:
        Dictionary with benchmark results
    """
    if not GRPC_AVAILABLE:
        return {
            "adapter": "grpc",
            "error": "gRPC not available",
            "iterations": iterations,
            "successful": 0,
            "errors": iterations,
        }

    from gollm.llm.providers.ollama.grpc import OllamaGrpcAdapter

    adapter = OllamaGrpcAdapter(config)
    durations = []
    tokens = []
    errors = 0

    async with adapter:
        for i in range(iterations):
            logger.info(f"gRPC Iteration {i+1}/{iterations}")
            start_time = time.time()

            try:
                result = await adapter.generate(prompt=prompt, model=config.model)
                duration = time.time() - start_time
                durations.append(duration)

                # Extract token count if available
                if "usage" in result:
                    tokens.append(result["usage"].get("total_tokens", 0))

                logger.info(f"gRPC Iteration {i+1} completed in {duration:.2f}s")
            except Exception as e:
                logger.error(f"gRPC Iteration {i+1} failed: {str(e)}")
                errors += 1

    # Calculate statistics
    stats = {
        "adapter": "grpc",
        "iterations": iterations,
        "successful": iterations - errors,
        "errors": errors,
    }

    if durations:
        stats.update(
            {
                "min_duration": min(durations),
                "max_duration": max(durations),
                "avg_duration": statistics.mean(durations),
                "median_duration": statistics.median(durations),
            }
        )

    if tokens:
        stats.update(
            {
                "avg_tokens": statistics.mean(tokens),
            }
        )

    return stats


async def run_benchmarks(
    config: OllamaConfig, prompt_type: str, iterations: int
) -> Dict[str, Any]:
    """Run benchmarks for both HTTP and gRPC adapters.

    Args:
        config: Ollama configuration
        prompt_type: Type of prompt to use (simple, medium, complex)
        iterations: Number of iterations to run

    Returns:
        Dictionary with benchmark results
    """
    prompt = TEST_PROMPTS.get(prompt_type, TEST_PROMPTS["simple"])

    # Run HTTP benchmark
    logger.info(f"Running HTTP benchmark with {prompt_type} prompt...")
    http_stats = await benchmark_http(config, prompt, iterations)

    # Run gRPC benchmark if available
    logger.info(f"Running gRPC benchmark with {prompt_type} prompt...")
    grpc_stats = await benchmark_grpc(config, prompt, iterations)

    # Compare results
    comparison = {}
    if "avg_duration" in http_stats and "avg_duration" in grpc_stats:
        http_avg = http_stats["avg_duration"]
        grpc_avg = grpc_stats["avg_duration"]

        if http_avg > 0:
            improvement = ((http_avg - grpc_avg) / http_avg) * 100
            comparison["improvement_percent"] = improvement
            comparison["faster_adapter"] = "grpc" if improvement > 0 else "http"

    return {
        "prompt_type": prompt_type,
        "prompt": prompt,
        "http": http_stats,
        "grpc": grpc_stats,
        "comparison": comparison,
    }


def setup_argparse():
    """Set up argument parser.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Benchmark HTTP vs gRPC performance for Ollama API"
    )
    parser.add_argument(
        "--url", default="http://localhost:11434", help="Ollama API URL"
    )
    parser.add_argument(
        "--model", default="codellama:7b", help="Model to use for benchmarking"
    )
    parser.add_argument(
        "--prompt-type",
        choices=["simple", "medium", "complex", "all"],
        default="simple",
        help="Type of prompt to use",
    )
    parser.add_argument(
        "--iterations", type=int, default=3, help="Number of iterations to run"
    )
    parser.add_argument("--timeout", type=int, default=60, help="Timeout in seconds")
    parser.add_argument(
        "--output", help="Output file to write results to (JSON format)"
    )

    return parser.parse_args()


async def main():
    """Main function."""
    args = setup_argparse()

    # Create configuration
    config = OllamaConfig(base_url=args.url, model=args.model, timeout=args.timeout)

    # Run benchmarks
    results = {}

    if args.prompt_type == "all":
        for prompt_type in TEST_PROMPTS.keys():
            results[prompt_type] = await run_benchmarks(
                config, prompt_type, args.iterations
            )
    else:
        results[args.prompt_type] = await run_benchmarks(
            config, args.prompt_type, args.iterations
        )

    # Print results
    for prompt_type, result in results.items():
        print(f"\n=== Results for {prompt_type} prompt ===\n")

        http_stats = result["http"]
        grpc_stats = result["grpc"]

        print("HTTP Adapter:")
        print(
            f"  Successful iterations: {http_stats['successful']}/{http_stats['iterations']}"
        )
        if "avg_duration" in http_stats:
            print(f"  Average duration: {http_stats['avg_duration']:.2f}s")
            print(
                f"  Min/Max duration: {http_stats['min_duration']:.2f}s / {http_stats['max_duration']:.2f}s"
            )
        if "avg_tokens" in http_stats:
            print(f"  Average tokens: {http_stats['avg_tokens']:.0f}")

        print("\ngRPC Adapter:")
        if "error" in grpc_stats:
            print(f"  Error: {grpc_stats['error']}")
        else:
            print(
                f"  Successful iterations: {grpc_stats['successful']}/{grpc_stats['iterations']}"
            )
            if "avg_duration" in grpc_stats:
                print(f"  Average duration: {grpc_stats['avg_duration']:.2f}s")
                print(
                    f"  Min/Max duration: {grpc_stats['min_duration']:.2f}s / {grpc_stats['max_duration']:.2f}s"
                )
            if "avg_tokens" in grpc_stats:
                print(f"  Average tokens: {grpc_stats['avg_tokens']:.0f}")

        if "comparison" in result and "improvement_percent" in result["comparison"]:
            improvement = result["comparison"]["improvement_percent"]
            faster = result["comparison"]["faster_adapter"]
            print(
                f"\nComparison: {faster.upper()} is {abs(improvement):.2f}% {'faster' if improvement > 0 else 'slower'}"
            )

    # Write results to file if specified
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults written to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
