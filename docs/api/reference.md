# API Reference

## Core Modules

### `gollm.main`

Main entry point for the goLLM application.

#### `main()`
Main entry point that parses command line arguments and executes the appropriate command.

### `gollm.llm.orchestrator`

Orchestrates LLM operations and manages the execution flow.

#### `LLMOrchestrator`
Main class that handles LLM orchestration.

```python
class LLMOrchestrator:
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the LLM orchestrator with optional configuration."""
        
    def handle_code_generation_request(
        self, 
        prompt: str, 
        context: Optional[Dict] = None,
        validate: bool = True
    ) -> str:
        """Handle a code generation request.
        
        Args:
            prompt: The prompt for code generation
            context: Optional context for the generation
            validate: Whether to validate the generated code
            
        Returns:
            Generated code as a string
        """
```

## CLI Commands

### Code Generation

#### `gollm generate <prompt>`
Generate code from a natural language prompt.

**Options:**
- `--fast`: Skip validation (faster but less reliable)
- `--adapter-type`: Choose adapter type (modular, http)
- `--output`: Output file path

**Example:**
```bash
gollm generate "Create a Python class for a user with name and email"
```

### Code Validation

#### `gollm validate <path>`
Validate code at the given path.

**Options:**
- `--rules`: Comma-separated list of rules to apply
- `--fix`: Automatically fix issues when possible
- `--format`: Format the code

**Example:**
```bash
gollm validate src/ --rules=pep8,security --fix
```

### Project Management

#### `gollm init`
Initialize a new goLLM project.

#### `gollm status`
Show project status and metrics.

## Configuration

goLLM can be configured using a `gollm.json` file in your project root:

```json
{
  "validation": {
    "enabled": true,
    "rules": ["pep8", "security"],
    "ignore": ["tests/*", "migrations/*"]
  },
  "generation": {
    "default_adapter": "modular",
    "validate_output": true,
    "temperature": 0.7,
    "max_tokens": 2000
  },
  "model": {
    "name": "gpt-4",
    "api_key": "${GOLLM_API_KEY}"
  }
}
```

## Error Handling

goLLM uses custom exceptions for error handling:

### `gollm.exceptions.GollmError`
Base exception class for all goLLM exceptions.

### `gollm.exceptions.ValidationError`
Raised when code validation fails.

### `gollm.exceptions.GenerationError`
Raised when code generation fails.

## Utilities

### `gollm.utils.file_utils`

#### `read_file(path: str) -> str`
Read a file and return its contents.

#### `write_file(path: str, content: str) -> None`
Write content to a file.

### `gollm.utils.string_utils`

#### `sanitize_input(text: str) -> str`
Sanitize user input to prevent injection attacks.

## Extending goLLM

### Custom Validators

Create a new validator by subclassing `gollm.validation.CodeValidator`:

```python
from gollm.validation import CodeValidator

class MyCustomValidator(CodeValidator):
    def validate(self, code: str) -> List[ValidationResult]:
        # Your validation logic here
        pass
```

### Custom Adapters

Create a new adapter by implementing the `LLMAdapter` interface:

```python
from typing import Dict, Any
from gollm.llm.base import LLMAdapter

class MyCustomAdapter(LLMAdapter):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    def generate(self, prompt: str, **kwargs) -> str:
        # Your generation logic here
        pass
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=gollm
```

### Writing Tests

Tests should be placed in the `tests/` directory and follow the pattern `test_*.py`.

Example test file:

```python
def test_my_feature():
    # Test setup
    # Test execution
    # Assertions
    pass
```

## Contributing

See [Contributing Guide](../development/contributing.md) for details on how to contribute to goLLM.
