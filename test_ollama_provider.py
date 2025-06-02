#!/usr/bin/env python3
"""Simple test script to verify Ollama provider functionality."""

import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from gollm.llm.providers.ollama.provider import OllamaLLMProvider

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_ollama_provider():
    """Test the Ollama provider with a simple prompt."""
    config = {
        "base_url": "http://localhost:11434",
        "model": "llama3:latest",
        "api_type": "chat",
        "timeout": 60
    }
    
    provider = OllamaLLMProvider(config)
    
    try:
        async with provider as p:
            prompt = "Generate a simple 'Hello, World!' Python program."
            
            print(f"\nSending prompt: {prompt}")
            
            try:
                response = await p.generate_response(
                    prompt=prompt,
                    temperature=0.1,
                    max_tokens=100,
                    stop=["```"]
                )
                
                if not response:
                    logger.error("No response received from generate_response")
                    return False
                    
                print("\nResponse:")
                print("-" * 80)
                print(f"Success: {response.get('success', False)}")
                print(f"Generated text: {response.get('generated_text', '')}")
                print(f"Model: {response.get('model', 'unknown')}")
                print(f"Usage: {response.get('usage', {})}")
                print("-" * 80)
                
                return response.get('success', False)
                
            except Exception as e:
                logger.exception(f"Error in generate_response: {str(e)}")
                return False
            
    except Exception as e:
        logger.exception("Error testing Ollama provider")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_ollama_provider())
    sys.exit(0 if success else 1)
