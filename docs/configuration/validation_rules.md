# Validation Rules

## Overview

Validation rules define the code quality standards enforced by goLLM. These rules help maintain consistent code quality across your project.

## Core Validation Rules

### Line Length
- **Setting**: `max_line_length`
- **Default**: 88
- **Description**: Maximum allowed line length in characters.

### Function Length
- **Setting**: `max_function_lines`
- **Default**: 50
- **Description**: Maximum number of lines allowed in a function.

### File Length
- **Setting**: `max_file_lines`
- **Default**: 300
- **Description**: Maximum number of lines allowed in a file.

### Cyclomatic Complexity
- **Setting**: `max_cyclomatic_complexity`
- **Default**: 10
- **Description**: Maximum cyclomatic complexity allowed in functions.

### Function Parameters
- **Setting**: `max_function_params`
- **Default**: 5
- **Description**: Maximum number of parameters allowed in a function.

## Code Style Rules

### Print Statements
- **Setting**: `forbid_print_statements`
- **Default**: `true`
- **Description**: Whether to forbid `print()` statements in favor of logging.

### Global Variables
- **Setting**: `forbid_global_variables`
- **Default**: `true`
- **Description**: Whether to forbid global variables.

### Docstrings
- **Setting**: `require_docstrings`
- **Default**: `true`
- **Description**: Whether to require docstrings for modules, classes, and functions.

### Type Hints
- **Setting**: `require_type_hints`
- **Default**: `false`
- **Description**: Whether to require type hints in function signatures.

### Naming Conventions
- **Setting**: `naming_convention`
- **Default**: `"snake_case"`
- **Options**: `"snake_case"`, `"camelCase"`, `"PascalCase"`
- **Description**: Naming convention to enforce for variables, functions, and classes.

## Example Configuration

```json
{
  "validation_rules": {
    "max_function_lines": 50,
    "max_file_lines": 300,
    "max_cyclomatic_complexity": 10,
    "max_function_params": 5,
    "max_line_length": 88,
    "forbid_print_statements": true,
    "forbid_global_variables": true,
    "require_docstrings": true,
    "require_type_hints": false,
    "naming_convention": "snake_case"
  }
}
```

## Customizing Rules

You can customize these rules by creating or modifying the `gollm.json` file in your project root. Run `gollm validate` to check your code against the current rules.

## Rule Severity

Each rule can have one of the following severity levels:
- `error`: Will fail the validation
- `warning`: Will show a warning but pass validation
- `off`: Disables the rule

## Disabling Rules

To disable a specific rule, you can either:
1. Set it to `false` in the configuration
2. Or set its severity to `"off"`

## Next Steps

- [Project Management Configuration](../configuration/project_management.md)
- [LLM Integration](../configuration/llm_integration.md)
- [Advanced Configuration](../configuration/advanced.md)
