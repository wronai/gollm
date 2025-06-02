import asyncio
from gollm.llm.providers.ollama.provider import OllamaLLMProvider
from gollm.llm.providers.ollama.config import OllamaConfig

async def test_generate():
    config = {
        'base_url': 'http://rock:8081',
        'model': 'deepseek-coder:latest',
        'api_type': 'chat',
        'timeout': 60
    }
    
    async with OllamaLLMProvider(config) as provider:
        # Test with a simple prompt
        prompt = """
        Write a Python program that prints "Hello, World!" to the console.
        
        RULES:
        - Respond with ONLY the Python code, nothing else
        - No explanations, no markdown, no additional text
        - Just the raw Python code that can be executed directly
        
        Example of the ONLY acceptable response:
        print("Hello, World!")
        
        CODE_ONLY: True
        """.strip()
        
        response = await provider.generate_response(prompt)
        
        print("\n=== Response ===")
        print(f"Success: {response['success']}")
        if response['success']:
            print("\nGenerated code:")
            print(repr(response['generated_text']))
            
            # Try to execute the generated code
            try:
                print("\n=== Execution Result ===")
                exec(response['generated_text'])
            except Exception as e:
                print(f"Error executing code: {e}")
        else:
            print(f"Error: {response.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(test_generate())
