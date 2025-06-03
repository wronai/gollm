#!/bin/bash

# Script to test GoLLM code generation with direct execution
# Each test generates Python code and runs it immediately

# Set up colors for output
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
NC="\033[0m" # No Color

TEST_DIR="$(mktemp -d)"
cd "$TEST_DIR" || exit 1
echo -e "${YELLOW}Running tests in temporary directory: $TEST_DIR${NC}"

# Function to run a test case
run_test() {
    local test_num=$1
    local description=$2
    local prompt=$3
    local expected_output=$4
    
    echo -e "\n${YELLOW}Test $test_num: $description${NC}"
    echo -e "Prompt: \"$prompt\""
    
    # Create a temporary Python file for output
    output_file="$TEST_DIR/output_$test_num.py"
    
    # Run gollm generate with the prompt and output to file
    output=$(gollm generate "$prompt" -o "$output_file" 2>&1)
    exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        echo -e "${RED}\u2718 Test $test_num failed: gollm generate command returned non-zero exit code $exit_code${NC}"
        echo "Output:"
        echo "$output"
        return 1
    fi
    
    # Check if the file was created
    if [ ! -f "$output_file" ]; then
        echo -e "${RED}\u2718 Test $test_num failed: Output file was not created${NC}"
        echo "gollm output:"
        echo "$output"
        return 1
    fi
    
    # Execute the generated Python code
    python_output=$(python "$output_file" 2>&1)
    python_exit_code=$?
    
    # Store combined output for checking
    output="$output\n\nPython execution output:\n$python_output"
    
    # Check if Python execution succeeded
    if [ $python_exit_code -ne 0 ]; then
        echo -e "${RED}✘ Test $test_num failed: Python execution returned non-zero exit code $python_exit_code${NC}"
        echo "Output:"
        echo -e "$output"
        return 1
    fi
    
    # If expected output is provided, check for it
    if [ -n "$expected_output" ]; then
        if echo -e "$output" | grep -q "$expected_output"; then
            echo -e "${GREEN}✓ Test $test_num passed: Found expected output${NC}"
        else
            echo -e "${RED}✘ Test $test_num failed: Expected output not found${NC}"
            echo "Output:"
            echo -e "$output"
            return 1
        fi
    else
        # If no specific output is expected, just check that it ran without errors
        echo -e "${GREEN}✓ Test $test_num passed: Code generated and executed successfully${NC}"
    fi
    
    return 0
}

# Run all test cases
failed_tests=0

# Test 1: Simple function that adds two numbers
run_test 1 "Simple addition function" \
         "Create a function that adds two numbers and test it with the values 5 and 7" \
         "12"
failed_tests=$((failed_tests + $?))

# Test 2: User class (in Polish)
run_test 2 "User class in Polish" \
         "Stwórz klasę użytkownika z polami imię, nazwisko, email i metodą do wyświetlania pełnych danych" \
         "imię"
failed_tests=$((failed_tests + $?))

# Test 3: Recursive factorial function
run_test 3 "Recursive factorial function" \
         "Create a recursive factorial function and test it with the value 5" \
         "120"
failed_tests=$((failed_tests + $?))

# Test 4: Fibonacci sequence
run_test 4 "Fibonacci sequence generator" \
         "Create a function that returns the first 10 numbers in the Fibonacci sequence" \
         "0, 1, 1, 2, 3, 5, 8, 13, 21, 34"
failed_tests=$((failed_tests + $?))

# Test 5: String manipulation
run_test 5 "Word counter function" \
         "Create a function that counts the occurrences of each word in a sentence and test it" \
         ""
failed_tests=$((failed_tests + $?))

# Test 6: Simple calculator class
run_test 6 "Calculator class" \
         "Create a Calculator class with methods for addition, subtraction, multiplication, and division" \
         ""
failed_tests=$((failed_tests + $?))

# Test 7: List comprehension
run_test 7 "List comprehension for filtering" \
         "Create a function that uses list comprehension to filter even numbers from a list and test it" \
         ""
failed_tests=$((failed_tests + $?))

# Test 8: File operations
run_test 8 "File read/write operations" \
         "Create a function that writes numbers 1 to 10 to a file and another function that reads and prints them" \
         ""
failed_tests=$((failed_tests + $?))

# Test 9: Exception handling
run_test 9 "Exception handling" \
         "Create a function that demonstrates try/except/finally blocks for division by zero" \
         "exception"
failed_tests=$((failed_tests + $?))

# Test 10: Class inheritance
run_test 10 "Class inheritance" \
         "Create a base Shape class and derived Circle and Rectangle classes with area methods" \
         "area"
failed_tests=$((failed_tests + $?))

# Print summary
echo -e "\n${YELLOW}Test Summary:${NC}"
if [ $failed_tests -eq 0 ]; then
    echo -e "${GREEN}All tests passed successfully!${NC}"
else
    echo -e "${RED}$failed_tests test(s) failed.${NC}"
fi

# Clean up
cd - > /dev/null
echo -e "${YELLOW}Tests completed. Temporary directory will remain for inspection: $TEST_DIR${NC}"

exit $failed_tests
