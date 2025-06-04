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
    # Create a test configuration
    config = {
        "llm_integration": {
            "enabled": True,
            "default_provider": "ollama",
            "fallback_order": ["ollama"],
            "timeout": 30,
            "max_retries": 2,
            "providers": {
                "ollama": {
                    "enabled": True,
                    "priority": 1,
                    "base_url": "http://localhost:11434",
                    "model": "llama2",
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "timeout": 60
                }
            }
        }
    }
    
    # Initialize provider manager
    manager = LLMProviderManager(config['llm_integration'])
    
    # Test prompt
    prompt = "Write a Python function to calculate factorial"
    
    try:
        # Get response from first available provider
        response = await manager.get_response(prompt)
        
        # Print results
        if response.get('success', False):
            print("\n✅ Success!")
            print(f"Model: {response.get('model_info', {}).get('model', 'unknown')}")
            print("\nGenerated code:")
            print(response.get('generated_code', 'No code generated'))
            return True
        else:
            print("\n❌ Failed!")
            print(f"Error: {response.get('error', 'Unknown error')}")
            print(f"Tried providers: {response.get('provider_info', {}).get('tried_providers', [])}")
            return False
            
    except Exception as e:
        print(f"\n❌ Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run the test
    asyncio.run(test_provider_manager())
