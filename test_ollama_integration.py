import asyncio
import logging
from gollm.llm.ollama_adapter import OllamaLLMProvider

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

async def test_ollama():
    try:
        print("Testing Ollama integration...")
        config = {
            "model": "codellama:7b",
            "base_url": "http://localhost:11434",
            "timeout": 300,
            "temperature": 0.1,
            "token_limit": 4000
        }
        
        print("Creating provider...")
        provider = OllamaLLMProvider(config)
        
        print("Generating response...")
        response = await provider.generate_response(
            "Write a simple Flask hello world app",
            context={"project_config": {"validation_rules": {}}}
        )
        
        print("\nResponse:", response)
        
        if response.get("success"):
            print("\n✅ Success! Generated code:")
            print("-" * 50)
            print(response.get("generated_code", "No code generated"))
            print("-" * 50)
        else:
            print(f"\n❌ Error: {response.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ollama())
