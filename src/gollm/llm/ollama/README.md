# Ollama Integration for GoLLM

This package provides integration with [Ollama](https://ollama.ai/), a self-hosted large language model server, for the GoLLM project.

## Features

- **Model Management**: List, pull, and manage Ollama models
- **Text Generation**: Generate text with configurable parameters
- **Chat Completion**: Support for chat-based interactions
- **Streaming**: Real-time streaming of model responses
- **Health Monitoring**: Check service and model availability
- **Configuration**: Flexible configuration via code or environment variables

## Installation

```bash
pip install gollm[llm]
```

## Quick Start

```python
from gollm.llm.ollama import OllamaLLMProvider

async def main():
    # Initialize the provider
    provider = OllamaLLMProvider({
        "model": "llama2",
        "base_url": "http://localhost:11434"
    })
    
    try:
        # Generate text
        response = await provider.generate("Hello, how are you?")
        print(response["response"])
        
        # Chat completion
        messages = [
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        chat_response = await provider.chat(messages)
        print(chat_response["message"]["content"])
        
        # Stream generation
        async for chunk in provider.stream_generate("Tell me a story about AI:"):
            print(chunk["response"], end="", flush=True)
            
    finally:
        # Cleanup
        await provider.close()

# Run the async function
import asyncio
asyncio.run(main())
```

## Configuration

The `OllamaConfig` class supports the following parameters:

| Parameter       | Type    | Default                  | Description                                      |
|----------------|---------|--------------------------|--------------------------------------------------|
| `base_url`     | str     | `http://localhost:11434` | Base URL of the Ollama server                    |
| `model`        | str     | `llama2`                 | Default model to use                             |
| `timeout`      | int     | 300                      | Request timeout in seconds                       |
| `max_retries`  | int     | 3                        | Number of retries for failed requests            |
| `temperature`  | float   | 0.7                      | Sampling temperature (0.0 to 1.0)                |
| `max_tokens`   | int     | 1000                     | Maximum number of tokens to generate             |
| `top_p`        | float   | 0.9                      | Nucleus sampling parameter                       |
| `top_k`        | int     | 40                       | Top-k sampling parameter                         |
| `repeat_penalty` | float | 1.1                     | Penalty for repeated tokens                      |


### Environment Variables

Configuration can also be set via environment variables with the `GOLLM_OLLAMA_` prefix:

```bash
export GOLLM_OLLAMA_BASE_URL="http://localhost:11434"
export GOLLM_OLLAMA_MODEL="llama2"
export GOLLM_OLLAMA_TIMEOUT="300"
```

## API Reference

### OllamaLLMProvider

Main provider class for interacting with Ollama models.

#### Methods

- `__init__(config: Optional[Dict] = None)`: Initialize with optional configuration
- `initialize() -> None`: Initialize the provider
- `close() -> None`: Clean up resources
- `is_available() -> bool`: Check if the provider is available
- `list_models() -> List[str]`: List available models
- `generate(prompt: str, model: Optional[str] = None, **kwargs) -> Dict`: Generate text
- `chat(messages: List[Dict], model: Optional[str] = None, **kwargs) -> Dict`: Chat completion
- `stream_generate(prompt: str, model: Optional[str] = None, **kwargs) -> AsyncGenerator[Dict, None]`: Stream generated text
- `health_check() -> Dict`: Check service health

## Error Handling

The package defines several custom exceptions:

- `ModelNotFoundError`: Raised when a specified model is not found
- `ModelOperationError`: Raised for errors during model operations
- `ConfigurationError`: Raised for invalid configuration
- `ValidationError`: Raised for validation errors

## Examples

### Using a Custom Model

```python
from gollm.llm.ollama import OllamaLLMProvider

async def main():
    provider = OllamaLLMProvider({
        "model": "codellama:13b",
        "temperature": 0.3,
        "max_tokens": 2000
    })
    
    try:
        response = await provider.generate("Write a Python function to sort a list")
        print(response["response"])
    finally:
        await provider.close()
```

### Handling Errors

```python
from gollm.llm.ollama import OllamaLLMProvider, ModelNotFoundError

async def main():
    provider = OllamaLLMProvider({"model": "nonexistent-model"})
    
    try:
        try:
            response = await provider.generate("Hello")
            print(response["response"])
        except ModelNotFoundError as e:
            print(f"Error: {e}")
            print("Available models:", await provider.list_models())
    finally:
        await provider.close()
```

## Development

### Running Tests

```bash
pytest tests/llm/ollama/test_ollama_adapter.py -v
```

### Code Style

```bash
black src/gollm/llm/ollama/
flake8 src/gollm/llm/ollama/
mypy src/gollm/llm/ollama/
```

## License

Apache-2.0
