# Contributing to goLLM

We welcome contributions from the community! This guide will help you get started with contributing to goLLM.

## 📋 Table of Contents

- [Code of Conduct](#-code-of-conduct)
- [Getting Started](#-getting-started)
- [Development Setup](#-development-setup)
- [Code Style](#-code-style)
- [Testing](#-testing)
- [Pull Request Process](#-pull-request-process)
- [Reporting Issues](#-reporting-issues)
- [Feature Requests](#-feature-requests)
- [Documentation](#-documentation)
- [Community](#-community)

## 👥 Code of Conduct

Please review our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing. We expect all contributors to adhere to these guidelines.

## 🚀 Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally
3. **Create a branch** for your changes
4. **Commit** your changes
5. **Push** your changes to your fork
6. Open a **pull request**

## 💻 Development Setup

### Prerequisites

- Python 3.8+
- pip
- Git
- pre-commit (recommended)

### Setup Instructions

```bash
# Clone your fork
git clone https://github.com/your-username/gollm.git
cd gollm

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install development dependencies
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install
```

## 🎨 Code Style

We use the following tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting
- **Flake8** for linting
- **mypy** for type checking

Run the following command to ensure your code meets our standards:

```bash
# Run all code quality checks
make check

# Or run them individually
make format  # Auto-format code
make lint    # Run linters
make type    # Run type checking
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run a specific test file
pytest tests/path/to/test_file.py

# Run tests with coverage
pytest --cov=gollm
```

### Writing Tests

- Place new test files in the `tests/` directory
- Follow the existing test structure
- Use descriptive test names
- Include docstrings explaining what each test verifies

## 🔄 Pull Request Process

1. Ensure your code passes all tests and checks
2. Update documentation as needed
3. Add or update tests for your changes
4. Keep your PR focused on a single feature or bug fix
5. Write a clear PR description explaining your changes
6. Reference any related issues

### PR Template

```markdown
## Description

[Brief description of the changes]

## Related Issues

- Fixes #issue_number
- Related to #issue_number

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Code style update (formatting, local variables)
- [ ] Refactoring (no functional changes, no api changes)
- [ ] Build related changes
- [ ] CI/CD related changes
- [ ] Other (please describe):

## Checklist

- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published in downstream modules
```

## 🐛 Reporting Issues

When reporting issues, please include:

1. A clear, descriptive title
2. Steps to reproduce the issue
3. Expected vs actual behavior
4. Environment details (OS, Python version, etc.)
5. Any relevant error messages or logs

## 💡 Feature Requests

We welcome feature requests! Please:

1. Check if a similar feature already exists
2. Explain why this feature would be valuable
3. Provide as much detail as possible
4. Include any relevant use cases

## 📚 Documentation

Good documentation is crucial. When making changes:

1. Update relevant docstrings
2. Update the documentation in `docs/`
3. Ensure all public APIs are documented
4. Add examples where helpful

## 🤝 Community

- Join our [Discord/Slack channel]()
- Follow us on [Twitter]()
- Read our [blog]()

## 🙏 Acknowledgments

- Thanks to all our contributors
- Special thanks to [list any major contributors or inspirations]

## 📝 License

By contributing, you agree that your contributions will be licensed under the project's [LICENSE](LICENSE).
