# GoLLM Code Generation Tests

## Overview

This directory contains end-to-end tests for GoLLM's code generation capabilities, focusing on verifying that:

1. GoLLM can generate valid Python code from natural language prompts
2. The generated code can be executed successfully
3. The code produces expected outputs

## Test Files

### `test_code_generation_run.py`

A unittest-based test suite that programmatically tests GoLLM's code generation with direct execution. This is designed to be run as part of the automated test suite.

```bash
python -m unittest tests/e2e/test_code_generation_run.py
```

### `run_code_generation_tests.sh`

A shell script that runs a series of 10 different code generation tests and verifies their outputs. This script is useful for quick manual testing and demonstration purposes.

```bash
./tests/e2e/run_code_generation_tests.sh
```

## Test Scenarios

Both test suites cover the following scenarios:

1. **Simple Function**: Tests generation of a basic addition function
2. **User Class (in Polish)**: Tests creating a user class with fields and methods
3. **Recursive Factorial**: Tests generation of a recursive algorithm
4. **Fibonacci Sequence**: Tests generation of a sequence generation function
5. **String Manipulation**: Tests word counting in sentences
6. **Calculator Class**: Tests class with multiple arithmetic methods
7. **List Comprehension**: Tests functional programming patterns
8. **File Operations**: Tests file I/O operations
9. **Exception Handling**: Tests try/except/finally blocks
10. **Class Inheritance**: Tests OOP inheritance with Shape, Circle, and Rectangle classes

## Integration with Iterative Code Completion

These tests also implicitly verify the functionality of the iterative code completion feature, which:

- Detects incomplete functions in generated code
- Automatically prompts the LLM to complete these functions
- Merges the completed functions back into the original code
- Continues this process until all functions are fully implemented or iteration limits are reached

The test cases are designed to exercise a wide range of Python programming concepts, making them effective for validating both the basic code generation capabilities and the more advanced iterative completion functionality.
