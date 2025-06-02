# Fast Mode and Direct API Access

## Overview

goLLM now offers two new ways to interact with LLM models that prioritize speed and simplicity:

1. **Fast Mode** - A streamlined version of the standard generation process with minimal validation
2. **Direct API Mode** - Raw API access similar to using curl, bypassing the validation pipeline entirely

These features address the performance difference between direct curl requests to the Ollama API and the standard `gollm -v generate` command, which goes through multiple layers of processing, context building, prompt formatting, and validation.

## Fast Mode

Fast mode streamlines the standard generation process by:

- Limiting to a single iteration instead of multiple attempts
- Using minimal context building
- Implementing simplified validation without extensive code quality checks
- Extracting code blocks directly without complex processing

### Usage

```bash
# Use fast mode with the standard generate command
gollm generate "Create a simple calculator function" --fast

# You can also specify the output file
gollm generate "Create a simple calculator function" --fast -o calculator.py
```

### When to Use Fast Mode

Fast mode is ideal for:

- Quick prototyping where speed is more important than validation
- Simple code generation tasks that don't require extensive quality checks
- Situations where you plan to manually review and modify the generated code

## Direct API Mode

Direct API mode provides raw access to the underlying LLM API (e.g., Ollama) with minimal overhead, similar to using curl directly. This mode:

- Bypasses the entire validation pipeline
- Makes direct HTTP requests to the API
- Returns raw responses without post-processing
- Offers both generate and chat interfaces

### Usage

```bash
# Generate code with direct API access
gollm direct generate "Write a function to calculate factorial"

# Chat with the model
gollm direct chat "Explain how asyncio works in Python"

# Save output to a file
gollm direct generate "Create a Flask app" -o app.py

# Get JSON response
gollm direct generate "Create a React component" --format json

# Use a specific model
gollm direct generate "Write a sorting algorithm" --model codellama:7b
```

### When to Use Direct API Mode

Direct API mode is best for:

- Maximum performance when validation isn't needed
- Getting raw, unprocessed responses from the model
- Debugging or comparing model outputs
- Simple chat interactions that don't require code generation

## Performance Comparison

Here's a general comparison of the three approaches:

| Method | Speed | Validation | Quality Checks | Multiple Iterations | Use Case |
|--------|-------|------------|----------------|---------------------|----------|
| Standard Mode | Slowest | Full | Yes | Yes (up to 3) | Production code generation |
| Fast Mode | Faster | Simplified | Minimal | No (1 iteration) | Quick prototyping |
| Direct API | Fastest | None | None | No | Raw model access, debugging |

## Implementation Details

Both features were implemented as part of a codebase refactoring effort to improve modularity and performance. The implementation includes:

1. A new `DirectLLMClient` class that provides a minimal HTTP client for direct API access
2. A `direct` command group in the CLI with `generate` and `chat` subcommands
3. Modifications to the `LLMOrchestrator` class to support fast mode
4. Simplified validation and code extraction for fast mode

## Configuration

No special configuration is needed to use these features. They work with your existing Ollama setup as defined in your `gollm.json` configuration file.

However, you can customize the behavior by setting environment variables:

```bash
# Set default API URL for direct mode
export GOLLM_API_URL="http://localhost:11434"

# Set default model for direct mode
export GOLLM_MODEL="codellama:7b"
```

## Examples

### Fast Mode Example

```bash
# Generate a simple utility function in fast mode
gollm generate "Create a function to convert temperature between Celsius and Fahrenheit" --fast -o temp_converter.py
```

### Direct API Example

```bash
# Get a direct response from the model
gollm direct generate "Write a Python class for a bank account with deposit and withdraw methods"

# Save to file
gollm direct generate "Write a Python class for a bank account" -o bank_account.py
```

## Troubleshooting

If you encounter issues with the direct API mode, check that:

1. Your Ollama service is running (`ollama serve`)
2. You have the required models pulled (`ollama pull codellama:7b`)
3. The API URL is correct (default: http://localhost:11434)

For fast mode issues, ensure that your goLLM configuration is valid and that the LLM integration is properly configured.
