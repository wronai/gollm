
.PHONY: help install dev test test-e2e test-coverage test-health lint format clean build publish demo-interactive demo-script infra-setup infra-deploy check-env setup docs docker-test docker-shell docker-clean docker-build

# Help target to show available commands
help:
	@echo "\nAvailable targets:"
	@echo "  help           - Show this help message"
	@echo "  install        - Install the package in development mode"
	@echo "  dev            - Install development dependencies"
	@echo "  setup          - Set up development environment"
	@echo "  test           - Run tests locally"
	@echo "  test-coverage  - Run tests with coverage report"
	@echo "  test-e2e       - Run end-to-end tests"
	@echo "  test-health    - Run health check script"
	@echo "  lint           - Run linters"
	@echo "  format         - Format code"
	@echo "  clean          - Clean build artifacts"
	@echo "  build          - Build package"
	@echo "  publish        - Publish to PyPI"
	@echo "  docs           - Build documentation"
	@echo "  demo           - Run demo"
	@echo "  docker-build   - Build Docker containers"
	@echo "  docker-test    - Run tests in Docker"
	@echo "  docker-shell   - Open shell in test environment"
	@echo "  docker-clean   - Remove Docker containers and volumes"

# Installation
install:
	pip install -e .

# Development environment
dev:
	pip install -e .[dev]

# Test locally (requires local Python environment)
test:
	pytest --timeout=60

# Run end-to-end tests (requires Ollama service running)
test-e2e: check-ollama
	pytest tests/e2e -v -m "not slow"

# Run streaming tests (requires Ollama service with modular adapter)
test-streaming: check-ollama
	OLLAMA_ADAPTER_TYPE=modular pytest tests/e2e/test_streaming.py -v

# Run all tests including slow ones
test-all: check-ollama
	pytest tests/ -v

# Run health check script
test-health:
	chmod +x tests/health_check.sh
	./tests/health_check.sh

# Check if Ollama service is running
check-ollama:
	@if ! curl -s http://localhost:11434/api/tags > /dev/null; then \
		echo "Error: Ollama service is not running. Please start it first with 'make infra-start'" >&2; \
		exit 1; \
	fi

# Run tests with coverage report
test-coverage:
	pytest tests/ --cov=src/gollm --cov-report=html --cov-report=term-missing
	@echo "\nCoverage report generated in htmlcov/index.html"

# Start infrastructure (Ollama service)
infra-start:
	docker-compose -f tests/infrastructure/docker-compose.yml up -d

# Stop infrastructure
infra-stop:
	docker-compose -f tests/infrastructure/docker-compose.yml down

# Deploy infrastructure using Ansible
infra-deploy: check-ansible
	ansible-playbook -i tests/ansible/inventory.ini tests/ansible/playbook.yml

# Check if Ansible is installed
check-ansible:
	@if ! command -v ansible > /dev/null; then \
		echo "Error: Ansible is not installed. Please install it first." >&2; \
		exit 1; \
	fi

# Jakość kodu
lint:
	flake8 src tests
	mypy src
	
format:
	black src tests
	isort src tests

# goLLM self-validation
gollm-check:
	python -m gollm validate-project
	python -m gollm status

# Czyszczenie
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -name "*.pyc" -delete || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.py,cover" -delete || true
	find . -name "coverage.xml" -delete || true
	find . -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

version:
	@echo "Updating version in pyproject.toml"
	@current_version=$$(grep -oP 'version = "\K[0-9]+\.[0-9]+\.[0-9]+(?=")' pyproject.toml); \
	IFS='.' read -r major minor patch <<< "$$current_version"; \
	new_patch=$$((patch + 1)); \
	new_version="$$major.$$minor.$$new_patch"; \
	sed -i "s/version = \".*\"/version = \"$$new_version\"/" pyproject.toml; \
	echo "Version updated from $$current_version to $$new_version"

# Budowanie
build: clean
	if [ ! -d "venv" ]; then \
		python -m venv venv; \
		. venv/bin/activate; \
		pip install -U pip setuptools wheel build twine; \
	else \
		. venv/bin/activate; \
		pip install -q --upgrade pip setuptools wheel build twine; \
	fi
	pip install -e .
	python -m build


# Build documentation
docs:
	@echo "Building documentation..."
	sphinx-build -b html docs/source docs/build
	@echo "\nDocumentation built in docs/build/index.html"

# Publish to PyPI
publish-test: build
	python -m twine upload --repository testpypi dist/*

publish: version build
	python -m twine upload dist/*

# Setup development environment
setup: dev
	@echo "Setting up development environment..."
	python -m pip install --upgrade pip
	pip install -e .[dev]
	python scripts/install_hooks.py
	python scripts/setup_ide.py vscode
	@echo "🎉 Development environment ready!"

# Demo
demo:
	@echo "🚀 goLLM Demo"
	@echo "1. Validating bad code example..."
	python -m gollm validate examples/bad_code.py
	@echo "\n2. Showing good code example..."
	python -m gollm validate examples/good_code.py
	@echo "\n3. Project status..."
	python -m gollm status
	@echo "\n4. Testing fast mode..."
	python -m gollm generate "Create a simple function" --fast
	@echo "\n5. Testing direct mode..."
	python -m gollm direct generate "Create a simple function"

# Test quick installation
# Docker commands
docker-build:
	docker-compose build

docker-test: docker-build
	docker-compose up --exit-code-from testenv --remove-orphans testenv

docker-shell:
	docker-compose run --rm --service-ports dev /bin/bash

docker-logs:
	docker-compose logs -f

docker-clean:
	docker-compose down -v --remove-orphans
	docker volume rm -f gollm_ollama_data gollm_gollm-cache 2>/dev/null || true
	docker rmi -f gollm_testenv gollm_dev 2>/dev/null || true
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true

# Show help
docker-help:
	@echo "Available Docker commands:"
	@echo "  make docker-build     - Build the Docker containers"
	@echo "  make docker-test      - Run tests in Docker"
	@echo "  make docker-shell     - Open a shell in the dev container"
	@echo "  make docker-logs      - View container logs"
	@echo "  make docker-clean     - Clean up Docker resources"

# Demo script target
demo-script:
	@echo "Run scripts/run_demo.sh instead"

demo-interactive:
	@echo ""
	@echo "🎯 goLLM Demo - Code Quality in Action"
	@echo "======================================"
	@echo ""
	@echo "1️⃣  Validating BAD code example..."
	@echo "-----------------------------------"
	python -m gollm validate examples/bad_code.py

	@echo ""
	@echo "2️⃣  Validating GOOD code example..."
	@echo "------------------------------------"
	python -m gollm validate examples/good_code.py

	@echo ""
	@echo "3️⃣  Project status overview..."
	@echo "------------------------------"
	python -m gollm status

	@echo ""
	@echo "4️⃣  Code generation with fast mode..."
	@echo "---------------------------------------"
	python -m gollm generate "Create a simple calculator function" --fast

	@echo ""
	@echo "5️⃣  Direct API access (curl-like)..."
	@echo "------------------------------------"
	python -m gollm direct generate "Create a simple hello world function"

	@echo ""
	@echo "6️⃣  Next TODO task..."
	@echo "--------------------"
	python -m gollm next-task

	@echo ""
	@echo "🎉 Demo completed!"
	@echo ""
	@echo "💡 Try these commands:"
	@echo "   gollm validate-project    # Validate entire project"
	@echo "   gollm generate 'create user class'  # Generate code with LLM"
	@echo "   gollm generate --fast 'quick function'  # Fast generation"
	@echo "   gollm direct generate 'direct api call'  # Direct API access"
	@echo "   gollm --help             # Show all commands"
