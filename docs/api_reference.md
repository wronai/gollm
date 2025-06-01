
# docs/api_reference.md
# SPYQ API Reference

## Core Classes

### SpyqCore
Main orchestrator class for SPYQ functionality.

```python
from spyq import SpyqCore

# Initialize
spyq = SpyqCore(config_path="spyq.json")

# Validate files
result = spyq.validate_file("src/myfile.py")
project_result = spyq.validate_project()

# LLM integration
response = await spyq.handle_code_generation("Create a user class")

# Project management
task = spyq.get_next_task()
spyq.record_change("bug_fix", {"description": "Fixed login issue"})
```

### CodeValidator
Validates Python code against quality rules.

```python
from spyq.validation.validators import CodeValidator
from spyq.config.config import SpyqConfig

config = SpyqConfig.load("spyq.json")
validator = CodeValidator(config)

# Validate single file
result = validator.validate_file("myfile.py")
# Returns: {"violations": [Violation...], "quality_score": 85}

# Validate entire project
project_result = validator.validate_project()
```

### LLMOrchestrator
Manages LLM interactions with context.

```python
from spyq.llm.orchestrator import LLMOrchestrator

orchestrator = LLMOrchestrator(config)

response = await orchestrator.handle_code_generation_request(
    "Create a payment processor",
    context={"current_file": "payments.py"}
)
```

## Configuration System

### SpyqConfig
Configuration management class.

```python
from spyq.config.config import SpyqConfig

# Load configuration
config = SpyqConfig.load("spyq.json")

# Access settings
max_lines = config.validation_rules.max_function_lines
llm_enabled = config.llm_integration.enabled

# Create default config
default_config = SpyqConfig.default()
default_config.save("new_spyq.json")
```

### ValidationRules
Quality rules configuration.

```python
from spyq.config.config import ValidationRules

rules = ValidationRules(
    max_function_lines=50,
    max_file_lines=300,
    forbid_print_statements=True,
    require_docstrings=True
)
```

## Validation System

### Violation
Represents a code quality violation.

```python
from spyq.validation.validators import Violation

violation = Violation(
    type="function_too_long",
    message="Function has 75 lines (max: 50)",
    file_path="src/myfile.py",
    line_number=25,
    severity="error",
    suggested_fix="Break into smaller functions"
)
```

### ASTValidator  
AST-based code analysis.

```python
from spyq.validation.validators import ASTValidator

validator = ASTValidator(config, "myfile.py")
violations = validator.violations  # After visiting AST
```

## Project Management

### TodoManager
Manages TODO lists and task creation.

```python
from spyq.project_management.todo_manager import TodoManager

todo_manager = TodoManager(config)

# Add task from violation
task = todo_manager.add_task_from_violation(
    "function_too_long",
    {
        "file_path": "src/myfile.py",
        "line_number": 25,
        "message": "Function too long"
    }
)

# Get next task
next_task = todo_manager.get_next_task()

# Complete task
todo_manager.complete_task(task.id)

# Get statistics
stats = todo_manager.get_stats()
# Returns: {"total": 10, "pending": 7, "completed": 3, "high_priority": 2}
```

### ChangelogManager
Manages CHANGELOG.md updates.

```python
from spyq.project_management.changelog_manager import ChangelogManager

changelog = ChangelogManager(config)

# Record change
entry = changelog.record_change(
    "code_quality_fix",
    {
        "description": "Fixed function complexity issues",
        "files": ["src/processor.py"],
        "violations_fixed": ["high_complexity"],
        "quality_delta": 5
    }
)
```

## LLM Integration

### OllamaAdapter
Local LLM integration via Ollama.

```python
from spyq.llm.ollama_adapter import OllamaAdapter, OllamaConfig

config = OllamaConfig(
    base_url="http://localhost:11434",
    model="codellama:7b",
    timeout=60
)

async with OllamaAdapter(config) as adapter:
    # Check availability
    available = await adapter.is_available()
    
    # List models
    models = await adapter.list_models()
    
    # Generate code
    result = await adapter.generate_code(
        "Create a user authentication function",
        context={"project_rules": {...}}
    )
```

### ContextBuilder
Builds comprehensive context for LLM.

```python
from spyq.llm.context_builder import ContextBuilder

builder = ContextBuilder(config)

context = await builder.build_context({
    "current_file": "auth.py",
    "user_request": "Add password validation"
})

# Context includes:
# - execution_context: Recent errors, logs
# - todo_context: Current tasks, priorities  
# - changelog_context: Recent changes
# - project_config: Quality rules, standards
```

## Utilities

### FileUtils
File operation utilities.

```python
from spyq.utils.file_utils import FileUtils

# Find Python files
py_files = FileUtils.find_python_files("src/")

# Safe file operations
FileUtils.backup_file("important.py")
FileUtils.safe_write("output.py", code_content)

# File hashing
file_hash = FileUtils.get_file_hash("myfile.py")
```

### StringUtils
String manipulation utilities.

```python
from spyq.utils.string_utils import StringUtils

# Case conversion
snake = StringUtils.to_snake_case("CamelCaseFunction")  # "camel_case_function"
camel = StringUtils.to_camel_case("snake_case_var")     # "SnakeCaseVar"

# Code parsing
func_name = StringUtils.extract_function_name("def my_function():")  # "my_function"
class_name = StringUtils.extract_class_name("class MyClass:")        # "MyClass"
```

### Decorators
Useful decorators for SPYQ development.

```python
from spyq.utils.decorators import timer, retry, cache_result

@timer
def slow_function():
    """Function execution time will be logged"""
    pass

@retry(max_attempts=3, delay=1.0)
def unreliable_function():
    """Will retry up to 3 times with 1s delay"""
    pass

@cache_result(ttl_seconds=300)
def expensive_computation():
    """Result cached for 5 minutes"""
    pass
```

## Git Integration

### GitAnalyzer
Git repository analysis.

```python
from spyq.git.analyzer import GitAnalyzer

git = GitAnalyzer(".")

# Check if Git repo
is_repo = git.is_git_repository()

# Get commit info
current_commit = git.get_current_commit_info()
recent_commits = git.get_recent_commits(days=7)

# Get file changes
staged = git.get_staged_files()
modified = git.get_modified_files()
file_history = git.get_file_history("src/myfile.py")

# Branch information
branch_info = git.get_branch_info()
```

## CLI Interface

### Command Line API
All functionality available via CLI.

```bash
# Validation
spyq validate <file>                    # Validate single file
spyq validate-project                   # Validate entire project

# Project management  
spyq status                            # Show project status
spyq next-task                         # Get next TODO task
spyq fix --auto                        # Auto-fix violations

# LLM integration
spyq generate "prompt"                 # Generate code with LLM

# Configuration
spyq config show                       # Show current config
spyq config set key value              # Set config value

# Setup
spyq init                              # Initialize SPYQ
spyq install-hooks                     # Install Git hooks
spyq setup-ide --editor=vscode         # Setup IDE integration
```

## Error Handling

### Common Exceptions

```python
from spyq.exceptions import SpyqValidationError, SpyqConfigError

try:
    result = spyq.validate_file("badfile.py")
except SpyqValidationError as e:
    print(f"Validation failed: {e}")
except SpyqConfigError as e:
    print(f"Configuration error: {e}")
```

## Extension Points

### Custom Validators
Create custom validation rules.

```python
from spyq.validation.validators import CodeValidator

class CustomValidator(CodeValidator):
    def validate_custom_rule(self, content, file_path):
        violations = []
        # Custom validation logic
        return violations
```

### Custom LLM Providers
Integrate with other LLM services.

```python
from spyq.llm.base import BaseLLMProvider

class CustomLLMProvider(BaseLLMProvider):
    async def generate_response(self, prompt, context):
        # Custom LLM integration
        return {"generated_code": "...", "success": True}
```

---

For more examples and advanced usage, see the [examples/](examples/) directory in the repository.