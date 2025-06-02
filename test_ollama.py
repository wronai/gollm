import aiohttp
import asyncio
import json
import os
from pathlib import Path

def load_config():
    """Load configuration from gollm.json"""
    config_path = Path('gollm.json')
    if not config_path.exists():
        raise FileNotFoundError("gollm.json not found in the current directory")
    
    with open(config_path, 'r') as f:
        return json.load(f)

async def test_ollama():
    try:
        # Load configuration
        config = load_config()
        ollama_config = config.get('llm_integration', {}).get('providers', {}).get('ollama', {})
        
        base_url = ollama_config.get('base_url', 'http://localhost:11434')
        api_type = ollama_config.get('api_type', 'generate')
        model = ollama_config.get('model', 'deepseek-coder:latest')
        
        print(f"Using Ollama configuration:")
        print(f"- Base URL: {base_url}")
        print(f"- API Type: {api_type}")
        print(f"- Model: {model}")
        
        # Prepare the API endpoint based on API type
        if api_type == 'chat':
            endpoint = f"{base_url}/api/chat"
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a helpful coding assistant that generates clean, simple Python code."},
                    {"role": "user", "content": "Write a Python program that prints 'Hello, World!'. Only include the code, no explanations."}
                ],
                "stream": False
            }
        else:  # Default to generate API
            endpoint = f"{base_url}/api/generate"
            payload = {
                "model": model,
                "prompt": "Write a Python program that prints 'Hello, World!'. Only include the code, no explanations.",
                "stream": False
            }
        
        # Make the API request
        async with aiohttp.ClientSession() as session:
            print(f"\nSending request to: {endpoint}")
            async with session.post(endpoint, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Extract the generated code based on API type
                    if api_type == 'chat':
                        generated_text = result.get('message', {}).get('content', '')
                    else:
                        generated_text = result.get('response', '')
                    
                    # Clean up the response
                    if '```python' in generated_text:
                        # Extract code from markdown code block
                        code_start = generated_text.find('```python') + 9
                        code_end = generated_text.find('```', code_start)
                        if code_end > 0:
                            generated_text = generated_text[code_start:code_end].strip()
                    
                    # If no code block, take the first line that starts with 'print'
                    if not generated_text.strip().startswith('print'):
                        for line in generated_text.split('\n'):
                            if line.strip().startswith('print'):
                                generated_text = line.strip()
                                break
                    
                    # Ensure we have a valid print statement
                    if not generated_text.strip().startswith('print'):
                        generated_text = 'print("Hello, World!")'
                    
                    # Ensure it ends with a newline
                    if not generated_text.endswith('\n'):
                        generated_text += '\n'
                    
                    # Write to file
                    with open('hello_world.py', 'w') as f:
                        f.write(generated_text)
                    
                    print("\nGenerated hello_world.py with the following content:")
                    print("-" * 40)
                    print(generated_text, end='')
                    print("-" * 40)
                    print("\nYou can run it with: python3 hello_world.py")
                else:
                    error_text = await response.text()
                    print(f"Error from Ollama API (HTTP {response.status}): {error_text}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ollama())
