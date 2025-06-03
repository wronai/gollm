#!/bin/bash
# Simple test script to check if code is generated and saved as a file

echo "Testing simple code generation with direct API call..."

# Create output directory
mkdir -p test_output

# Test with direct curl to Ollama API
echo "\n1. Testing with direct curl to Ollama API..."
CURL_OUTPUT=$(curl -s -X POST http://rock:8081/api/chat \
     -H 'Content-Type: application/json' \
     -d '{
       "model": "qwen3:4b",
       "messages": [ {"role": "user", "content": "Write a simple Python function to add two numbers"} ],
       "stream": false
     }')

# Save the curl output
echo "$CURL_OUTPUT" > test_output/curl_output.json
echo "Curl output saved to test_output/curl_output.json"

# Extract the content from the response
CONTENT=$(echo "$CURL_OUTPUT" | jq -r '.message.content')

# Save the content to a file
echo "$CONTENT" > test_output/direct_api_function.txt
echo "Content saved to test_output/direct_api_function.txt"

# Try to extract Python code
PYTHON_CODE=$(echo "$CONTENT" | sed -n '/```python/,/```/p' | sed '1d;$d')

if [ -n "$PYTHON_CODE" ]; then
    echo "Python code extracted successfully!"
    echo "$PYTHON_CODE" > test_output/add_numbers.py
    echo "Python code saved to test_output/add_numbers.py"
    
    # Test if the code runs
    echo "\nTesting if the generated code runs:"
    python3 -m py_compile test_output/add_numbers.py
    if [ $? -eq 0 ]; then
        echo "✅ Code compiles successfully!"
    else
        echo "❌ Code compilation failed!"
    fi
else
    echo "No Python code found in the response!"
fi

# Now test with gollm CLI
echo "\n2. Testing with gollm CLI..."

# First with standard mode
echo "Testing with standard mode..."
GOLLM_ADAPTER_TYPE=modular GOLLM_LOG_LEVEL=DEBUG gollm generate "Write a Python function to add two numbers" > test_output/gollm_output.txt 2>&1
echo "gollm output saved to test_output/gollm_output.txt"

# Check if a .py file was created in the current directory
PY_FILES=$(find . -maxdepth 1 -name "*.py" -type f -newer test_output/gollm_output.txt)
if [ -n "$PY_FILES" ]; then
    echo "✅ gollm created Python file(s): $PY_FILES"
    # Copy the file to our test output directory
    cp $PY_FILES test_output/
    echo "Copied to test_output/"
else
    echo "❌ No Python files created by gollm!"
fi

# Try with fast mode
echo "\nTesting with fast mode..."
GOLLM_ADAPTER_TYPE=modular GOLLM_LOG_LEVEL=DEBUG gollm generate "Write a Python function to add two numbers" --fast > test_output/gollm_fast_output.txt 2>&1
echo "gollm fast mode output saved to test_output/gollm_fast_output.txt"

# Check if a .py file was created in the current directory
PY_FILES_FAST=$(find . -maxdepth 1 -name "*.py" -type f -newer test_output/gollm_fast_output.txt)
if [ -n "$PY_FILES_FAST" ]; then
    echo "✅ gollm fast mode created Python file(s): $PY_FILES_FAST"
    # Copy the file to our test output directory
    cp $PY_FILES_FAST test_output/
    echo "Copied to test_output/"
else
    echo "❌ No Python files created by gollm in fast mode!"
fi

echo "\nTest summary:"
echo "============="
echo "1. Direct API call: $([ -f test_output/add_numbers.py ] && echo "✅ Success" || echo "❌ Failed")"
echo "2. gollm standard: $([ -n "$PY_FILES" ] && echo "✅ Success" || echo "❌ Failed")"
echo "3. gollm fast mode: $([ -n "$PY_FILES_FAST" ] && echo "✅ Success" || echo "❌ Failed")"

echo "\nAll test outputs saved in the test_output directory"
