# goLLM - Getting Started Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Git (optional but recommended)
- Text editor or IDE

### Installation

#### Option 1: Quick Install (Recommended)
```bash
curl -sSL https://raw.githubusercontent.com/wronai/gollm/main/install.sh | bash
```

#### Option 2: Manual Installation
```bash
# Clone the repository
git clone https://github.com/wronai/gollm
cd gollm

# Run installation script
./install.sh

# Or install manually
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

### First Steps

1. **Initialize goLLM in your project:**
```bash
cd your_python_project
gollm init
```

2. **Run your first validation:**
```bash
gollm validate-project
```

3. **Check project status:**
```bash
gollm status
```

## 📝 Basic Configuration

goLLM creates a `gollm.json` configuration file in your project root:

```json
{
  "validation_rules": {
    "max_function_lines": 50,
    "max_file_lines": 300,
    "forbid_print_statements": true,
    "require_docstrings": true
  },
  "llm_integration": {
    "enabled": false
  }
}
```

## 🎯 Common Workflows

### Daily Development
```bash
# Check what needs attention
gollm status

# Work on next priority task
gollm next-task

# Validate as you code
gollm validate src/myfile.py

# Auto-fix simple issues
gollm fix --auto
```

### Before Commits
```bash
# Full project validation
gollm validate-project

# Fix any issues
gollm fix --auto

# Check final status
gollm status
```

### With Git Integration
```bash
# Install Git hooks (one-time setup)
gollm install-hooks

# Now validation happens automatically on commit
git add .
git commit -m "feature: new functionality"
# goLLM validates automatically
```

## 🤖 LLM Integration Setup

### OpenAI Setup
```bash
# Set API key
export OPENAI_API_KEY="sk-..."

# Enable in config
gollm config set llm_integration.enabled true
gollm config set llm_integration.providers.openai.enabled true
```

### Ollama Setup (Local LLM)
```bash
# Install Ollama (see ollama.ai)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a code model
ollama pull codellama:7b

# Configure goLLM
gollm config set llm_integration.enabled true
gollm config set llm_integration.providers.ollama.enabled true
gollm config set llm_integration.providers.ollama.model codellama:7b
```

### Generate Code with LLM
```bash
# Generate code with AI assistance
gollm generate "Create a user authentication class"

# goLLM will:
# 1. Send request to LLM with project context
# 2. Validate generated code
# 3. Iterate until quality standards are met
# 4. Update TODO and CHANGELOG automatically
```

## 🛠️ IDE Integration

### VS Code
```bash
# Setup VS Code integration
gollm setup-ide --editor=vscode

# This configures:
# - Real-time validation
# - Auto-fix on save
# - goLLM tasks and shortcuts
# - Code actions and quick fixes
```

### Manual IDE Setup
Add these to your IDE settings:
- **Linter:** Use `gollm validate` as custom linter
- **Formatter:** Use `gollm fix --auto` as formatter
- **Build task:** `gollm validate-project`

## 📊 Understanding Output

### Validation Results
```bash
❌ Found 3 violations in user_processor.py:
  - function_too_long: Function 'process_data' has 55 lines (max: 50)
  - too_many_parameters: Function has 7 parameters (max: 5)  
  - missing_docstring: Function 'process_data' missing docstring
```

### Quality Scores
- **90-100:** Excellent - minimal issues
- **80-89:** Good - minor improvements needed
- **70-79:** Fair - moderate issues to address
- **Below 70:** Needs attention - significant issues

### TODO Management
goLLM automatically creates TODO entries for violations:
- **🔴 HIGH:** Critical issues (complexity, too many params)
- **🟡 MEDIUM:** Important improvements (print statements, naming)
- **🟢 LOW:** Nice-to-have (documentation, minor refactoring)

## 🔧 Troubleshooting

### Common Issues

**"Command not found: gollm"**
```bash
# Make sure you're in the virtual environment
source venv/bin/activate
# Or check if goLLM is installed
pip list | grep gollm
```

**"No module named gollm"**
```bash
# Install in development mode
pip install -e .
# Or check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

**"LLM not responding"**
```bash
# Check Ollama is running
ollama list
# Or verify API keys
echo $OPENAI_API_KEY
```

**"Git hooks not working"**
```bash
# Reinstall hooks
gollm install-hooks
# Check permissions
ls -la .git/hooks/pre-commit
```

### Getting Help
```bash
# Show all commands
gollm --help

# Command-specific help
gollm validate --help

# Show current configuration
gollm config show

# Debug mode
gollm validate-project --debug
```

## 📚 Next Steps

1. **Read the Configuration Guide:** Learn about all available settings
2. **Explore LLM Integration:** Set up AI-powered code generation
3. **Customize Rules:** Adapt goLLM to your team's standards
4. **Set up CI/CD:** Integrate with your build pipeline
5. **Team Setup:** Share configuration across your team

## 🎯 Best Practices

1. **Start Small:** Begin with basic validation, add features gradually
2. **Team Alignment:** Agree on quality standards before enforcing
3. **Gradual Enforcement:** Start with warnings, move to blocking saves
4. **Regular Reviews:** Check TODO and CHANGELOG regularly
5. **LLM Training:** Provide good prompts for better code generation

---

**Need help?** Check our [documentation](docs/) or open an issue on GitHub!
