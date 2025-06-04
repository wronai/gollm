#!/usr/bin/env python3
import asyncio
import logging
import os
import sys
import pytest
from tests.conftest import llm_test, llm_model

from gollm.llm.ollama_adapter import OllamaAdapter, OllamaConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,  # Reduced from DEBUG to INFO for cleaner output
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

@llm_test(timeout=30)  # 30 second timeout for this test
async def test_ollama_code_generation(llm_model):
    """Test basic code generation with the Ollama adapter."""
    logger.info("Initializing Ollama adapter with model: %s", llm_model)
    
    # Initialize the Ollama adapter with the configured model
    config = OllamaConfig(
        model=llm_model,
        timeout=30,  # 30 second timeout
        max_tokens=100,  # Keep responses short for testing
        temperature=0.7,
    )

    # Use the adapter with async context manager
    async with OllamaAdapter(config) as adapter:
        # Simple code completion prompt
        prompt = "def add(a, b):"
        logger.info("Sending request to Ollama...")

        
        try:
            # Generate code using the adapter
            result = await adapter.generate_code(prompt)
            
            # Basic validation of the result
            assert isinstance(result, dict), "Result should be a dictionary"
            assert "success" in result, "Result should contain 'success' key"
            
            if result["success"]:
                logger.info("Code generation successful")
                assert "generated_code" in result, "Successful result should contain 'generated_code'"
                assert isinstance(result["generated_code"], str), "Generated code should be a string"
                logger.debug("Generated code:\n%s", result["generated_code"])
            else:
                logger.error("Code generation failed: %s", result.get("error", "Unknown error"))
                assert "error" in result, "Failed result should contain 'error'"
                
        except Exception as e:
            logger.exception("Test failed with exception")
            raise


# This allows running the test directly with: python -m tests.e2e.test_ollama
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
