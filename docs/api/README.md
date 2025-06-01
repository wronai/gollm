# API Reference

This directory contains the complete API reference for goLLM, including core functionality, CLI commands, and extension points.

## Table of Contents

1. [Core API](./core.md) - Main classes and functions
2. [CLI Reference](./cli.md) - Command-line interface documentation
3. [Extensions](./extensions.md) - Creating custom rules, commands, and formatters

## Quick Start

### Core API Example

```python
from gollm import GollmCore

# Initialize
gollm = GollmCore()

# Validate code
result = gollm.validate_file("myfile.py")
print(f"Code quality score: {result['score']}")
```

### CLI Example

```bash
# Validate code
gollm validate src/

# Generate code
gollm generate "Create a Flask web server" -o app.py
```

## Core Concepts

### GollmCore

The main entry point for programmatic access to goLLM functionality.

### Code Validation

- Rule-based code validation
- Custom rule support
- Quality scoring

### LLM Integration

- Multiple LLM provider support
- Code generation
- Chat interface

## Extension Points

- **Rules**: Add custom validation rules
- **Commands**: Add new CLI commands
- **Formatters**: Customize output formatting
- **Hooks**: Run code at specific points
- **Events**: Listen for and react to events

## Best Practices

1. **Error Handling**: Always handle exceptions
2. **Logging**: Use the built-in logging system
3. **Testing**: Write tests for your code
4. **Documentation**: Document your API usage

## Related Documentation

- [Configuration](../configuration/README.md) - Configuration options
- [Guides](../guides/README.md) - Tutorials and how-to guides
