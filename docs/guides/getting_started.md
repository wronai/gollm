# Getting Started with goLLM

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (optional, for version control)

## Installation

### Using pip

```bash
# Basic installation
pip install gollm

# With LLM support (recommended)
pip install gollm[llm]

# For development
pip install -e .[dev]
```

### From Source

```bash
# Clone the repository
git clone https://github.com/wronai/gollm.git
cd gollm

# Install in development mode
pip install -e .[dev]
```

## Quick Start

### 1. Initialize a Project

```bash
# Create a new directory
mkdir my_project
cd my_project

# Initialize goLLM
gollm init
```

This creates a `gollm.json` configuration file with default settings.

### 2. Validate Your Code

```bash
# Create a Python file
echo 'def hello():
    print("Hello, World!")' > hello.py

# Validate the file
gollm validate hello.py
```

### 3. Generate Code

```bash
# Generate a simple function
gollm generate "Create a function that calculates factorial" -o math_utils.py

# Generate a complete project
gollm generate "Create a Flask web application with user authentication" -o myapp
```

## Project Structure

A typical goLLM project looks like this:

```
my_project/
├── gollm.json        # Configuration file
├── src/             # Source code
│   └── main.py
├── tests/           # Test files
│   └── test_main.py
├── docs/            # Documentation
├── .gollm/          # Cache and temporary files
├── README.md        # Project documentation
└── requirements.txt # Python dependencies
```

## Configuration

Edit `gollm.json` to customize goLLM's behavior:

```json
{
  "version": "0.2.0",
  "validation_rules": {
    "max_line_length": 88,
    "max_function_lines": 50,
    "require_docstrings": true
  },
  "project_management": {
    "todo_integration": true,
    "changelog_integration": true
  },
  "llm_integration": {
    "enabled": true,
    "provider": "openai"
  }
}
```

## Common Tasks

### Validate Code

```bash
# Validate a single file
gollm validate src/main.py

# Validate entire project
gollm validate-project
```

### Generate Code

```bash
# Generate a single file
gollm generate "Create a function to process CSV files" -o csv_utils.py

# Generate a complete project
gollm generate "Create a REST API with FastAPI" -o myapi
```

### Manage TODOs

```bash
# List all TODOs
gollm todo list

# Add a new TODO
gollm todo add "Implement user authentication"

# Complete a TODO
gollm todo complete 1
```

### Update Changelog

```bash
# Show changelog
gollm changelog show

# Add a change
gollm changelog add "Added user authentication"

# Bump version
gollm changelog bump 1.0.0
```

## Next Steps

- [Configuration Guide](../configuration/README.md) - Learn how to customize goLLM
- [API Reference](../api/README.md) - Detailed API documentation
- [Extension Guide](../api/extensions.md) - Create custom rules and commands

## Getting Help

- [GitHub Issues](https://github.com/wronai/gollm/issues) - Report bugs and request features
- [Documentation](https://gollm.readthedocs.io) - Full documentation
- [Discord](https://discord.gg/your-invite-link) - Join the community
