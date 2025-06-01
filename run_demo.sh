#!/bin/bash
# run_demo.sh - goLLM Demo Script for Linux/macOS

echo "🚀 goLLM - Smart Python Quality Guardian Demo"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# Check if Python is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        echo "Please install Python 3.8+ from https://python.org"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_success "Python $PYTHON_VERSION found"
}

# Setup virtual environment
setup_venv() {
    print_step "📦 Setting up virtual environment..."
    
    if [ ! -d "venv" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    print_info "Activating virtual environment..."
    source venv/bin/activate
    
    print_info "Upgrading pip..."
    pip install --upgrade pip > /dev/null 2>&1
    
    print_success "Virtual environment ready"
}

# Install goLLM
install_gollm() {
    print_step "⬇️  Installing goLLM..."
    
    pip install -e . > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        print_success "goLLM installed successfully"
    else
        print_error "goLLM installation failed"
        exit 1
    fi
}

# Run demo validation
run_validation_demo() {
    print_step "🔍 goLLM Validation Demo"
    echo "========================================"
    echo ""
    
    print_info "Validating BAD code example (examples/bad_code.py)..."
    echo ""
    
    # Run validation on bad code
    python -m gollm validate examples/bad_code.py
    
    echo ""
    print_info "Validating GOOD code example (examples/good_code.py)..."
    echo ""
    
    # Run validation on good code  
    python -m gollm validate examples/good_code.py
    
    echo ""
    print_success "Validation demo completed"
}

# Show project status
show_project_status() {
    print_step "📊 Project Status Overview"
    echo "========================================"
    echo ""
    
    python -m gollm status
    
    echo ""
    print_success "Status overview completed"
}

# Show next TODO task
show_next_task() {
    print_step "📋 Next TODO Task"
    echo "========================================"
    echo ""
    
    python -m gollm next-task
    
    echo ""
    print_success "TODO task display completed"
}

# Demo LLM integration (if available)
demo_llm_integration() {
    print_step "🤖 LLM Integration Demo"
    echo "========================================"
    echo ""
    
    # Check if any LLM provider is configured
    LLM_ENABLED=$(python -c "
from gollm.config.config import GollmConfig
try:
    config = GollmConfig.load('examples/gollm.json')
    print('true' if config.llm_integration.enabled else 'false')
except:
    print('false')
" 2>/dev/null)
    
    if [ "$LLM_ENABLED" = "true" ]; then
        print_info "LLM integration is enabled, testing code generation..."
        echo ""
        
        # Try to generate simple code
        python -m gollm generate "Create a simple hello world function" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            print_success "LLM code generation demo completed"
        else
            print_warning "LLM generation failed (this is normal if no LLM provider is configured)"
        fi
    else
        print_info "LLM integration is disabled in demo config"
        print_info "To enable LLM features:"
        echo ""
        echo "  For Ollama (local, free):"
        echo "    1. Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh"
        echo "    2. Pull model: ollama pull codellama:7b"
        echo "    3. Enable: gollm config set llm_integration.enabled true"
        echo ""
        echo "  For OpenAI:"
        echo "    1. Get API key from platform.openai.com"
        echo "    2. Set key: export OPENAI_API_KEY='sk-...'"
        echo "    3. Enable: gollm config set llm_integration.providers.openai.enabled true"
    fi
    
    echo ""
}

# Show configuration
show_configuration() {
    print_step "⚙️  goLLM Configuration"
    echo "========================================"
    echo ""
    
    print_info "Current configuration (examples/gollm.json):"
    echo ""
    
    if [ -f "examples/gollm.json" ]; then
        cat examples/gollm.json | python -m json.tool 2>/dev/null || cat examples/gollm.json
    else
        print_warning "Configuration file not found"
    fi
    
    echo ""
    print_success "Configuration display completed"
}

# Demo file watching (background process)
demo_file_watching() {
    print_step "👁️  Real-time File Monitoring Demo"
    echo "========================================"
    echo ""
    
    print_info "goLLM can monitor files in real-time and validate changes automatically"
    print_info "This would normally run in the background integrated with your IDE"
    echo ""
    
    # Create a temporary file with bad code
    TEMP_FILE="demo_temp_file.py"
    
    cat > $TEMP_FILE << 'EOF'
def bad_function(a, b, c, d, e, f):  # Too many parameters
    print("This is bad code")  # Print statement forbidden
    return a + b + c + d + e + f
EOF
    
    print_info "Created temporary file with violations: $TEMP_FILE"
    echo ""
    
    print_info "Validating the temporary file..."
    python -m gollm validate $TEMP_FILE
    
    echo ""
    print_info "Cleaning up temporary file..."
    rm -f $TEMP_FILE
    
    print_success "File monitoring demo completed"
}

# Show help and next steps
show_next_steps() {
    print_step "🎓 Next Steps & Quick Reference"
    echo "========================================"
    echo ""
    
    print_info "Essential Commands:"
    echo ""
    echo "  📊 Project Management:"
    echo "    gollm status              # Show project quality status"
    echo "    gollm validate-project    # Validate entire project"
    echo "    gollm next-task          # Get next TODO task"
    echo ""
    echo "  🔧 Code Quality:"
    echo "    gollm validate <file>     # Validate specific file"
    echo "    gollm fix --auto         # Auto-fix violations"
    echo ""
    echo "  🤖 LLM Integration:"
    echo "    gollm generate \"prompt\"   # Generate code with AI"
    echo "    gollm fix --llm <file>   # Fix code with AI assistance"
    echo ""
    echo "  ⚙️  Configuration:"
    echo "    gollm config show        # Show current config"
    echo "    gollm config set key val # Set configuration value"
    echo "    gollm init              # Initialize goLLM in project"
    echo ""
    echo "  🔗 Integration:"
    echo "    gollm install-hooks      # Install Git hooks"
    echo "    gollm setup-ide --editor=vscode  # Setup IDE integration"
    echo ""
    
    print_info "Documentation:"
    echo "    📚 docs/getting_started.md   # Getting started guide"
    echo "    🔧 docs/configuration.md     # Configuration reference"
    echo "    🤖 docs/llm_integration.md   # LLM setup and usage"
    echo "    🦙 docs/ollama_setup.md      # Local LLM with Ollama"
    echo "    📖 docs/api_reference.md     # Complete API reference"
    echo ""
    
    print_info "Example Workflows:"
    echo ""
    echo "  🚀 Daily Development:"
    echo "    1. gollm status           # Check what needs attention"
    echo "    2. gollm next-task        # Work on priority items"
    echo "    3. gollm validate <file>  # Validate as you code"
    echo "    4. gollm fix --auto       # Fix simple issues"
    echo ""
    echo "  🤖 With LLM (after setup):"
    echo "    1. gollm generate \"create user auth class\""
    echo "    2. # goLLM automatically validates and improves code"
    echo "    3. # TODO and CHANGELOG updated automatically"
    echo ""
    echo "  📝 Project Setup:"
    echo "    1. cd your_project"
    echo "    2. gollm init             # Create gollm.json config"
    echo "    3. gollm install-hooks    # Install Git validation"
    echo "    4. gollm setup-ide        # Configure your editor"
    echo ""
}

# Main demo execution
main() {
    clear
    
    print_step "🧪 goLLM Demo Starting..."
    echo ""
    
    # Pre-flight checks
    check_python
    
    # Setup environment
    setup_venv
    install_gollm
    
    echo ""
    print_step "🎯 Running goLLM Demos..."
    echo ""
    
    # Run all demo sections
    run_validation_demo
    echo ""
    
    show_project_status
    echo ""
    
    show_next_task
    echo ""
    
    demo_llm_integration
    echo ""
    
    show_configuration
    echo ""
    
    demo_file_watching
    echo ""
    
    show_next_steps
    
    echo ""
    print_step "🎉 goLLM Demo Completed Successfully!"
    echo ""
    print_success "goLLM is now ready to improve your code quality!"
    print_info "To start using goLLM in your projects, run: gollm init"
    echo ""
}

# Run main function
main

