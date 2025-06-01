
.PHONY: install dev test lint format clean build publish demo-interactive demo-script

# Instalacja
install:
	pip install -e .

dev:
	pip install -e .[dev]

# Testowanie
test:
	pytest tests/ -v
	
test-coverage:
	pytest tests/ --cov=src/gollm --cov-report=html --cov-report=term-missing

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
	find . -name "*.pyc" -delete || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

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
	@echo "4️⃣  Next TODO task..."
	@echo "--------------------"
	python -m gollm next-task

	@echo ""
	@echo "🎉 Demo completed!"
	@echo ""
	@echo "💡 Try these commands:"
	@echo "   gollm validate-project    # Validate entire project"
	@echo "   gollm generate 'create user class'  # Generate code with LLM"
	@echo "   gollm fix --auto         # Auto-fix violations"
	@echo "   gollm --help             # Show all commands"
