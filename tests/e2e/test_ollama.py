#!/usr/bin/env python3
import asyncio
import json
import logging
import os
import sys
import pytest
from datetime import datetime

from tests.conftest import llm_test, llm_model
from gollm.llm.ollama_adapter import OllamaAdapter, OllamaConfig

# Set up logging with timestamps
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for maximum verbosity
    format="%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Add a file handler for detailed logs
log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"test_ollama_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter("%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s", 
                                 datefmt="%Y-%m-%d %H:%M:%S")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

logger.info("Starting test with detailed logging to: %s", log_file)

@llm_test(timeout=120)  # Increased timeout to 120 seconds
async def test_ollama_code_generation(llm_model):
    """Test basic code generation with the Ollama adapter."""
    logger.info("=" * 80)
    logger.info("STARTING TEST: test_ollama_code_generation")
    logger.info("=" * 80)
    logger.info("Initializing Ollama adapter with model: %s", llm_model)
    
    try:
        # Initialize the Ollama adapter with the configured model
        config = OllamaConfig(
            model=llm_model,
            timeout=120,  # Increased timeout
            max_tokens=200,  # Increased max tokens for better responses
            temperature=0.7,
        )
        logger.debug("OllamaConfig created: %s", vars(config))

        # Test Ollama availability first
        logger.info("Testing Ollama service availability...")
        async with OllamaAdapter(config) as adapter:
            is_available = await adapter.is_available()
            logger.info("Ollama service available: %s", is_available)
            assert is_available, "Ollama service is not available"

            # List available models
            try:
                models = await adapter.list_models()
                logger.info("Available models: %s", models)
                assert llm_model in models, f"Configured model {llm_model} not found in available models"
            except Exception as e:
                logger.warning("Failed to list models: %s", str(e))

            # Simple code completion prompt
            prompt = """
            Write a Python function that adds two numbers and returns the result.
            Include type hints and a docstring.
            """
            
            logger.info("Sending code generation request to Ollama...")
            logger.debug("Prompt: %s", prompt)

            try:
                # Generate code using the adapter
                result = await adapter.generate_code(prompt)
                logger.info("Received response from Ollama")
                
                # Log the full result for debugging
                logger.debug("Full response: %s", json.dumps(result, indent=2, default=str))
                
                # Basic validation of the result
                assert isinstance(result, dict), "Result should be a dictionary"
                assert "success" in result, "Result should contain 'success' key"
                
                if result["success"]:
                    logger.info("✓ Code generation successful")
                    logger.debug("Response keys: %s", list(result.keys()))
                    
                    # Check for generated code in different possible locations
                    code = result.get("generated_code") or result.get("response") or result.get("text", "")
                    assert code, "No generated code found in response"
                    assert isinstance(code, str), "Generated code should be a string"
                    
                    logger.info("Generated code:\n%s", code)
                    
                    # Additional validation of the generated code
                    assert "def " in code, "Generated code should contain a function definition"
                    assert "return " in code, "Generated code should contain a return statement"
                    
                else:
                    error_msg = result.get("error", "Unknown error")
                    logger.error("✗ Code generation failed: %s", error_msg)
                    assert False, f"Code generation failed: {error_msg}"
                    
            except Exception as e:
                logger.exception("Error during code generation")
                raise
                
    except Exception as e:
        logger.exception("Test failed with unexpected exception")
        raise
    finally:
        logger.info("=" * 80)
        logger.info("TEST COMPLETED")
        logger.info("=" * 80)


# This allows running the test directly with: python -m tests.e2e.test_ollama
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
