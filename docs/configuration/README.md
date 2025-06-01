# Configuration Guide

This directory contains detailed documentation for configuring goLLM to suit your project's needs.

## Table of Contents

1. [Validation Rules](./validation_rules.md) - Configure code quality rules and standards
2. [Project Management](./project_management.md) - Set up TODO tracking and changelog management
3. [LLM Integration](./llm_integration.md) - Configure LLM providers and models
4. [Advanced Configuration](./advanced.md) - Custom rules, plugins, and advanced settings

## Quick Start

1. Create a `gollm.json` file in your project root:
   ```bash
   gollm init
   ```

2. Edit the configuration as needed:
   ```json
   {
     "version": "0.2.0",
     "validation_rules": {
       "max_line_length": 88,
       "max_function_lines": 50
     },
     "project_management": {
       "todo_integration": true
     }
   }
   ```

3. Run goLLM with your configuration:
   ```bash
   gollm validate
   ```

## Configuration Precedence

1. Command-line arguments
2. Environment variables
3. `gollm.json` in current directory
4. `~/.config/gollm/config.json`
5. Default values

## Environment Variables

All settings can be set via environment variables using the `GOLLM_` prefix:

```bash
export GOLLM_VALIDATION_RULES_MAX_LINE_LENGTH=100
export GOLLM_PROJECT_MANAGEMENT_TODO_INTEGRATION=true
```

## Next Steps

- [Getting Started](../guides/getting_started.md) - Learn the basics of goLLM
- [API Reference](../api/README.md) - Detailed API documentation
- [Guides](../guides/README.md) - Tutorials and how-to guides
