#!/usr/bin/env python3
"""Test script for LLM provider manager."""
import asyncio
import logging
import os
from dotenv import load_dotenv
from gollm.llm.provider_manager import LLMProviderManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_provider_manager():
    """Test the provider manager with different configurations."""
    # Load configuration from gollm.json
    import json
    with open('gollm.json') as f:
        config = json.load(f)
    
    # Initialize provider manager
    manager = LLMProviderManager(config['llm_integration'])
    
    # Test prompt
    prompt = "Write a Python function to calculate factorial"
    
    # Get response from first available provider
    response = await manager.get_response(prompt)
    
    # Print results
    if response.get('success', False):
        print("\n✅ Success!")
        print(f"Model: {response['model_info']['model']}")
        print("\nGenerated code:")
        print(response['generated_code'])
    else:
        print("\n❌ Failed!")
        print(f"Error: {response.get('error', 'Unknown error')}")
        print(f"Tried providers: {response.get('provider_info', {}).get('tried_providers', [])}")

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run the test
    asyncio.run(test_provider_manager())
