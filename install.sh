
#!/bin/bash

echo "🚀 goLLM Installation Script"
echo "==========================="

# Sprawdź wymagania systemowe
echo "🔍 Checking system requirements..."

# Python 3.8+
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    echo "📥 Please install Python 3.8+ from https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $PYTHON_VERSION found, but Python $REQUIRED_VERSION+ is required"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION found"

# pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed"
    echo "📥 Please install pip3"
    exit 1
fi

echo "✅ pip3 found"

# Git (opcjonalne ale zalecane)
if command -v git &> /dev/null; then
    echo "✅ Git found - Git hooks will be available"
    GIT_AVAILABLE=true
else
    echo "⚠️  Git not found - Git hooks will be skipped"
    GIT_AVAILABLE=false
fi

echo ""
echo "📦 Installing goLLM..."

# Utwórz wirtualne środowisko jeśli nie istnieje
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
fi

# Aktywuj wirtualne środowisko
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Zainstaluj goLLM
echo "📥 Installing goLLM package..."
pip install -e .

# Sprawdź instalację
echo "🧪 Testing installation..."
if python -c "import gollm; print('goLLM imported successfully')" 2>/dev/null; then
    echo "✅ goLLM installed successfully"
else
    echo "❌ goLLM installation failed"
    exit 1
fi

# Inicjalizuj projekt
echo ""
echo "🔧 Initializing goLLM for this project..."

# Utwórz domyślną konfigurację jeśli nie istnieje
if [ ! -f "gollm.json" ]; then
    echo "📝 Creating default configuration..."
    cat > gollm.json << 'EOF'
{
  "validation_rules": {
    "max_function_lines": 50,
    "max_file_lines": 300,
    "max_cyclomatic_complexity": 10,
    "forbid_print_statements": true,
    "forbid_global_variables": true,
    "require_docstrings": true,
    "max_function_params": 5,
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
    "model_name": "gpt-4",
    "max_iterations": 3,
    "token_limit": 4000
  },
  "enforcement": {
    "block_save": false,
    "block_execution": false,
    "auto_fix_enabled": true
  }
}
EOF
    echo "✅ Created gollm.json"
else
    echo "✅ gollm.json already exists"
fi

# Utwórz strukturę katalogów goLLM
echo "📁 Creating goLLM directory structure..."
mkdir -p .gollm/{cache,templates,hooks}
mkdir -p .gollm/cache/{execution_logs,validation_cache,llm_context}

# Utwórz szablony
cat > .gollm/templates/todo_template.md << 'EOF'
# TODO List - Updated: {timestamp}

## 🔴 HIGH Priority

## 🟡 MEDIUM Priority

## 🟢 LOW Priority

---
*This file is automatically managed by goLLM*
EOF

cat > .gollm/templates/changelog_template.md << 'EOF'
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
### Changed
### Fixed
### Removed

---
*This changelog is automatically maintained by goLLM*
EOF

echo "✅ goLLM structure created"

# Zainstaluj Git hooks jeśli Git jest dostępne
if [ "$GIT_AVAILABLE" = true ] && [ -d ".git" ]; then
    echo "🪝 Installing Git hooks..."
    python scripts/install_hooks.py
else
    echo "⚠️  Skipping Git hooks (no Git repository found)"
fi

# Konfiguracja IDE
echo ""
echo "🛠️  IDE Integration Setup"
echo "========================"

# VS Code
if [ -d ".vscode" ] || command -v code &> /dev/null; then
    echo "🔍 VS Code detected"
    read -p "Setup VS Code integration? (y/n): " setup_vscode
    if [[ $setup_vscode =~ ^[Yy]$ ]]; then
        python scripts/setup_ide.py vscode
    fi
fi

# Uruchom podstawowe testy
echo ""
echo "🧪 Running basic functionality tests..."
python test_basic_functionality.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 goLLM Installation Complete!"
    echo "=============================="
    echo ""
    echo "✅ goLLM is now installed and configured"
    echo "📁 Configuration: gollm.json"
    echo "📂 goLLM data: .gollm/"
    echo ""
    echo "🚀 Quick Start Commands:"
    echo "  gollm validate-project    # Validate entire project"
    echo "  gollm status             # Show project status"
    echo "  gollm next-task          # Get next TODO task"
    echo "  gollm --help             # Show all commands"
    echo ""
    echo "📚 Documentation: README.md"
    echo "⚙️  Configuration: docs/configuration.md"
    echo ""
    echo "💡 To enable LLM integration:"
    echo "   1. Set API key: export OPENAI_API_KEY='sk-...'"
    echo "   2. Enable in config: gollm config set llm_integration.enabled true"
    echo ""
    echo "Happy coding with goLLM! 🐍✨"
else
    echo ""
    echo "⚠️  Installation completed with some issues"
    echo "📋 Check the test output above for details"
    echo "🔧 You may need to fix configuration or dependencies"
fi
