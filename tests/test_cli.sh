#!/bin/bash
# Test script for the improved Ollama adapter with code generation capabilities

echo "Testing improved Ollama adapter with code generation..."
echo "==================================================="

# Set environment variables to use the modular adapter
export GOLLM_ADAPTER_TYPE=modular
export GOLLM_LOG_LEVEL=DEBUG
# Set code generation flag
export GOLLM_CODE_GENERATION=true

# Test simple Hello World code generation
echo -e "\n\nTest 1: Simple Hello World in Python"
echo "----------------------------------------"
python -m gollm generate "Write a Python function that prints 'Hello, World!'" -o hello_world.py

# Test with a slightly more complex code generation task
echo -e "\n\nTest 2: Factorial function in Python"
echo "----------------------------------------"
python -m gollm generate "Write a Python function to calculate factorial recursively" -o factorial.py

# Test with a very short prompt (should use shorter timeout)
echo -e "\n\nTest 3: Very short prompt"
echo "----------------------------------------"
python -m gollm generate "Print hello world in Python" -o hello.py

echo -e "\n\nAll tests completed!"
echo "Generated files:"
ls -l hello_world.py factorial.py hello.py
