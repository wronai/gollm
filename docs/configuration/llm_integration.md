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
- **Default**: `"ollama"`
- **Options**: `"openai"`, `"ollama"`, `"anthropic"`
- **Description**: Default LLM provider to use.

### Model Selection
- **Setting**: `model`
- **Default**: `"codellama:7b"` (for Ollama)
- **Description**: Default model to use for generation.

## Provider Configuration

### OpenAI

```json
{
  "llm": {
    "enabled": true,
    "default_provider": "openai",
    "providers": {
      "openai": {
        "api_key": "your-openai-api-key",
        "model": "gpt-4-turbo",
        "temperature": 0.1,
        "max_tokens": 4000,
        "timeout": 120
      }
    }
  }
}
```

### Ollama (Local)

```json
{
  "llm": {
    "enabled": true,
    "default_provider": "ollama",
    "providers": {
      "ollama": {
        "base_url": "http://localhost:11434",
        "model": "codellama:7b",
        "timeout": 180,
        "max_tokens": 4000,
        "temperature": 0.1,
        "api_type": "chat"
      }
    }
  }
}
```

### Anthropic

```json
{
  "llm": {
    "enabled": true,
    "default_provider": "anthropic",
    "providers": {
      "anthropic": {
        "api_key": "your-anthropic-api-key",
        "model": "claude-3-sonnet",
        "temperature": 0.1,
        "max_tokens": 4000,
        "timeout": 120
      }
    }
  }
}
```

## Environment Variables

You can also configure providers using environment variables:

```bash
# OpenAI
export OPENAI_API_KEY=your-api-key

# Ollama
export OLLAMA_BASE_URL=http://localhost:11434

# Anthropic
export ANTHROPIC_API_KEY=your-api-key
```

## Provider Priority

If multiple providers are configured, goLLM will use them in this order:
1. The provider specified in the command line (if any)
2. The default provider from config
3. Ollama (if available)
4. OpenAI (if configured)
5. Anthropic (if configured)

## Health Checks

You can verify your LLM provider configuration with:

```bash
gollm health
```

This will check the availability of all configured providers and show their status.

## Advanced Configuration

### Caching

```json
{
  "llm": {
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
  "llm": {
    "rate_limiting": {
      "enabled": true,
      "requests_per_minute": 60
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **Connection Issues**:
   - Verify the provider's base URL is correct
   - Check if the service is running (for local providers like Ollama)
   - Ensure your API keys are valid and have sufficient permissions

2. **Model Not Found**:
   - Verify the model name is correct
   - For Ollama, make sure the model is downloaded locally
   - Check if the model is accessible with your API key

3. **Timeout Errors**:
   - Increase the timeout setting in your configuration
   - Check your network connection
   - For local models, ensure you have sufficient system resources

## Next Steps

- [Getting Started with Ollama](./../guides/ollama_setup.md)
- [Advanced Configuration](./advanced.md)
- [Project Management](./project_management.md)
