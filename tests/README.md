# goLLM Test Suite

This directory contains the test suite for the goLLM project. The tests are organized into different categories to ensure comprehensive test coverage.

## Test Organization

### Unit Tests
Fast, isolated tests that verify individual components in isolation.

- `test_validators.py`: Tests for input validation utilities
- `test_config_aggregator.py`: Tests for configuration management
- `test_todo_manager.py`: Tests for TODO management functionality
- `test_changelog_manager.py`: Tests for changelog generation and management

### Integration Tests
Tests that verify the interaction between components.

- `test_llm_orchestrator.py`: Tests for the LLM orchestration layer
- `test_gollm.py`: Integration tests for the main application

### End-to-End Tests
Tests that verify the complete system functionality (requires Ollama service).

- `test_ollama.py`: Basic Ollama LLM provider tests
- `test_ollama_direct.py`: Direct API tests for Ollama
- `test_ollama_integration.py`: Full integration tests with Ollama
- `test_basic_functionality.py`: End-to-end tests of core functionality

### Environment Tests
- `test_env.py`: Environment variable and configuration tests
- `test_import.py`: Module import tests

## Running Tests

### Prerequisites
- Python 3.8+
- `pytest`
- `pytest-cov` (for coverage reports)
- Ollama service running (for end-to-end tests)

### Using Makefile (Recommended)

The `Makefile` provides convenient commands for running tests:

```bash
# Show available test commands
make help

# Run all tests
make all

# Run only unit tests
make unit

# Run only integration tests
make integration

# Run only end-to-end tests (requires Ollama)
make e2e

# Generate coverage report
make coverage

# Run code linters
make lint

# Clean test artifacts
make clean
```

### Directly with pytest

You can also run tests directly with pytest:

```bash
# Run all tests
pytest

# Run specific test file
pytest test_llm_orchestrator.py

# Run tests with specific markers
pytest -m "not slow"  # Skip slow tests
pytest -v             # Verbose output
pytest -s             # Show print output
```

## Test Coverage

To generate a coverage report:

```bash
make coverage
```

This will generate both a console report and an HTML report in the `htmlcov` directory.

## Writing New Tests

When adding new tests:

1. Place unit tests in the appropriate test file or create a new one if needed
2. Use descriptive test function names starting with `test_`
3. Add appropriate pytest markers (e.g., `@pytest.mark.integration`)
4. Include docstrings explaining what each test verifies
5. For end-to-end tests, mark them with `@pytest.mark.e2e`

## Debugging Tests

To debug a failing test:

```bash
# Run a specific test with pdb (Python debugger)
pytest test_file.py::test_function -v --pdb

# Run with detailed logging
pytest -v --log-cli-level=DEBUG
```

## Continuous Integration

The test suite is automatically run on pull requests and pushes to the main branch. See the project's CI configuration for details.
