# LLM Integration

## Overview

goLLM supports multiple LLM providers for code generation and analysis. This document explains how to configure different LLM providers.

## Common Settings

### Enable LLM Integration
- **Setting**: `enabled`
- **Default**: `false`
- **Description**: Enable or disable LLM integration.

### Default Provider
- **Setting**: `default_provider`
- **Default**: `"openai"`
- **Options**: `"openai"`, `"ollama"`, `"huggingface"`
- **Description**: Default LLM provider to use.

### Model Selection
- **Setting**: `model`
- **Default**: `"gpt-4"`
- **Description**: Default model to use for generation.

## Provider Configuration

### OpenAI

```json
{
  "llm_integration": {
    "enabled": true,
    "default_provider": "openai",
    "providers": {
      "openai": {
        "api_key": "your-api-key",
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 2048
      }
    }
  }
}
```

### Ollama (Local)

```json
{
  "llm_integration": {
    "enabled": true,
    "default_provider": "ollama",
    "providers": {
      "ollama": {
        "base_url": "http://localhost:11434",
        "model": "codellama:7b",
        "temperature": 0.5
      }
    }
  }
}
```

### Hugging Face

```json
{
  "llm_integration": {
    "enabled": true,
    "default_provider": "huggingface",
    "providers": {
      "huggingface": {
        "api_key": "your-api-key",
        "model": "codellama/CodeLlama-7b-hf",
        "max_new_tokens": 512
      }
    }
  }
}
```

## Advanced Settings

### Caching

```json
{
  "llm_integration": {
    "caching": {
      "enabled": true,
      "ttl": 3600,
      "directory": ".gollm/cache"
    }
  }
}
```

### Rate Limiting

```json
{
  "llm_integration": {
    "rate_limiting": {
      "enabled": true,
      "requests_per_minute": 60
    }
  }
}
```

## Environment Variables

You can also configure LLM settings using environment variables:

```bash
export GOLLM_LLM_ENABLED=true
export GOLLM_LLM_DEFAULT_PROVIDER=openai
export OPENAI_API_KEY=your-api-key
```

## Testing Configuration

To test your LLM configuration:

```bash
# Test LLM connection
gollm test-llm

# Get available models
gollm list-models
```

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   - Verify the API key is set in the config file or environment variables
   - Check for typos in the configuration

2. **Connection Errors**
   - Verify the API endpoint URL is correct
   - Check your internet connection
   - For local models (Ollama), ensure the service is running

3. **Rate Limiting**
   - Check your API provider's rate limits
   - Enable rate limiting in the configuration

## Related Documentation

- [Validation Rules](./validation_rules.md)
- [Project Management](./project_management.md)
- [Advanced Configuration](./advanced.md)
