#!/usr/bin/env python3
import asyncio
import logging
import os
import sys
from gollm.llm.ollama_adapter import OllamaAdapter, OllamaConfig

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ollama_test.log')
    ]
)

async def test_ollama():
    # Initialize the Ollama adapter with codellama:7b model
    config = OllamaConfig(
        model="codellama:7b",
        timeout=120,
        max_tokens=2000,
        temperature=0.1
    )
    
    # Use the adapter with async context manager
    async with OllamaAdapter(config) as adapter:
        # Simple code completion prompt
        prompt = "def add(a, b):"
        
        print("\nSending request to Ollama...")
        
        # Generate code using the adapter
        result = await adapter.generate_code(prompt)
        
        # Print the result
        print("\n=== Result ===")
        print(f"Success: {result['success']}")
        if result['success']:
            print("\nGenerated code:")
            print(result['generated_code'])
        else:
            print(f"Error: {result['error']}")
        
        print("\nTest complete!")

if __name__ == "__main__":
    asyncio.run(test_ollama())
