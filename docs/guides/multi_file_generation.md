# Multi-File Project Generation

## Overview

goLLM's multi-file project generation allows you to create complete project structures with a single command. This feature is particularly useful for scaffolding new applications, libraries, or websites.

## Basic Usage

### Generating a New Project

```bash
# Generate a new project
gollm generate "Create a Flask web application with user authentication" -o myapp
```

This will create a directory structure like:

```
myapp/
├── app.py
├── requirements.txt
├── static/
│   ├── css/
│   └── js/
├── templates/
│   ├── base.html
│   └── index.html
└── README.md
```

### Supported Project Types

goLLM can generate various types of projects:

1. **Web Applications**
   ```bash
   gollm generate "Create a FastAPI REST API with SQLAlchemy" -o myapi
   ```

2. **Libraries**
   ```bash
   gollm generate "Create a Python library for data validation" -o mylib
   ```

3. **CLI Tools**
   ```bash
   gollm generate "Create a command-line tool for file processing" -o mycli
   ```

4. **Full-Stack Applications**
   ```bash
   gollm generate "Create a React frontend with FastAPI backend" -o fullstack
   ```

## Project Structure

### Web Application Structure

```
myapp/
├── app/                      # Application package
│   ├── __init__.py
│   ├── models.py            # Database models
│   ├── routes/              # Route handlers
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── api.py
│   └── utils/               # Utility functions
├── tests/                   # Test files
│   ├── __init__.py
│   └── test_app.py
├── static/                  # Static files
│   ├── css/
│   ├── js/
│   └── images/
├── templates/               # HTML templates
│   ├── base.html
│   ├── index.html
│   └── auth/
│       ├── login.html
│       └── register.html
├── .env                    # Environment variables
├── .gitignore
├── requirements.txt        # Python dependencies
├── README.md              # Project documentation
└── app.py                 # Application entry point
```

### Library Structure

```
mylib/
├── src/
│   └── mylib/             # Source package
│       ├── __init__.py
│       ├── core.py         # Core functionality
│       └── utils/          # Utility modules
├── tests/                  # Test files
│   ├── __init__.py
│   └── test_core.py
├── docs/                   # Documentation
│   ├── index.md
│   └── api/
├── .gitignore
├── pyproject.toml          # Build configuration
├── README.md
└── setup.py
```

## Advanced Usage

### Specifying Project Type

You can explicitly specify the project type:

```bash
# Generate a FastAPI project
gollm generate "Create a FastAPI project" -o myapi --type fastapi

# Generate a React project
gollm generate "Create a React app" -o myapp --type react
```

### Including Dependencies

Specify required dependencies in your prompt:

```bash
gollm generate "Create a project using FastAPI, SQLAlchemy, and Pydantic" -o myapi
```

### Custom Templates

Create custom project templates in `~/.gollm/templates/`:

```
~/.gollm/templates/
└── my-template/
    ├── template.json
    ├── {{project_name}}/
    │   ├── README.md
    │   └── {{project_name}}/
    │       └── __init__.py
    └── hooks/
        └── post_generate.py
```

Use the template:

```bash
gollm generate --template my-template -o myproject
```

## Best Practices

1. **Be Specific**
   - Clearly describe your requirements
   - Mention the frameworks and libraries you want to use
   - Specify any architectural patterns

2. **Start Small**
   - Generate a minimal viable project first
   - Add features incrementally

3. **Review Generated Code**
   - Always review the generated code
   - Add tests as needed
   - Update documentation

## Troubleshooting

### Common Issues

#### 1. Incomplete Generation

```bash
# Regenerate with more specific prompt
gollm generate "Create a complete Flask app with User model and authentication" -o myapp
```

#### 2. Missing Dependencies

```bash
# Check requirements.txt
cat myapp/requirements.txt

# Install missing dependencies
pip install -r myapp/requirements.txt
```

#### 3. File Structure Issues

```bash
# Check the generated structure
tree myapp

# Regenerate with --verbose for more details
gollm generate "..." -o myapp --verbose
```

## Examples

### Generate a Data Science Project

```bash
gollm generate "Create a data science project with Jupyter, pandas, and scikit-learn" -o datascience
```

### Generate a Microservice

```bash
gollm generate "Create a microservice with FastAPI, Redis, and Docker" -o myservice
```

### Generate a Full-Stack Application

```bash
gollm generate "Create a full-stack application with React frontend and FastAPI backend" -o fullstack
```

## Next Steps

- [Configuration Guide](../configuration/README.md) - Customize project generation
- [API Reference](../api/README.md) - Learn about the generation API
- [Extending goLLM](../api/extensions.md) - Create custom project templates
