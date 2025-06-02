import asyncio
import logging
from gollm.llm.ollama_adapter import OllamaLLMProvider

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

async def main():
    try:
        print("Testing Ollama provider directly...")
        config = {
            "enabled": True,
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
            "Create a simple Flask hello world app",
            context={"project_config": {"validation_rules": {}}}
        )
        
        print("\nResponse:", response)
        
        if response.get("success"):
            print("\n✅ Success! Generated code:")
            print("-" * 50)
            print(response.get("generated_code", "No code generated"))
            print("-" * 50)
            
            # Save to file
            import os
            os.makedirs('test_app', exist_ok=True)
            with open('test_app/app.py', 'w') as f:
                f.write(response.get("generated_code", ""))
            print('\n✅ Saved to test_app/app.py')
        else:
            print(f"\n❌ Error: {response.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
