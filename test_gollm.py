import asyncio
import logging
from gollm.llm.ollama_adapter import OllamaLLMProvider
from gollm.config.config import GollmConfig

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

async def test_ollama():
    try:
        print("Testing Ollama connection...")
        config = {
            "enabled": True,
            "model": "codellama:7b",
            "base_url": "http://localhost:11434",
            "timeout": 300
        }
        
        provider = OllamaLLMProvider(config)
        
        # Test simple completion
        print("\nTesting completion...")
        response = await provider.complete("Write a Python function that returns 'Hello, World!'")
        print("\nResponse:", response)
        
        return True
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_ollama())
