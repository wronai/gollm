# goLLM Documentation

Welcome to the goLLM documentation! This directory contains comprehensive guides and references for using and extending goLLM.

## Documentation Structure

### 📚 [Guides](./guides/README.md)
Step-by-step tutorials and how-to guides for common tasks.

### ⚙️ [Configuration](./configuration/README.md)
Detailed documentation of configuration options and settings.

### 📚 [API Reference](./api/README.md)
Complete reference for goLLM's public API.

## Getting Started

1. **Install goLLM**
   ```bash
   pip install gollm[llm]
   ```

2. **Initialize a Project**
   ```bash
   mkdir myproject
   cd myproject
   gollm init
   ```

3. **Explore the Documentation**
   - [Quick Start Guide](./guides/getting_started.md)
   - [Configuration Options](./configuration/README.md)
   - [API Reference](./api/README.md)

## Documentation Conventions

- **Code blocks** show example usage
- **Bolded terms** indicate important concepts
- `Inline code` represents commands and configuration values
- 🔹 Icons help identify different types of content

## Building the Documentation

To build the documentation locally:

```bash
# Install documentation dependencies
pip install -r docs/requirements.txt

# Build the documentation
cd docs
make html

# View the docs
open _build/html/index.html
```

## Contributing

We welcome contributions to the documentation! Please see our [Contributing Guide](../CONTRIBUTING.md) for details.

## Need Help?

- [GitHub Issues](https://github.com/wronai/gollm/issues) - Report bugs or request features
- [Discussions](https://github.com/wronai/gollm/discussions) - Ask questions and share ideas
- [Examples](./examples/README.md) - Browse example projects
