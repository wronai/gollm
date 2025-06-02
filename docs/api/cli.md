# CLI Reference

## Overview

goLLM provides a command-line interface for common tasks. All commands support the `--help` flag for more information.

## Global Options

| Option | Description |
|--------|-------------|
| `--config PATH` | Path to configuration file |
| `--verbose` | Enable verbose output |
| `--quiet` | Suppress non-essential output |
| `--version` | Show version and exit |

## Commands

### `gollm init [PATH]`

Initialize a new goLLM project.

**Options:**
- `--force`: Overwrite existing configuration
- `--defaults`: Use default configuration

**Examples:**
```bash
# Initialize in current directory
gollm init

# Initialize in specific directory
gollm init my_project
```

### `gollm validate [PATH]`

Validate Python files.

**Options:**
- `--fix`: Automatically fix fixable issues
- `--rules RULES`: Comma-separated list of rule IDs to run
- `--exclude RULES`: Comma-separated list of rule IDs to exclude

**Examples:**
```bash
# Validate current directory
gollm validate

# Validate specific file
gollm validate src/main.py

# Validate with specific rules
gollm validate --rules=line-length,function-length
```

### `gollm generate PROMPT`

Generate code using LLM with quality validation.

**Options:**
- `-o, --output FILE`: Output file or directory path
- `--critical`: Mark as high priority task
- `--no-todo`: Skip creating a TODO item
- `-f, --fast`: Use fast mode with minimal validation
- `-i, --iterations INT`: Number of generation iterations (default: 3)
- `--model MODEL`: Override default model
- `--temperature FLOAT`: Sampling temperature (0.0-2.0)
- `--max-tokens INT`: Maximum number of tokens to generate

**Examples:**
```bash
# Generate code with prompt
gollm generate "Create a Flask web server"

# Save to file
gollm generate "Create a Flask web server" -o app.py

# Use fast mode for quicker results
gollm generate "Create a Flask web server" --fast

# Specify number of iterations
gollm generate "Create a Flask web server" --iterations 2
```

### `gollm direct`

Direct API commands for fast LLM access with minimal processing.

#### `gollm direct generate PROMPT`

Generate text using direct API access without validation pipeline.

**Options:**
- `-m, --model MODEL`: Model to use (default: deepseek-coder:1.3b)
- `-t, --temperature FLOAT`: Sampling temperature (0.0-1.0)
- `--max-tokens INT`: Maximum tokens to generate
- `--api-url URL`: API base URL (default: http://localhost:11434)
- `-o, --output FILE`: Output file path
- `-f, --format FORMAT`: Output format (text or json)
- `--timeout INT`: Request timeout in seconds (default: 60)

**Examples:**
```bash
# Generate code with direct API access
gollm direct generate "Write Hello World in Python"

# Use specific model
gollm direct generate "Write Hello World in Python" --model codellama:7b

# Save output to file
gollm direct generate "Write Hello World in Python" -o hello.py
```

#### `gollm direct chat PROMPT`

Chat with LLM using direct API access without validation pipeline.

**Options:**
- Same as `gollm direct generate`

**Examples:**
```bash
# Chat with LLM using direct API access
gollm direct chat "How do I use asyncio in Python?"

# Get JSON response
gollm direct chat "How do I use asyncio in Python?" --format json
```

### `gollm todo`

Manage TODOs in your project.

**Subcommands:**
- `list`: List all TODOs
- `add "DESCRIPTION"`: Add a new TODO
- `complete ID`: Mark a TODO as complete
- `priority ID LEVEL`: Set TODO priority (high/medium/low)

**Examples:**
```bash
# List all TODOs
gollm todo list

# Add a new TODO
gollm todo add "Fix login bug"

# Complete a TODO
gollm todo complete 1
```

### `gollm changelog`

Manage project changelog.

**Subcommands:**
- `show`: Show changelog
- `add "CHANGE"`: Add a change
- `bump VERSION`: Bump version and update changelog

**Examples:**
```bash
# Show changelog
gollm changelog show

# Add a change
gollm changelog add "Fixed critical security issue"

# Bump version
gollm changelog bump 1.2.3
```

### `gollm config`

Manage configuration.

**Subcommands:**
- `show`: Show current configuration
- `get KEY`: Get a configuration value
- `set KEY VALUE`: Set a configuration value
- `edit`: Edit configuration in default editor

**Examples:**
```bash
# Show all config
gollm config show

# Get specific value
gollm config get validation.max_line_length

# Set a value
gollm config set validation.max_line_length 100
```

## Environment Variables

All CLI options can be set via environment variables with the `GOLLM_` prefix:

```bash
# Equivalent to --verbose
export GOLLM_VERBOSE=1

# Set default model
export GOLLM_MODEL=gpt-4
```

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | File not found |
| 4 | Validation failed |
| 5 | Configuration error |

## Shell Completion

Enable shell completion by adding to your shell's rc file:

**Bash:**
```bash
eval "$(_GOLLM_COMPLETE=bash_source gollm)" >> ~/.bashrc
```

**Zsh:**
```zsh
eval "$(_GOLLM_COMPLETE=zsh_source gollm)" >> ~/.zshrc
```

**Fish:**
```fish
gollm --completion fish > ~/.config/fish/completions/gollm.fish
```

## Configuration File

See [Configuration Reference](../configuration/README.md) for details on the configuration file format.
