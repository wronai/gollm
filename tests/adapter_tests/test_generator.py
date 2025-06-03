#!/usr/bin/env python3
import asyncio
import aiohttp
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import the generator
from gollm.llm.providers.ollama.modules.generation.generator import OllamaGenerator

async def test_generator():
    """Test the OllamaGenerator with adaptive timeout"""
    print("Starting generator test...")
    
    async with aiohttp.ClientSession() as session:
        # Create generator with adaptive timeout enabled
        config = {
            'base_url': 'http://rock:8081',
            'model': 'deepseek-coder:1.3b',  # Using available model
            'timeout': 60,
            'adaptive_timeout': True
        }
        
        # Test with both API types
        await test_chat_api(session, config)
        await test_completion_api(session, config)

async def test_chat_api(session, config):
    """Test the chat API"""
    print("\n===== Testing Chat API =====")
    generator = OllamaGenerator(session, config)
    generator.api_type = 'chat'  # Force chat API
    
    # Test with a simple prompt
    prompt = "Write a simple hello world function in Python"
    print(f"Sending prompt to chat API: {prompt}")
    
    try:
        # First, try a direct API call to verify the server response
        print("Making direct API call to /api/chat...")
        payload = {
            "model": config['model'],
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }
        
        async with session.post(
            f"{config['base_url']}/api/chat",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"Direct API response: {json.dumps(data, indent=2)}")
            else:
                print(f"API error: {response.status} - {await response.text()}")
        
        # Now test through our generator
        print("\nTesting through generator...")
        result = await generator.generate(prompt, {'adaptive_timeout': True})
        print(f"Generation successful!")
        print(f"Generated text: {result.get('text', '')}")
        print(f"Metadata: {result.get('metadata', {})}")
    except Exception as e:
        print(f"Error during chat generation: {str(e)}")

async def test_completion_api(session, config):
    """Test the completion API"""
    print("\n===== Testing Completion API =====")
    generator = OllamaGenerator(session, config)
    generator.api_type = 'completion'  # Force completion API
    
    # Test with a simple prompt
    prompt = "Write a simple hello world function in Python"
    print(f"Sending prompt to completion API: {prompt}")
    
    try:
        # First, try a direct API call to verify the server response
        print("Making direct API call to /api/generate...")
        payload = {
            "model": config['model'],
            "prompt": prompt,
            "stream": False
        }
        
        async with session.post(
            f"{config['base_url']}/api/generate",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"Direct API response: {json.dumps(data, indent=2)}")
            else:
                print(f"API error: {response.status} - {await response.text()}")
        
        # Now test through our generator
        print("\nTesting through generator...")
        result = await generator.generate(prompt, {'adaptive_timeout': True, 'api_type': 'completion'})
        print(f"Generation successful!")
        print(f"Generated text: {result.get('text', '')}")
        print(f"Metadata: {result.get('metadata', {})}")
    except Exception as e:
        print(f"Error during completion generation: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_generator())
