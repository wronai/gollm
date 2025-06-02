# Test Makefile for goLLM Project
# This Makefile provides commands to run different test suites and generate reports

.PHONY: help all unit integration e2e coverage lint clean

# Default target - show help
help:
	@echo "Test targets:"
	@echo "  make help       - Show this help message"
	@echo "  make all        - Run all test suites"
	@echo "  make unit       - Run unit tests"
	@echo "  make integration - Run integration tests"
	@echo "  make e2e        - Run end-to-end tests (requires Ollama service)"
	@echo "  make coverage   - Generate test coverage report"
	@echo "  make lint       - Run code linters"
	@echo "  make clean      - Clean test artifacts"

# Run all test suites
all: unit integration e2e

# Run unit tests (fast, isolated tests)
unit:
	@pytest -v -m "not integration and not e2e"

# Run integration tests
integration:
	@pytest -v -m integration

# Run end-to-end tests (requires Ollama service)
e2e: check-ollama
	@pytest -v -m e2e

# Generate test coverage report
coverage:
	@pytest --cov=../src/gollm --cov-report=term-missing --cov-report=html

# Run code linters
lint:
	@flake8 .
	@mypy .


# Clean test artifacts
clean:
	@find . -name '*.pyc' -delete
	@find . -name '__pycache__' -delete
	@rm -rf .pytest_cache/
	@rm -rf htmlcov/
	@rm -f .coverage

# Check if Ollama service is running
check-ollama:
	@if ! curl -s http://localhost:11434/api/tags > /dev/null; then \
		echo "Error: Ollama service is not running. Please start it first with 'make infra-start' in the project root"; \
		exit 1; \
	fi
