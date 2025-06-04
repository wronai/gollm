import aiohttp
import asyncio
import json

async def test_ollama_direct():
    url = "http://rock:8081/api/generate"
    
    # Very simple and direct prompt
    prompt = """
    Write a Python program that prints "Hello, World!" to the console.
    
    Respond with ONLY the Python code, nothing else.
    No explanations, no markdown, no additional text.
    Just the code.
    """.strip()
    
    payload = {
        "model": "deepseek-coder:latest",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.1,
            "num_ctx": 4096,
            "num_predict": 100,
            "stop": ["\n"]
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                print("\n=== Raw Response ===")
                print(json.dumps(result, indent=2))
                
                generated_text = result.get('response', '').strip()
                print("\n=== Extracted Text ===")
                print(repr(generated_text))
                
                # Try to extract just the code
                if '```' in generated_text:
                    parts = generated_text.split('```')
                    if len(parts) > 1:
                        code_part = parts[1]
                        if code_part.startswith('python'):
                            code_part = code_part[6:].lstrip('\n')
                        generated_text = code_part.split('```')[0].strip()
                
                print("\n=== Final Code ===")
                print(repr(generated_text))
                
                # Try to get just the first line that looks like code
                for line in generated_text.split('\n'):
                    line = line.strip()
                    if line and (line.startswith('print(') or line.startswith('def ') or line.startswith('import ')):
                        print("\n=== Cleaned Code ===")
                        print(repr(line))
                        break
            else:
                print(f"Error: {response.status}")
                print(await response.text())

if __name__ == "__main__":
    asyncio.run(test_ollama_direct())
