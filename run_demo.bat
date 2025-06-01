# run_demo.bat - Windows version
@echo off
setlocal enabledelayedexpansion

echo 🚀 SPYQ - Smart Python Quality Guardian Demo
echo ==============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is required but not installed
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

REM Install SPYQ
echo ⬇️  Installing SPYQ...
pip install -e . >nul 2>&1

if errorlevel 1 (
    echo ❌ SPYQ installation failed
    pause
    exit /b 1
)

echo ✅ SPYQ installed successfully
echo.

echo 🎯 SPYQ Demo - Code Quality in Action
echo ======================================
echo.

echo 1️⃣  Validating BAD code example...
echo -----------------------------------
python -m spyq validate examples\bad_code.py
echo.

echo 2️⃣  Validating GOOD code example...
echo ------------------------------------
python -m spyq validate examples\good_code.py
echo.

echo 3️⃣  Project status overview...
echo ------------------------------
python -m spyq status
echo.

echo 4️⃣  Next TODO task...
echo --------------------
python -m spyq next-task
echo.

echo 5️⃣  Configuration display...
echo ---------------------------
if exist "examples\spyq.json" (
    type examples\spyq.json
) else (
    echo ⚠️  Configuration file not found
)
echo.

echo 6️⃣  LLM Integration Status...
echo ----------------------------
echo ℹ️  LLM integration is available but requires setup:
echo.
echo   For Ollama (local, free):
echo     1. Download from ollama.ai
echo     2. Install and run: ollama pull codellama:7b
echo     3. Enable: spyq config set llm_integration.enabled true
echo.
echo   For OpenAI:
echo     1. Get API key from platform.openai.com
echo     2. Set environment variable: set OPENAI_API_KEY=sk-...
echo     3. Enable: spyq config set llm_integration.providers.openai.enabled true
echo.

echo 🎉 Demo completed!
echo.
echo 💡 Essential Commands:
echo    spyq validate-project    # Validate entire project
echo    spyq status             # Show project status
echo    spyq next-task          # Get next TODO task
echo    spyq fix --auto         # Auto-fix violations
echo    spyq generate "prompt"  # Generate code with LLM (after setup)
echo    spyq --help             # Show all commands
echo.
echo 📚 Documentation:
echo    docs\getting_started.md   # Getting started guide
echo    docs\configuration.md     # Configuration reference  
echo    docs\llm_integration.md   # LLM setup and usage
echo    docs\ollama_setup.md      # Local LLM with Ollama
echo.
echo 🚀 To start using SPYQ in your projects:
echo    1. cd your_python_project
echo    2. spyq init
echo    3. spyq install-hooks
echo    4. spyq setup-ide --editor=vscode
echo.
echo Happy coding with SPYQ! 🐍✨

pause

# quick_test.sh - Quick functionality test
#!/bin/bash

echo "🧪 SPYQ Quick Test"
echo "=================="

# Test basic functionality
echo "Testing basic validation..."
python -m spyq validate examples/bad_code.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Validation command works"
else
    echo "❌ Validation command failed"
    exit 1
fi

# Test configuration loading
echo "Testing configuration..."
python -c "from spyq.config.config import SpyqConfig; SpyqConfig.load('examples/spyq.json')" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Configuration loading works"
else
    echo "❌ Configuration loading failed"
    exit 1
fi

# Test project status
echo "Testing project status..."
python -m spyq status > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Status command works"
else
    echo "❌ Status command failed"
    exit 1
fi

echo ""
echo "🎉 All basic tests passed!"
echo "SPYQ is ready to use!"

# demo_with_ollama.sh - Extended demo with Ollama
#!/bin/bash

echo "🤖 SPYQ + Ollama Integration Demo"
echo "=================================="

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama not found"
    echo ""
    echo "To install Ollama:"
    echo "  curl -fsSL https://ollama.ai/install.sh | sh"
    echo ""
    echo "Then run this demo again."
    exit 1
fi

echo "✅ Ollama found"

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "❌ Ollama service not running"
    echo ""
    echo "Please start Ollama:"
    echo "  ollama serve"
    echo ""
    echo "Then run this demo again."
    exit 1
fi

echo "✅ Ollama service running"

# Check for available models
echo "📋 Available Ollama models:"
ollama list

# Check for CodeLlama
if ollama list | grep -q "codellama"; then
    echo "✅ CodeLlama model found"
    
    # Configure SPYQ to use Ollama
    echo "⚙️  Configuring SPYQ for Ollama..."
    
    # Create temporary config with Ollama enabled
    cp examples/spyq.json spyq_ollama_demo.json
    
    # Enable LLM integration (would normally use spyq config commands)
    python -c "
import json
with open('spyq_ollama_demo.json', 'r') as f:
    config = json.load(f)
config['llm_integration']['enabled'] = True
config['llm_integration']['providers']['ollama']['enabled'] = True
with open('spyq_ollama_demo.json', 'w') as f:
    json.dump(config, f, indent=2)
"
    
    echo "🤖 Testing code generation with Ollama..."
    
    # Test code generation
    python -m spyq --config spyq_ollama_demo.json generate "Create a simple function to add two numbers with proper documentation"
    
    if [ $? -eq 0 ]; then
        echo "✅ Ollama code generation successful!"
    else
        echo "⚠️  Ollama code generation had issues (this is normal for first run)"
    fi
    
    # Cleanup
    rm -f spyq_ollama_demo.json
    
else
    echo "❌ No CodeLlama model found"
    echo ""
    echo "To install a model for code generation:"
    echo "  ollama pull codellama:7b        # 4GB RAM required"
    echo "  ollama pull codellama:13b       # 8GB RAM required"
    echo "  ollama pull phind-codellama:34b # 20GB RAM required"
    echo ""
    echo "Then run this demo again."
fi

echo ""
echo "🎉 Ollama demo completed!"