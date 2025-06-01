# Advanced Configuration

## Overview

This document covers advanced configuration options for goLLM, including custom rules, plugins, and integration settings.

## Custom Rules

### Creating Custom Rules

1. Create a `rules` directory in your project root
2. Add Python files with your custom rules
3. Each rule should be a class that extends `BaseRule`

Example custom rule (`rules/custom_rules.py`):

```python
from gollm.rules.base import BaseRule

class NoPrintStatementsRule(BaseRule):
    """Custom rule to forbid print statements."""
    
    id = "no-print"
    description = "Forbid print statements"
    
    def check_node(self, node, filename):
        if isinstance(node, ast.Print):
            self.report_error(
                node.lineno,
                "Print statements are not allowed. Use logging instead."
            )
```

### Registering Custom Rules

Add your custom rules to `gollm.json`:

```json
{
  "custom_rules": [
    "rules.custom_rules.NoPrintStatementsRule"
  ]
}
```

## Plugins

goLLM supports plugins to extend functionality. Plugins can add new commands, rules, and integrations.

### Example Plugin Structure

```
my_plugin/
├── __init__.py
├── commands.py
└── rules.py
```

### Registering Plugins

```json
{
  "plugins": [
    "my_plugin"
  ]
}
```

## Environment-Specific Configuration

You can have different configurations for different environments:

```bash
# gollm.dev.json
gollm --config gollm.dev.json

# gollm.prod.json
gollm --config gollm.prod.json
```

## Performance Tuning

### Cache Settings

```json
{
  "cache": {
    "enabled": true,
    "directory": ".gollm/cache",
    "ttl": 3600
  }
}
```

### Parallel Processing

```json
{
  "performance": {
    "max_workers": 4,
    "chunk_size": 100
  }
}
```

## Security

### Secret Management

```json
{
  "secrets": {
    "backend": "env",
    "env_prefix": "GOLLM_"
  }
}
```

### SSL Configuration

```json
{
  "ssl": {
    "enabled": true,
    "cert_file": "/path/to/cert.pem",
    "key_file": "/path/to/key.pem",
    "verify": true
  }
}
```

## Logging

### Log Levels

```json
{
  "logging": {
    "level": "INFO",
    "file": "gollm.log",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  }
}
```

## Extending goLLM

### Custom Commands

Create a new command:

```python
from gollm.cli import command

@command("my-command")
def my_command(args):
    """My custom command."""
    print("Running my custom command!")
```

### Custom Formatters

Create a custom output formatter:

```python
from gollm.formatters import BaseFormatter

class MyFormatter(BaseFormatter):
    def format(self, results):
        return "\n".join(f"{r.filename}:{r.line} - {r.message}" for r in results)
```

## Migration

### Version Compatibility

Check version compatibility:

```bash
gollm check-version
```

### Configuration Migration

Migrate configuration between versions:

```bash
gollm migrate-config
```

## Related Documentation

- [Validation Rules](./validation_rules.md)
- [Project Management](./project_management.md)
- [LLM Integration](./llm_integration.md)
