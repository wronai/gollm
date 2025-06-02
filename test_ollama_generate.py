import asyncio
from gollm.llm.providers.ollama.provider import OllamaLLMProvider

async def test_generate():
    config = {
        'base_url': 'http://rock:8081',
        'model': 'deepseek-coder:latest', 
        'api_type': 'chat',
        'timeout': 60
    }
    
    async with OllamaLLMProvider(config) as provider:
        # Test with a very explicit prompt
        prompt = """
        I need a Python program that prints "Hello, World!" to the console.
        
        RULES:
        1. Respond with ONLY the following exact line of code, nothing else:
        print("Hello, World!")
        
        DO NOT include any other text, explanations, or formatting.
        DO NOT use markdown code blocks.
        DO NOT add any comments or additional lines.
        
        Your response should be exactly this single line:
        print("Hello, World!")
        """
        
        response = await provider.generate_response(prompt)
        
        print("\n=== Response ===")
        print(f"Success: {response['success']}")
        if response['success']:
            print("\nGenerated code:")
            print(response['generated_text'])
        else:
            print(f"Error: {response.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(test_generate())
