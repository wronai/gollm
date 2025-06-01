
.PHONY: install dev test lint format clean build publish

# Instalacja
install:
	pip install -e .

dev:
	pip install -e .[dev]

# Testowanie
test:
	pytest tests/ -v
	
test-coverage:
	pytest tests/ --cov=src/spyq --cov-report=html --cov-report=term-missing

# Jakość kodu
lint:
	flake8 src tests
	mypy src
	
format:
	black src tests
	isort src tests

# SPYQ self-validation
spyq-check:
	python -m spyq validate-project
	python -m spyq status

# Czyszczenie
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -name "*.pyc" -delete

# Budowanie
build: clean
	python -m build

# Publikacja
publish-test: build
	python -m twine upload --repository testpypi dist/*

publish: build
	python -m twine upload dist/*

# Rozwój
dev-setup: dev
	python scripts/install_hooks.py
	python scripts/setup_ide.py vscode
	echo "🎉 Development environment ready!"

# Demo
demo:
	@echo "🚀 SPYQ Demo"
	@echo "1. Validating bad code example..."
	python -m spyq validate examples/bad_code.py
	@echo "\n2. Showing good code example..."
	python -m spyq validate examples/good_code.py
	@echo "\n3. Project status..."
	python -m spyq status

# Test quick installation
test-install:
	pip uninstall spyq -y || true
	pip install -e .
	spyq --help
	echo "✅ Installation test passed"

# run_demo.sh
#!/bin/bash

echo "🚀 SPYQ - Smart Python Quality Guardian Demo"
echo "=============================================="

# Sprawdź czy Python jest zainstalowany
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Utwórz wirtualne środowisko jeśli nie istnieje
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Aktywuj wirtualne środowisko
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Zainstaluj SPYQ
echo "⬇️  Installing SPYQ..."
pip install -e .

echo ""
echo "🎯 SPYQ Demo - Code Quality in Action"
echo "======================================"

echo ""
echo "1️⃣  Validating BAD code example..."
echo "-----------------------------------"
python -m spyq validate examples/bad_code.py

echo ""
echo "2️⃣  Validating GOOD code example..."
echo "------------------------------------"
python -m spyq validate examples/good_code.py

echo ""
echo "3️⃣  Project status overview..."
echo "------------------------------"
python -m spyq status

echo ""
echo "4️⃣  Next TODO task..."
echo "--------------------"
python -m spyq next-task

echo ""
echo "🎉 Demo completed!"
echo ""
echo "💡 Try these commands:"
echo "   spyq validate-project    # Validate entire project"
echo "   spyq generate 'create user class'  # Generate code with LLM"
echo "   spyq fix --auto         # Auto-fix violations"
echo "   spyq --help             # Show all commands"
