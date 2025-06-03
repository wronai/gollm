# Getting Started with goLLM

## Prerequisites

- Python 3.8 or higher
- pip (latest version)
- Ollama (optional, for local LLM models)

## Installation

### Using pip

#### Basic Installation
```bash
pip install gollm
```

#### With LLM Support (Recommended)
```bash
pip install gollm[llm]
```

### For Developers

```bash
# Clone the repository
git clone https://github.com/wronai/gollm.git
cd gollm

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install in development mode
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install
```

## Quick Start

1. **Initialize your project**
   ```bash
   # Navigate to your project
   cd your_project
   
   # Initialize configuration (creates gollm.json)
   gollm init
   ```

2. **Validate your code**
   ```bash
   # Check a single file
   gollm validate file.py
   
   # Check entire project
   gollm validate-project
   
   # Check project status
   gollm status
   ```

3. **Generate code with LLM**
   ```bash
   # Standard generation with validation
   gollm generate "Create a user class"
   
   # Fast generation (no validation)
   gollm generate "Create a user class" --fast
   ```

## Next Steps

- Learn about [Features](/features/overview.md)
- Explore [Usage Examples](/features/usage.md)
- Check out [API Reference](/api/reference.md)
