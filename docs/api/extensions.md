# Extending goLLM

## Overview

goLLM is designed to be extensible. You can create custom rules, formatters, and commands to tailor it to your needs.

## Creating Custom Rules

### Rule Structure

Create a new rule by extending `BaseRule`:

```python
from gollm.rules.base import BaseRule

class MyCustomRule(BaseRule):
    """Check for custom patterns in code."""
    
    id = "my-custom-rule"
    description = "Custom rule description"
    severity = "warning"
    
    def check_node(self, node, filename):
        # Your validation logic here
        if self._has_forbidden_pattern(node):
            self.report_violation(
                node.lineno,
                "Found forbidden pattern",
                node=node
            )
```

### Rule Registration

Register your rule in `gollm.json`:

```json
{
  "custom_rules": [
    "my_package.rules.MyCustomRule"
  ]
}
```

## Creating Custom Commands

### Command Structure

Create a new command using the `@command` decorator:

```python
from gollm.cli import command

@command("my-command")
def my_command(args):
    """Description of my command."""
    print("Running my custom command!")
```

### Command Registration

Place your command in a Python package and add it to `gollm.json`:

```json
{
  "plugins": [
    "my_package.commands"
  ]
}
```

## Creating Custom Formatters

### Formatter Structure

Create a formatter by extending `BaseFormatter`:

```python
from gollm.formatters.base import BaseFormatter

class MyFormatter(BaseFormatter):
    """Custom output formatter."""
    
    def format(self, results):
        """Format validation results."""
        output = []
        for result in results:
            output.append(f"{result.filename}:{result.line} - {result.message}")
        return "\n".join(output)
```

### Formatter Registration

Register your formatter in `gollm.json`:

```json
{
  "formatters": {
    "my-formatter": "my_package.formatters.MyFormatter"
  }
}
```

## Creating Plugins

### Plugin Structure

A plugin is a Python package that can contain rules, commands, and formatters:

```
my_plugin/
├── __init__.py
├── commands.py
├── formatters.py
└── rules.py
```

### Plugin Registration

Add your plugin to `gollm.json`:

```json
{
  "plugins": [
    "my_plugin"
  ]
}
```

## Hooks

goLLM provides hooks to extend functionality at specific points:

### Available Hooks

- `pre_validation`: Before validation starts
- `post_validation`: After validation completes
- `pre_generation`: Before code generation
- `post_generation`: After code generation

### Example Hook

```python
from gollm.hooks import register_hook

@register_hook("pre_validation")
async def my_pre_validation_hook(context):
    """Run before validation."""
    print("Running pre-validation hook")
    return context
```

## Events

goLLM emits events that you can listen to:

### Available Events

- `validation_started`: When validation starts
- `validation_completed`: When validation completes
- `generation_started`: When code generation starts
- `generation_completed`: When code generation completes

### Example Event Listener

```python
from gollm.events import event_bus

def on_validation_completed(event):
    print(f"Validation completed with {len(event.results)} results")

event_bus.subscribe("validation_completed", on_validation_completed)
```

## Custom LLM Providers

### Provider Structure

Create a custom LLM provider:

```python
from gollm.llm.base import BaseLLMProvider

class MyLLMProvider(BaseLLMProvider):
    """Custom LLM provider."""
    
    def __init__(self, config):
        super().__init__(config)
        self.name = "my-llm"
    
    async def generate(self, prompt, **kwargs):
        """Generate text from prompt."""
        # Your generation logic here
        return {
            "text": "Generated text",
            "metadata": {}
        }
```

### Provider Registration

Register your provider in `gollm.json`:

```json
{
  "llm_integration": {
    "providers": {
      "my-llm": {
        "class": "my_package.providers.MyLLMProvider"
      }
    }
  }
}
```

## Testing Extensions

### Unit Tests

Create tests for your extensions:

```python
import unittest
from my_package.rules import MyCustomRule

class TestMyCustomRule(unittest.TestCase):
    def test_rule(self):
        rule = MyCustomRule()
        # Test your rule
        self.assertTrue(True)  # Your test assertions
```

### Integration Tests

Test your extension with goLLM:

```python
import unittest
from gollm import GollmCore

class TestMyExtension(unittest.TestCase):
    def test_extension(self):
        gollm = GollmCore()
        # Test your extension with goLLM
        self.assertTrue(True)  # Your test assertions
```

## Best Practices

1. **Keep It Simple**: Extensions should do one thing well
2. **Documentation**: Document your extension's purpose and usage
3. **Error Handling**: Handle errors gracefully
4. **Testing**: Write tests for your extensions
5. **Versioning**: Follow semantic versioning for your extensions

## Distribution

### Package Structure

```
my_extension/
├── setup.py
├── README.md
├── my_extension/
│   ├── __init__.py
│   ├── commands.py
│   ├── rules.py
│   └── formatters.py
└── tests/
    └── test_extension.py
```

### setup.py

```python
from setuptools import setup, find_packages

setup(
    name="gollm-my-extension",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["gollm"],
    entry_points={
        "gollm.plugins": [
            "my_extension = my_extension"
        ]
    }
)
```

## Example Extensions

See the [goLLM Extensions Repository](https://github.com/wronai/gollm-extensions) for example extensions.
