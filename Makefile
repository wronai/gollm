
.PHONY: install dev test test-e2e test-health lint format clean build publish demo-interactive demo-script infra-setup infra-deploy check-env

# Instalacja
install:
	pip install -e .

dev:
	pip install -e .[dev]

# Testowanie
test:
	pytest tests/ -v

# Run end-to-end tests (requires Ollama service running)
test-e2e: check-ollama
	pytest tests/e2e -v -m "not slow"

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


# Publikacja
publish-test: build
	python -m twine upload --repository testpypi dist/*

publish: version build
	python -m twine upload dist/*

# Rozwój
dev-setup: dev
	python scripts/install_hooks.py
	python scripts/setup_ide.py vscode
	echo "🎉 Development environment ready!"

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
test-install:
	pip uninstall gollm -y || true
	pip install -e .
	gollm --help
	echo "✅ Installation test passed"

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
