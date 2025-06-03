# Using goLLM

## Basic Commands

### Code Generation

Generate code from natural language descriptions:

```bash
# Basic code generation
gollm generate "Create a function to sort a list of dictionaries by key"

# Generate with validation
gollm generate "Create a REST API endpoint" --validate

# Fast generation (skips validation)
gollm generate "Quick script to parse CSV" --fast
```

### Code Validation

```bash
# Validate a single file
gollm validate path/to/file.py

# Validate entire project
gollm validate-project

# Validate with specific rules
gollm validate --rules=pep8,security path/to/file.py
```

### Project Management

```bash
# Initialize a new project
gollm init

# Check project status
gollm status

# List all TODOs in project
gollm todo list

# Generate changelog
gollm changelog generate
```

## Advanced Usage

### Using Different Adapters

goLLM supports multiple LLM adapters:

```bash
# Use modular adapter (default)
gollm generate "Create a class" --adapter-type modular

# Use HTTP adapter
gollm generate "Create a class" --adapter-type http
```

### Batch Processing

```bash
# Process all Python files in a directory
gollm process ./src --output ./output

# Process with specific options
gollm process ./src --validate --fix --format
```

### Configuration

Create a `gollm.json` file in your project root:

```json
{
  "validation": {
    "enabled": true,
    "rules": ["pep8", "security", "performance"]
  },
  "generation": {
    "default_adapter": "modular",
    "validate_output": true
  }
}
```

## IDE Integration

### VS Code

1. Install the goLLM extension from the marketplace
2. Set your API key in settings
3. Use the command palette to access goLLM features

### PyCharm/IntelliJ

1. Install the goLLM plugin
2. Configure your preferences in Settings > Tools > goLLM
3. Right-click in the editor to access context menu options

## CI/CD Integration

### GitHub Actions Example

```yaml
name: goLLM Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    - name: Install goLLM
      run: |
        python -m pip install --upgrade pip
        pip install gollm[llm]
    - name: Run validation
      run: gollm validate-project
```

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```bash
   # Install all required dependencies
   pip install -r requirements.txt
   ```

2. **API Key Not Set**
   ```bash
   # Set your API key
   export GOLLM_API_KEY='your-api-key'
   ```

3. **Validation Errors**
   ```bash
   # Get detailed error information
   gollm validate --verbose path/to/file.py
   ```

## Next Steps

- Explore [Examples](../examples/README.md) for real-world use cases
- Check the [API Reference](../api/reference.md) for advanced usage
- Learn how to [contribute](../development/contributing.md) to goLLM
