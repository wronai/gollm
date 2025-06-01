# Core API Reference

## GollmCore

Main orchestrator class for goLLM functionality.

### Initialization

```python
from gollm import GollmCore

# Initialize with default configuration
gollm = GollmCore()

# Initialize with custom config path
gollm = GollmCore(config_path="path/to/config.json")
```

### Methods

#### `validate_file(file_path: str) -> Dict`
Validate a single file against configured rules.

**Parameters:**
- `file_path`: Path to the file to validate

**Returns:**
```python
{
    "valid": bool,
    "violations": List[Violation],
    "score": float,
    "summary": Dict[str, int]
}
```

#### `validate_project(directory: str = ".") -> Dict`
Validate all Python files in a directory.

**Parameters:**
- `directory`: Directory path to scan (default: current directory)

**Returns:**
```python
{
    "valid": bool,
    "files": Dict[str, FileResult],
    "summary": Dict[str, int],
    "score": float
}
```

#### `async handle_code_generation(prompt: str, context: Dict = None) -> Dict`
Generate code using the configured LLM.

**Parameters:**
- `prompt`: User's code generation request
- `context`: Additional context (optional)

**Returns:**
```python
{
    "code": str,
    "explanation": str,
    "valid": bool,
    "score": float
}
```

## CodeValidator

Validates Python code against quality rules.

### Initialization

```python
from gollm.validation.validators import CodeValidator
from gollm.config.config import GollmConfig

config = GollmConfig.load()
validator = CodeValidator(config)
```

### Methods

#### `validate_file(file_path: str) -> Dict`
Validate a single file.

#### `validate_project(directory: str = ".") -> Dict`
Validate all Python files in a directory.

#### `validate_code(code: str, filename: str = "<string>") -> Dict`
Validate a string containing Python code.

## LLMOrchestrator

Manages interactions with LLM providers.

### Initialization

```python
from gollm.llm.orchestrator import LLMOrchestrator
from gollm.config.config import GollmConfig

config = GollmConfig.load()
orchestrator = LLMOrchestrator(config)
```

### Methods

#### `async generate_code(prompt: str, context: Dict = None) -> Dict`
Generate code based on the given prompt.

**Parameters:**
- `prompt`: Code generation prompt
- `context`: Additional context (optional)

**Returns:**
```python
{
    "code": str,
    "explanation": str,
    "metadata": Dict
}
```

#### `async chat(messages: List[Dict]) -> Dict`
Have a conversation with the LLM.

**Parameters:**
- `messages`: List of message dictionaries with 'role' and 'content'

**Returns:**
```python
{
    "response": str,
    "metadata": Dict
}
```

## FileUtils

Utility functions for file operations.

### Methods

#### `backup_file(file_path: str) -> str`
Create a backup of a file.

#### `safe_write(file_path: str, content: str) -> None`
Safely write content to a file with backup.

#### `get_file_hash(file_path: str) -> str`
Calculate MD5 hash of a file.

## Violation

Represents a code quality violation.

### Attributes
- `rule_id`: str - Identifier of the violated rule
- `message`: str - Description of the violation
- `filename`: str - Path to the file
- `line`: int - Line number
- `column`: int - Column number
- `severity`: str - One of: 'error', 'warning', 'info'
- `context`: str - Code context around the violation

## Configuration

See [Configuration Reference](../configuration/README.md) for detailed configuration options.

## Error Handling

All API methods raise specific exceptions:

- `GollmError`: Base exception class
- `ValidationError`: Raised for validation failures
- `LLMError`: Raised for LLM-related errors
- `ConfigError`: Raised for configuration issues

Example error handling:

```python
try:
    result = gollm.validate_file("myfile.py")
except gollm.ValidationError as e:
    print(f"Validation failed: {e}")
except gollm.GollmError as e:
    print(f"Error: {e}")
```

## Logging

Configure logging using Python's standard logging module:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gollm")
```
