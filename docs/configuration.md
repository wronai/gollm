# docs/configuration.md
# goLLM Configuration Guide

## 📋 Overview

goLLM uses a `gollm.json` file for configuration. This guide covers all available settings and how to customize them for your project.

## 🔧 Basic Configuration

### Default Configuration
```json
{
  "version": "0.2.0",
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
  },
  "project_management": {
    "todo_integration": true,
    "auto_create_tasks": true,
    "todo_file": "TODO.md",
    "changelog_integration": true,
    "auto_update_changelog": true,
    "changelog_file": "CHANGELOG.md"
  },
  "llm_integration": {
    "enabled": false,
    "providers": {
      "openai": {
        "enabled": false,
        "model": "gpt-4"
      },
      "ollama": {
        "enabled": false,
        "model": "codellama:7b"
      }
    }
  }
}
```

## 📏 Validation Rules

### Code Structure Rules

#### `max_function_lines` (default: 50)
Maximum allowed lines in a single function.
```json
"max_function_lines": 30  // Stricter limit
```

#### `max_file_lines` (default: 300)
Maximum allowed lines in a single file.
```json
"max_file_lines": 500  // More permissive
```

#### `max_function_params` (default: 5)
Maximum number of parameters in a function.
```json
"max_function_params": 3  // Encourage simpler interfaces
```

### Complexity Rules

#### `max_cyclomatic_complexity` (default: 10)
Maximum cyclomatic complexity for functions.
```json
"max_cyclomatic_complexity": 8  // Lower complexity
```

#### `max_line_length` (default: 88)
Maximum line length (follows Black formatter).
```json
"max_line_length": 120  // Wider lines
```

### Code Quality Rules

#### `forbid_print_statements` (default: true)
Prohibit print() statements in code.
```json
"forbid_print_statements": false  // Allow prints for debugging
```

#### `forbid_global_variables` (default: true)
Prohibit global variable usage.
```json
"forbid_global_variables": false  // Allow globals
```

#### `require_docstrings` (default: true)
Require docstrings for all functions.
```json
"require_docstrings": false  // Make docstrings optional
```

#### `require_type_hints` (default: false)
Require type hints for function parameters and returns.
```json
"require_type_hints": true  // Enforce type hints
```

#### `naming_convention` (default: "snake_case")
Enforce naming convention.
```json
"naming_convention": "camelCase"  // Alternative: "PascalCase"
```

## 📋 Project Management

### TODO Integration

#### `todo_integration` (default: true)
Enable automatic TODO management.
```json
"todo_integration": false  // Disable TODO features
```

#### `auto_create_tasks` (default: true)
Automatically create TODO tasks from violations.
```json
"auto_create_tasks": false  // Manual task creation only
```

#### `todo_file` (default: "TODO.md")
Path to TODO file.
```json
"todo_file": "docs/tasks.md"  // Custom location
```

### CHANGELOG Integration

#### `changelog_integration` (default: true)
Enable automatic CHANGELOG updates.
```json
"changelog_integration": false  // Disable CHANGELOG
```

#### `auto_update_changelog` (default: true)
Automatically update CHANGELOG on changes.
```json
"auto_update_changelog": false  // Manual updates only
```

#### `changelog_file` (default: "CHANGELOG.md")
Path to CHANGELOG file.
```json
"changelog_file": "docs/HISTORY.md"  // Custom location
```

### Priority Mapping
```json
"priority_mapping": {
  "critical": "🔴 URGENT",
  "major": "🟡 HIGH", 
  "minor": "🟢 NORMAL"
}
```

## 🤖 LLM Integration

### Basic LLM Settings

#### `enabled` (default: false)
Enable LLM integration.
```json
"enabled": true
```

#### `max_iterations` (default: 3)
Maximum LLM improvement iterations.
```json
"max_iterations": 5  // More thorough refinement
```

#### `token_limit` (default: 4000)
Maximum tokens per LLM request.
```json
"token_limit": 8000  // Longer responses
```

### Provider Configuration

#### OpenAI Provider
```json
"providers": {
  "openai": {
    "enabled": true,
    "model": "gpt-4",
    "api_key_env": "OPENAI_API_KEY",
    "temperature": 0.1,
    "max_tokens": 4000
  }
}
```

#### Anthropic Provider
```json
"providers": {
  "anthropic": {
    "enabled": true,
    "model": "claude-3-sonnet-20240229",
    "api_key_env": "ANTHROPIC_API_KEY",
    "temperature": 0.1,
    "max_tokens": 4000
  }
}
```

#### Ollama Provider (Local)
```json
"providers": {
  "ollama": {
    "enabled": true,
    "base_url": "http://localhost:11434",
    "model": "codellama:7b",
    "timeout": 60,
    "temperature": 0.1
  }
}
```

## 🛡️ Enforcement Settings

### `block_save` (default: false)
Block file saving when violations exist.
```json
"enforcement": {
  "block_save": true  // Prevent saving bad code
}
```

### `block_execution` (default: false)
Block code execution when violations exist.
```json
"enforcement": {
  "block_execution": true  // Prevent running bad code
}
```

### `auto_fix_enabled` (default: true)
Enable automatic fixing of violations.
```json
"enforcement": {
  "auto_fix_enabled": false  // Manual fixes only
}
```

### `real_time_validation` (default: true)
Enable real-time validation during editing.
```json
"enforcement": {
  "real_time_validation": false  // Validate on save only
}
```

## 🔔 Notifications

### `show_violations` (default: true)
Show violation notifications.
```json
"notifications": {
  "show_violations": false  // Quiet mode
}
```

### `suggest_refactoring` (default: true)
Show refactoring suggestions.
```json
"notifications": {
  "suggest_refactoring": false  // No refactoring hints
}
```

### `desktop_notifications` (default: false)
Enable desktop notifications.
```json
"notifications": {
  "desktop_notifications": true  // Show system notifications
}
```

## 🔗 Git Integration

### `pre_commit_validation` (default: true)
Validate code before commits.
```json
"git_integration": {
  "pre_commit_validation": false  // Skip pre-commit checks
}
```

### `post_commit_updates` (default: true)
Update documentation after commits.
```json
"git_integration": {
  "post_commit_updates": false  // Manual doc updates
}
```

### `auto_commit_fixes` (default: false)
Automatically commit auto-fixes.
```json
"git_integration": {
  "auto_commit_fixes": true  // Auto-commit improvements
}
```

## 🎯 Team Configurations

### Strict Team Setup
```json
{
  "validation_rules": {
    "max_function_lines": 25,
    "max_file_lines": 200,
    "max_cyclomatic_complexity": 5,
    "max_function_params": 3,
    "require_docstrings": true,
    "require_type_hints": true,
    "forbid_print_statements": true
  },
  "enforcement": {
    "block_save": true,
    "block_execution": true,
    "real_time_validation": true
  }
}
```

### Permissive Setup
```json
{
  "validation_rules": {
    "max_function_lines": 100,
    "max_file_lines": 1000,
    "max_cyclomatic_complexity": 15,
    "forbid_print_statements": false,
    "require_docstrings": false
  },
  "enforcement": {
    "block_save": false,
    "block_execution": false,
    "auto_fix_enabled": true
  }
}
```

### Learning/Educational Setup
```json
{
  "validation_rules": {
    "max_function_lines": 30,
    "require_docstrings": true,
    "forbid_print_statements": false
  },
  "notifications": {
    "suggest_refactoring": true,
    "desktop_notifications": true
  },
  "llm_integration": {
    "enabled": true,
    "max_iterations": 2
  }
}
```

## 🔧 Configuration Management

### Environment-specific Configs
```bash
# Development
cp gollm.dev.json gollm.json

# Production  
cp gollm.prod.json gollm.json

# Testing
cp gollm.test.json gollm.json
```

### Using CLI for Configuration
```bash
# View current config
gollm config show

# Set individual values
gollm config set validation_rules.max_function_lines 40
gollm config set llm_integration.enabled true

# Reset to defaults
gollm config reset

# Validate configuration
gollm config validate
```

### Configuration Inheritance
```json
{
  "extends": "./team-base.json",
  "validation_rules": {
    "max_function_lines": 60  // Override team default
  }
}
```

## 🔄 Migration Between Versions

### Automatic Migration
```bash
# Migrate configuration to latest version
gollm config migrate --to-version 0.2.0

# Backup created automatically as gollm.json.backup
```

### Manual Migration
```bash
# Check configuration compatibility
gollm config check-compatibility

# Show migration recommendations
gollm config migration-guide
```

## 🎛️ Advanced Configuration

### Custom Validation Rules
```json
{
  "custom_rules": {
    "max_nested_loops": 2,
    "max_try_except_blocks": 3,
    "forbid_specific_imports": ["os.system", "eval", "exec"]
  }
}
```

### Integration with External Tools
```json
{
  "external_integrations": {
    "black": {
      "enabled": true,
      "line_length": 88
    },
    "flake8": {
      "enabled": true,
      "max_line_length": 88,
      "ignore": ["E203", "W503"]
    },
    "mypy": {
      "enabled": true,
      "strict": true
    }
  }
}
```

### Performance Settings
```json
{
  "performance": {
    "parallel_validation": true,
    "max_workers": 4,
    "cache_validation_results": true,
    "cache_duration_minutes": 30
  }
}
```

## 📊 Monitoring and Reporting

### Quality Metrics
```json
{
  "metrics": {
    "track_quality_trends": true,
    "quality_threshold": 80,
    "generate_reports": true,
    "report_frequency": "weekly"
  }
}
```

### Logging Configuration
```json
{
  "logging": {
    "level": "INFO",
    "file": ".gollm/logs/gollm.log",
    "max_size_mb": 10,
    "backup_count": 5
  }
}
```

## 🚨 Troubleshooting Configuration

### Common Issues

**Configuration not loading:**
```bash
# Check file syntax
gollm config validate

# Reset to defaults
gollm config reset
```

**LLM not working:**
```bash
# Test LLM connection
gollm config test-llm

# Check API keys
echo $OPENAI_API_KEY
```

**Git hooks not triggering:**
```bash
# Reinstall hooks
gollm install-hooks

# Check permissions
ls -la .git/hooks/
```

### Debug Mode
```json
{
  "debug": {
    "enabled": true,
    "verbose_logging": true,
    "save_llm_conversations": true
  }
}
```

---

For more examples and team setups, see [examples/configurations/](../examples/configurations/) directory.

# docs/llm_integration.md
# goLLM LLM Integration Guide

## 🎯 Overview

goLLM integrates with Large Language Models to provide intelligent code generation, automatic fixes, and context-aware suggestions. This guide covers setup, usage, and best practices.

## 🔌 Supported LLM Providers

### 1. OpenAI (GPT Models)
- **Models:** GPT-4, GPT-3.5-turbo, GPT-4-turbo
- **Strengths:** High quality, fast responses
- **Cost:** Pay-per-token
- **Best for:** Production environments, complex code generation

### 2. Anthropic (Claude Models)  
- **Models:** Claude-3-sonnet, Claude-3-haiku, Claude-3-opus
- **Strengths:** Long context, careful reasoning
- **Cost:** Pay-per-token
- **Best for:** Complex refactoring, documentation

### 3. Ollama (Local Models)
- **Models:** CodeLlama, Phind-CodeLlama, WizardCoder, StarCoder
- **Strengths:** Privacy, no API costs, offline usage
- **Cost:** Free (hardware requirements)
- **Best for:** Privacy-sensitive projects, development

## ⚙️ Setup Guide

### OpenAI Setup
```bash
# 1. Get API key from platform.openai.com
export OPENAI_API_KEY="sk-..."

# 2. Enable in goLLM
gollm config set llm_integration.enabled true
gollm config set llm_integration.providers.openai.enabled true
gollm config set llm_integration.providers.openai.model gpt-4

# 3. Test connection
gollm generate "Create a hello world function"
```

### Anthropic Setup
```bash
# 1. Get API key from console.anthropic.com
export ANTHROPIC_API_KEY="sk-ant-..."

# 2. Enable in goLLM
gollm config set llm_integration.enabled true
gollm config set llm_integration.providers.anthropic.enabled true
gollm config set llm_integration.providers.anthropic.model claude-3-sonnet-20240229

# 3. Test connection
gollm generate "Create a data validation class"
```

### Ollama Setup (Detailed in ollama_setup.md)
```bash
# 1. Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Pull model
ollama pull codellama:7b

# 3. Configure goLLM
gollm config set llm_integration.enabled true
gollm config set llm_integration.providers.ollama.enabled true
gollm config set llm_integration.providers.ollama.model codellama:7b
```

## 🚀 Usage Examples

### Basic Code Generation
```bash
# Simple function
gollm generate "Create a function to validate email addresses"

# Class with methods
gollm generate "Create a User class with authentication methods"

# Complex logic
gollm generate "Create a payment processor that handles multiple payment methods"
```

### Context-Aware Generation
goLLM automatically provides rich context to the LLM:

```bash
# LLM receives:
# - Your project's quality rules (max 50 lines, no prints, etc.)
# - Recent errors and issues
# - Current TODO tasks
# - Code style standards
# - File structure and dependencies

gollm generate "Create a user registration system"
```

### Auto-fixing Existing Code
```bash
# Fix specific file
gollm fix --llm src/problematic_file.py

# Fix all violations
gollm fix --auto --llm

# Interactive fixing
gollm fix --interactive
```

### Iterative Improvement
```bash
# goLLM automatically iterates with LLM until quality standards are met:

$ gollm generate "Create a data processor"

🤖 LLM Generation (Attempt 1)...
❌ Validation failed: 3 violations found
   - Function too long (75 lines, max: 50)  
   - Too many parameters (8, max: 5)
   - Missing docstring

🔄 Sending feedback to LLM...

🤖 LLM Generation (Attempt 2)...
❌ Validation failed: 1 violation found
   - Complexity too high (12, max: 10)

🔄 Sending feedback to LLM...

🤖 LLM Generation (Attempt 3)...
✅ All validations passed!
📝 TODO updated: 0 new tasks
📝 CHANGELOG updated: Code generation entry
💾 Code saved: data_processor.py
```

## 🎛️ Advanced Configuration

### Provider Selection Strategy
```json
{
  "llm_integration": {
    "enabled": true,
    "provider_selection": "auto",  // auto, round_robin, preference
    "fallback_enabled": true,
    "provider_preference": ["openai", "anthropic", "ollama"],
    "providers": {
      "openai": {
        "enabled": true,
        "model": "gpt-4",
        "temperature": 0.1,
        "max_tokens": 4000,
        "use_for": ["generation", "fixing", "refactoring"]
      },
      "ollama": {
        "enabled": true,
        "model": "codellama:13b",
        "use_for": ["simple_fixes", "documentation"]
      }
    }
  }
}
```

### Context Configuration
```json
{
  "llm_integration": {
    "context_settings": {
      "include_recent_errors": true,
      "include_todo_tasks": true,
      "include_file_history": true,
      "include_dependencies": true,
      "max_context_files": 5,
      "context_window_size": 8000
    }
  }
}
```

### Quality Control
```json
{
  "llm_integration": {
    "quality_control": {
      "max_iterations": 3,
      "min_quality_score": 85,
      "require_tests": false,
      "require_documentation": true,
      "auto_format": true
    }
  }
}
```

## 📊 LLM Performance Comparison

### Code Generation Quality Test
**Task:** "Create a user authentication system with proper error handling"

| Provider | Model | Time | Quality Score | Iterations | Cost |
|----------|-------|------|---------------|------------|------|
| OpenAI | GPT-4 | 8s | 94/100 | 1.2 avg | $0.12 |
| OpenAI | GPT-3.5-turbo | 3s | 87/100 | 1.8 avg | $0.02 |
| Anthropic | Claude-3-sonnet | 12s | 92/100 | 1.4 avg | $0.08 |
| Ollama | CodeLlama-13B | 25s | 89/100 | 2.1 avg | Free |
| Ollama | CodeLlama-7B | 15s | 83/100 | 2.4 avg | Free |

### Recommendations by Use Case

**Production Applications:**
- Primary: OpenAI GPT-4
- Fallback: Anthropic Claude-3-sonnet

**Development & Learning:**
- Primary: Ollama CodeLlama-13B
- Fallback: OpenAI GPT-3.5-turbo

**Enterprise (Privacy-focused):**
- Primary: Ollama Phind-CodeLlama-34B
- Fallback: Self-hosted models

**Cost-sensitive:**
- Primary: Ollama CodeLlama-7B
- Fallback: OpenAI GPT-3.5-turbo

## 🔧 Troubleshooting

### Common Issues

#### 1. API Key Not Working
```bash
# Test API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models

# Check environment variable
echo $OPENAI_API_KEY

# Reset and retry
unset OPENAI_API_KEY
export OPENAI_API_KEY="sk-new-key..."
```

#### 2. Rate Limiting
```bash
# Configure rate limiting
gollm config set llm_integration.rate_limiting.requests_per_minute 20
gollm config set llm_integration.rate_limiting.retry_delay_seconds 5
```

#### 3. Context Too Large
```bash
# Reduce context size
gollm config set llm_integration.context_settings.max_context_files 3
gollm config set llm_integration.context_settings.context_window_size 4000
```

#### 4. Poor Code Quality
```bash
# Increase iterations
gollm config set llm_integration.quality_control.max_iterations 5

# Raise quality threshold
gollm config set llm_integration.quality_control.min_quality_score 90

# Use better model
gollm config set llm_integration.providers.openai.model gpt-4
```

### Debug Mode
```bash
# Enable debug logging
gollm config set debug.enabled true
gollm config set debug.save_llm_conversations true

# Check debug logs
tail -f .gollm/logs/llm_debug.log
```

## 🎯 Best Practices

### 1. Prompt Engineering
```bash
# Be specific about requirements
gollm generate "Create a REST API endpoint for user registration with email validation, password hashing, and proper error responses"

# Include context
gollm generate "Add payment processing to our existing e-commerce system, following the patterns in src/orders/"

# Specify constraints
gollm generate "Create a data validation function under 30 lines with comprehensive docstring"
```

### 2. Iterative Development
```bash
# Start simple
gollm generate "Create basic user model"

# Add features incrementally  
gollm generate "Add authentication methods to existing User class"
gollm generate "Add password reset functionality to User class"
```

### 3. Quality Assurance
```bash
# Always validate generated code
gollm validate generated_file.py

# Review before committing
gollm status
git diff

# Test generated code
python -m pytest tests/test_generated_code.py
```

### 4. Cost Management
```bash
# Use cheaper models for simple tasks
gollm config set llm_integration.providers.openai.model gpt-3.5-turbo

# Monitor usage
gollm stats --llm --period month

# Set usage limits
gollm config set llm_integration.usage_limits.monthly_tokens 100000
```

## 🔐 Security & Privacy

### Data Privacy
- **Local models (Ollama):** Code never leaves your machine
- **API providers:** Code sent to external servers
- **Recommendations:** Use local models for sensitive code

### API Key Security
```bash
# Use environment variables (not config files)
export OPENAI_API_KEY="sk-..."

# Rotate keys regularly
# Monitor usage in provider dashboards
# Use restricted API keys when possible
```

### Code Review
```bash
# Always review LLM-generated code
gollm generate "create user auth" --review

# Check for security issues
gollm validate --security-scan generated_code.py

# Run security linters
bandit generated_code.py
safety check
```

## 📈 Performance Optimization

### Model Selection
```bash
# Fast development
gollm config set llm_integration.providers.openai.model gpt-3.5-turbo

# High quality production
gollm config set llm_integration.providers.openai.model gpt-4

# Local privacy
gollm config set llm_integration.providers.ollama.model codellama:13b
```

### Caching
```json
{
  "llm_integration": {
    "caching": {
      "enabled": true,
      "cache_duration_hours": 24,
      "cache_similar_requests": true,
      "similarity_threshold": 0.85
    }
  }
}
```

### Parallel Processing
```json
{
  "llm_integration": {
    "parallel_processing": {
      "enabled": true,
      "max_concurrent_requests": 3,
      "batch_similar_requests": true
    }
  }
}
```

---

For more advanced LLM integration examples, see [examples/llm/](../examples/llm/) directory.



# docs/configuration.md
# goLLM Configuration Guide

## 📋 Overview

goLLM uses a `gollm.json` file for configuration. This guide covers all available settings and how to customize them for your project.

## 🔧 Basic Configuration

### Default Configuration
```json
{
  "version": "0.2.0",
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
  },
  "project_management": {
    "todo_integration": true,
    "auto_create_tasks": true,
    "todo_file": "TODO.md",
    "changelog_integration": true,
    "auto_update_changelog": true,
    "changelog_file": "CHANGELOG.md"
  },
  "llm_integration": {
    "enabled": false,
    "providers": {
      "openai": {
        "enabled": false,
        "model": "gpt-4"
      },
      "ollama": {
        "enabled": false,
        "model": "codellama:7b"
      }
    }
  }
}
```

## 📏 Validation Rules

### Code Structure Rules

#### `max_function_lines` (default: 50)
Maximum allowed lines in a single function.
```json
"max_function_lines": 30  // Stricter limit
```

#### `max_file_lines` (default: 300)
Maximum allowed lines in a single file.
```json
"max_file_lines": 500  // More permissive
```

#### `max_function_params` (default: 5)
Maximum number of parameters in a function.
```json
"max_function_params": 3  // Encourage simpler interfaces
```

### Complexity Rules

#### `max_cyclomatic_complexity` (default: 10)
Maximum cyclomatic complexity for functions.
```json
"max_cyclomatic_complexity": 8  // Lower complexity
```

#### `max_line_length` (default: 88)
Maximum line length (follows Black formatter).
```json
"max_line_length": 120  // Wider lines
```

### Code Quality Rules

#### `forbid_print_statements` (default: true)
Prohibit print() statements in code.
```json
"forbid_print_statements": false  // Allow prints for debugging
```

#### `forbid_global_variables` (default: true)
Prohibit global variable usage.
```json
"forbid_global_variables": false  // Allow globals
```

#### `require_docstrings` (default: true)
Require docstrings for all functions.
```json
"require_docstrings": false  // Make docstrings optional
```

#### `require_type_hints` (default: false)
Require type hints for function parameters and returns.
```json
"require_type_hints": true  // Enforce type hints
```

#### `naming_convention` (default: "snake_case")
Enforce naming convention.
```json
"naming_convention": "camelCase"  // Alternative: "PascalCase"
```

## 📋 Project Management

### TODO Integration

#### `todo_integration` (default: true)
Enable automatic TODO management.
```json
"todo_integration": false  // Disable TODO features
```

#### `auto_create_tasks` (default: true)
Automatically create TODO tasks from violations.
```json
"auto_create_tasks": false  // Manual task creation only
```

#### `todo_file` (default: "TODO.md")
Path to TODO file.
```json
"todo_file": "docs/tasks.md"  // Custom location
```

### CHANGELOG Integration

#### `changelog_integration` (default: true)
Enable automatic CHANGELOG updates.
```json
"changelog_integration": false  // Disable CHANGELOG
```

#### `auto_update_changelog` (default: true)
Automatically update CHANGELOG on changes.
```json
"auto_update_changelog": false  // Manual updates only
```

#### `changelog_file` (default: "CHANGELOG.md")
Path to CHANGELOG file.
```json
"changelog_file": "docs/HISTORY.md"  // Custom location
```

### Priority Mapping
```json
"priority_mapping": {
  "critical": "🔴 URGENT",
  "major": "🟡 HIGH", 
  "minor": "🟢 NORMAL"
}
```

## 🤖 LLM Integration

### Basic LLM Settings

#### `enabled` (default: false)
Enable LLM integration.
```json
"enabled": true
```

#### `max_iterations` (default: 3)
Maximum LLM improvement iterations.
```json
"max_iterations": 5  // More thorough refinement
```

#### `token_limit` (default: 4000)
Maximum tokens per LLM request.
```json
"token_limit": 8000  // Longer responses
```

### Provider Configuration

#### OpenAI Provider
```json
"providers": {
  "openai": {
    "enabled": true,
    "model": "gpt-4",
    "api_key_env": "OPENAI_API_KEY",
    "temperature": 0.1,
    "max_tokens": 4000
  }
}
```

#### Anthropic Provider
```json
"providers": {
  "anthropic": {
    "enabled": true,
    "model": "claude-3-sonnet-20240229",
    "api_key_env": "ANTHROPIC_API_KEY",
    "temperature": 0.1,
    "max_tokens": 4000
  }
}
```

#### Ollama Provider (Local)
```json
"providers": {
  "ollama": {
    "enabled": true,
    "base_url": "http://localhost:11434",
    "model": "codellama:7b",
    "timeout": 60,
    "temperature": 0.1
  }
}
```

## 🛡️ Enforcement Settings

### `block_save` (default: false)
Block file saving when violations exist.
```json
"enforcement": {
  "block_save": true  // Prevent saving bad code
}
```

### `block_execution` (default: false)
Block code execution when violations exist.
```json
"enforcement": {
  "block_execution": true  // Prevent running bad code
}
```

### `auto_fix_enabled` (default: true)
Enable automatic fixing of violations.
```json
"enforcement": {
  "auto_fix_enabled": false  // Manual fixes only
}
```

### `real_time_validation` (default: true)
Enable real-time validation during editing.
```json
"enforcement": {
  "real_time_validation": false  // Validate on save only
}
```

## 🔔 Notifications

### `show_violations` (default: true)
Show violation notifications.
```json
"notifications": {
  "show_violations": false  // Quiet mode
}
```

### `suggest_refactoring` (default: true)
Show refactoring suggestions.
```json
"notifications": {
  "suggest_refactoring": false  // No refactoring hints
}
```

### `desktop_notifications` (default: false)
Enable desktop notifications.
```json
"notifications": {
  "desktop_notifications": true  // Show system notifications
}
```

## 🔗 Git Integration

### `pre_commit_validation` (default: true)
Validate code before commits.
```json
"git_integration": {
  "pre_commit_validation": false  // Skip pre-commit checks
}
```

### `post_commit_updates` (default: true)
Update documentation after commits.
```json
"git_integration": {
  "post_commit_updates": false  // Manual doc updates
}
```

### `auto_commit_fixes` (default: false)
Automatically commit auto-fixes.
```json
"git_integration": {
  "auto_commit_fixes": true  // Auto-commit improvements
}
```

## 🎯 Team Configurations

### Strict Team Setup
```json
{
  "validation_rules": {
    "max_function_lines": 25,
    "max_file_lines": 200,
    "max_cyclomatic_complexity": 5,
    "max_function_params": 3,
    "require_docstrings": true,
    "require_type_hints": true,
    "forbid_print_statements": true
  },
  "enforcement": {
    "block_save": true,
    "block_execution": true,
    "real_time_validation": true
  }
}
```

### Permissive Setup
```json
{
  "validation_rules": {
    "max_function_lines": 100,
    "max_file_lines": 1000,
    "max_cyclomatic_complexity": 15,
    "forbid_print_statements": false,
    "require_docstrings": false
  },
  "enforcement": {
    "block_save": false,
    "block_execution": false,
    "auto_fix_enabled": true
  }
}
```

### Learning/Educational Setup
```json
{
  "validation_rules": {
    "max_function_lines": 30,
    "require_docstrings": true,
    "forbid_print_statements": false
  },
  "notifications": {
    "suggest_refactoring": true,
    "desktop_notifications": true
  },
  "llm_integration": {
    "enabled": true,
    "max_iterations": 2
  }
}
```

## 🔧 Configuration Management

### Environment-specific Configs
```bash
# Development
cp gollm.dev.json gollm.json

# Production  
cp gollm.prod.json gollm.json

# Testing
cp gollm.test.json gollm.json
```

### Using CLI for Configuration
```bash
# View current config
gollm config show

# Set individual values
gollm config set validation_rules.max_function_lines 40
gollm config set llm_integration.enabled true

# Reset to defaults
gollm config reset

# Validate configuration
gollm config validate
```

### Configuration Inheritance
```json
{
  "extends": "./team-base.json",
  "validation_rules": {
    "max_function_lines": 60  // Override team default
  }
}
```

## 🔄 Migration Between Versions

### Automatic Migration
```bash
# Migrate configuration to latest version
gollm config migrate --to-version 0.2.0

# Backup created automatically as gollm.json.backup
```

### Manual Migration
```bash
# Check configuration compatibility
gollm config check-compatibility

# Show migration recommendations
gollm config migration-guide
```

## 🎛️ Advanced Configuration

### Custom Validation Rules
```json
{
  "custom_rules": {
    "max_nested_loops": 2,
    "max_try_except_blocks": 3,
    "forbid_specific_imports": ["os.system", "eval", "exec"]
  }
}
```

### Integration with External Tools
```json
{
  "external_integrations": {
    "black": {
      "enabled": true,
      "line_length": 88
    },
    "flake8": {
      "enabled": true,
      "max_line_length": 88,
      "ignore": ["E203", "W503"]
    },
    "mypy": {
      "enabled": true,
      "strict": true
    }
  }
}
```

### Performance Settings
```json
{
  "performance": {
    "parallel_validation": true,
    "max_workers": 4,
    "cache_validation_results": true,
    "cache_duration_minutes": 30
  }
}
```

## 📊 Monitoring and Reporting

### Quality Metrics
```json
{
  "metrics": {
    "track_quality_trends": true,
    "quality_threshold": 80,
    "generate_reports": true,
    "report_frequency": "weekly"
  }
}
```

### Logging Configuration
```json
{
  "logging": {
    "level": "INFO",
    "file": ".gollm/logs/gollm.log",
    "max_size_mb": 10,
    "backup_count": 5
  }
}
```

## 🚨 Troubleshooting Configuration

### Common Issues

**Configuration not loading:**
```bash
# Check file syntax
gollm config validate

# Reset to defaults
gollm config reset
```

**LLM not working:**
```bash
# Test LLM connection
gollm config test-llm

# Check API keys
echo $OPENAI_API_KEY
```

**Git hooks not triggering:**
```bash
# Reinstall hooks
gollm install-hooks

# Check permissions
ls -la .git/hooks/
```

### Debug Mode
```json
{
  "debug": {
    "enabled": true,
    "verbose_logging": true,
    "save_llm_conversations": true
  }
}
```

---

For more examples and team setups, see [examples/configurations/](../examples/configurations/) directory.

# docs/llm_integration.md
# goLLM LLM Integration Guide

## 🎯 Overview

goLLM integrates with Large Language Models to provide intelligent code generation, automatic fixes, and context-aware suggestions. This guide covers setup, usage, and best practices.

## 🔌 Supported LLM Providers

### 1. OpenAI (GPT Models)
- **Models:** GPT-4, GPT-3.5-turbo, GPT-4-turbo
- **Strengths:** High quality, fast responses
- **Cost:** Pay-per-token
- **Best for:** Production environments, complex code generation

### 2. Anthropic (Claude Models)  
- **Models:** Claude-3-sonnet, Claude-3-haiku, Claude-3-opus
- **Strengths:** Long context, careful reasoning
- **Cost:** Pay-per-token
- **Best for:** Complex refactoring, documentation

### 3. Ollama (Local Models)
- **Models:** CodeLlama, Phind-CodeLlama, WizardCoder, StarCoder
- **Strengths:** Privacy, no API costs, offline usage
- **Cost:** Free (hardware requirements)
- **Best for:** Privacy-sensitive projects, development

## ⚙️ Setup Guide

### OpenAI Setup
```bash
# 1. Get API key from platform.openai.com
export OPENAI_API_KEY="sk-..."

# 2. Enable in goLLM
gollm config set llm_integration.enabled true
gollm config set llm_integration.providers.openai.enabled true
gollm config set llm_integration.providers.openai.model gpt-4

# 3. Test connection
gollm generate "Create a hello world function"
```

### Anthropic Setup
```bash
# 1. Get API key from console.anthropic.com
export ANTHROPIC_API_KEY="sk-ant-..."

# 2. Enable in goLLM
gollm config set llm_integration.enabled true
gollm config set llm_integration.providers.anthropic.enabled true
gollm config set llm_integration.providers.anthropic.model claude-3-sonnet-20240229

# 3. Test connection
gollm generate "Create a data validation class"
```

### Ollama Setup (Detailed in ollama_setup.md)
```bash
# 1. Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Pull model
ollama pull codellama:7b

# 3. Configure goLLM
gollm config set llm_integration.enabled true
gollm config set llm_integration.providers.ollama.enabled true
gollm config set llm_integration.providers.ollama.model codellama:7b
```

## 🚀 Usage Examples

### Basic Code Generation
```bash
# Simple function
gollm generate "Create a function to validate email addresses"

# Class with methods
gollm generate "Create a User class with authentication methods"

# Complex logic
gollm generate "Create a payment processor that handles multiple payment methods"
```

### Context-Aware Generation
goLLM automatically provides rich context to the LLM:

```bash
# LLM receives:
# - Your project's quality rules (max 50 lines, no prints, etc.)
# - Recent errors and issues
# - Current TODO tasks
# - Code style standards
# - File structure and dependencies

gollm generate "Create a user registration system"
```

### Auto-fixing Existing Code
```bash
# Fix specific file
gollm fix --llm src/problematic_file.py

# Fix all violations
gollm fix --auto --llm

# Interactive fixing
gollm fix --interactive
```

### Iterative Improvement
```bash
# goLLM automatically iterates with LLM until quality standards are met:

$ gollm generate "Create a data processor"

🤖 LLM Generation (Attempt 1)...
❌ Validation failed: 3 violations found
   - Function too long (75 lines, max: 50)  
   - Too many parameters (8, max: 5)
   - Missing docstring

🔄 Sending feedback to LLM...

🤖 LLM Generation (Attempt 2)...
❌ Validation failed: 1 violation found
   - Complexity too high (12, max: 10)

🔄 Sending feedback to LLM...

🤖 LLM Generation (Attempt 3)...
✅ All validations passed!
📝 TODO updated: 0 new tasks
📝 CHANGELOG updated: Code generation entry
💾 Code saved: data_processor.py
```

## 🎛️ Advanced Configuration

### Provider Selection Strategy
```json
{
  "llm_integration": {
    "enabled": true,
    "provider_selection": "auto",  // auto, round_robin, preference
    "fallback_enabled": true,
    "provider_preference": ["openai", "anthropic", "ollama"],
    "providers": {
      "openai": {
        "enabled": true,
        "model": "gpt-4",
        "temperature": 0.1,
        "max_tokens": 4000,
        "use_for": ["generation", "fixing", "refactoring"]
      },
      "ollama": {
        "enabled": true,
        "model": "codellama:13b",
        "use_for": ["simple_fixes", "documentation"]
      }
    }
  }
}
```

### Context Configuration
```json
{
  "llm_integration": {
    "context_settings": {
      "include_recent_errors": true,
      "include_todo_tasks": true,
      "include_file_history": true,
      "include_dependencies": true,
      "max_context_files": 5,
      "context_window_size": 8000
    }
  }
}
```

### Quality Control
```json
{
  "llm_integration": {
    "quality_control": {
      "max_iterations": 3,
      "min_quality_score": 85,
      "require_tests": false,
      "require_documentation": true,
      "auto_format": true
    }
  }
}
```

## 📊 LLM Performance Comparison

### Code Generation Quality Test
**Task:** "Create a user authentication system with proper error handling"

| Provider | Model | Time | Quality Score | Iterations | Cost |
|----------|-------|------|---------------|------------|------|
| OpenAI | GPT-4 | 8s | 94/100 | 1.2 avg | $0.12 |
| OpenAI | GPT-3.5-turbo | 3s | 87/100 | 1.8 avg | $0.02 |
| Anthropic | Claude-3-sonnet | 12s | 92/100 | 1.4 avg | $0.08 |
| Ollama | CodeLlama-13B | 25s | 89/100 | 2.1 avg | Free |
| Ollama | CodeLlama-7B | 15s | 83/100 | 2.4 avg | Free |

### Recommendations by Use Case

**Production Applications:**
- Primary: OpenAI GPT-4
- Fallback: Anthropic Claude-3-sonnet

**Development & Learning:**
- Primary: Ollama CodeLlama-13B
- Fallback: OpenAI GPT-3.5-turbo

**Enterprise (Privacy-focused):**
- Primary: Ollama Phind-CodeLlama-34B
- Fallback: Self-hosted models

**Cost-sensitive:**
- Primary: Ollama CodeLlama-7B
- Fallback: OpenAI GPT-3.5-turbo

## 🔧 Troubleshooting

### Common Issues

#### 1. API Key Not Working
```bash
# Test API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models

# Check environment variable
echo $OPENAI_API_KEY

# Reset and retry
unset OPENAI_API_KEY
export OPENAI_API_KEY="sk-new-key..."
```

#### 2. Rate Limiting
```bash
# Configure rate limiting
gollm config set llm_integration.rate_limiting.requests_per_minute 20
gollm config set llm_integration.rate_limiting.retry_delay_seconds 5
```

#### 3. Context Too Large
```bash
# Reduce context size
gollm config set llm_integration.context_settings.max_context_files 3
gollm config set llm_integration.context_settings.context_window_size 4000
```

#### 4. Poor Code Quality
```bash
# Increase iterations
gollm config set llm_integration.quality_control.max_iterations 5

# Raise quality threshold
gollm config set llm_integration.quality_control.min_quality_score 90

# Use better model
gollm config set llm_integration.providers.openai.model gpt-4
```

### Debug Mode
```bash
# Enable debug logging
gollm config set debug.enabled true
gollm config set debug.save_llm_conversations true

# Check debug logs
tail -f .gollm/logs/llm_debug.log
```

## 🎯 Best Practices

### 1. Prompt Engineering
```bash
# Be specific about requirements
gollm generate "Create a REST API endpoint for user registration with email validation, password hashing, and proper error responses"

# Include context
gollm generate "Add payment processing to our existing e-commerce system, following the patterns in src/orders/"

# Specify constraints
gollm generate "Create a data validation function under 30 lines with comprehensive docstring"
```

### 2. Iterative Development
```bash
# Start simple
gollm generate "Create basic user model"

# Add features incrementally  
gollm generate "Add authentication methods to existing User class"
gollm generate "Add password reset functionality to User class"
```

### 3. Quality Assurance
```bash
# Always validate generated code
gollm validate generated_file.py

# Review before committing
gollm status
git diff

# Test generated code
python -m pytest tests/test_generated_code.py
```

### 4. Cost Management
```bash
# Use cheaper models for simple tasks
gollm config set llm_integration.providers.openai.model gpt-3.5-turbo

# Monitor usage
gollm stats --llm --period month

# Set usage limits
gollm config set llm_integration.usage_limits.monthly_tokens 100000
```

## 🔐 Security & Privacy

### Data Privacy
- **Local models (Ollama):** Code never leaves your machine
- **API providers:** Code sent to external servers
- **Recommendations:** Use local models for sensitive code

### API Key Security
```bash
# Use environment variables (not config files)
export OPENAI_API_KEY="sk-..."

# Rotate keys regularly
# Monitor usage in provider dashboards
# Use restricted API keys when possible
```

### Code Review
```bash
# Always review LLM-generated code
gollm generate "create user auth" --review

# Check for security issues
gollm validate --security-scan generated_code.py

# Run security linters
bandit generated_code.py
safety check
```

## 📈 Performance Optimization

### Model Selection
```bash
# Fast development
gollm config set llm_integration.providers.openai.model gpt-3.5-turbo

# High quality production
gollm config set llm_integration.providers.openai.model gpt-4

# Local privacy
gollm config set llm_integration.providers.ollama.model codellama:13b
```

### Caching
```json
{
  "llm_integration": {
    "caching": {
      "enabled": true,
      "cache_duration_hours": 24,
      "cache_similar_requests": true,
      "similarity_threshold": 0.85
    }
  }
}
```

### Parallel Processing
```json
{
  "llm_integration": {
    "parallel_processing": {
      "enabled": true,
      "max_concurrent_requests": 3,
      "batch_similar_requests": true
    }
  }
}
```

---

For more advanced LLM integration examples, see [examples/llm/](../examples/llm/) directory.