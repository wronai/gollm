# GoLLM Usage Examples

## Basic Code Generation

### Simple Python Function
```bash
gollm generate "Write a Python function to calculate factorial"
```

### Complete Python Script with Tests
```bash
gollm generate "Create a Python script that implements a basic calculator class with unit tests"
```

## Advanced Features

### Automatic Test Generation
```bash
# Generate code with automatic unit tests (default behavior)
gollm generate "Create a Python class for a bank account with deposit and withdraw methods"

# Disable automatic test generation
gollm generate "Create a Python class for a bank account" --no-tests
```

### Automatic Function Completion
```bash
# GoLLM will automatically detect and complete any incomplete functions
gollm generate "Create a Python class for a payment processor with error handling"

# Disable automatic function completion
gollm generate "Create a Python class for a payment processor" --no-auto-complete
```

### Automatic Code Execution Testing and Fixing
```bash
# GoLLM will automatically test the generated code by executing it
# and fix any runtime errors (default behavior)
gollm generate "Create a Python script that processes a list of numbers"

# Disable execution testing
gollm generate "Create a Python script that processes a list of numbers" --no-execute-test

# Disable automatic fixing of execution errors
gollm generate "Create a Python script that processes a list of numbers" --no-auto-fix

# Increase the maximum number of fix attempts (default is 5)
gollm generate "Create a complex data processing script" --max-fix-attempts 10
```

### Increased Iteration Limit
```bash
# Use the default of 6 iterations for high-quality code
gollm generate "Create a robust error handling system"

# Specify a custom number of iterations
gollm generate "Create a robust error handling system" --iterations 10

# Use fast mode with minimal validation (1 iteration)
gollm generate "Create a simple utility function" --fast
```

## Web Development

### Flask Web Application
```bash
gollm generate "Create a simple Flask web app with a single endpoint that returns current time"
```

### FastAPI Endpoint
```bash
gollm generate "Generate a FastAPI endpoint that accepts JSON and returns a greeting"
```

### Full-Stack Web Application
```bash
# Generate a complete web application with frontend and backend
gollm generate "Create a to-do list web application with Flask and JavaScript"
```

## Data Analysis

### Pandas Data Processing
```bash
gollm generate "Write a Python script using pandas to load a CSV, clean the data, and create a basic visualization"
```

### Data Class Example
```bash
gollm generate "Create a Python dataclass for a Product with name, price, and quantity"
```

### Machine Learning Example
```bash
gollm generate "Create a simple machine learning model using scikit-learn for classifying iris flowers"
```

## Advanced Usage

### Using Different Adapters
```bash
gollm generate "Create a simple Python class" --adapter-type modular
gollm generate "Create a simple Python class" --adapter-type http
```

### Fast Mode for Quick Results
```bash
gollm generate "Write a Python function to sort a dictionary by value" --fast
```

### Multi-language Support
```bash
gollm generate "Write a function to reverse a string in JavaScript"
gollm generate "Create a simple Go HTTP server"
```

## Real-world Examples

### File Operations
```bash
gollm generate "Write a Python script that reads all .txt files in a directory and counts word frequencies"
```

### API Client
```bash
gollm generate "Create a Python client for a REST API that fetches and displays weather data"
```

### Database Operations
```bash
gollm generate "Write a Python script that connects to SQLite, creates a table, and performs CRUD operations"
```

### Asynchronous Programming
```bash
gollm generate "Create an asynchronous Python script that fetches data from multiple APIs concurrently"
```

### Design Patterns
```bash
gollm generate "Implement the Observer design pattern in Python"
gollm generate "Create a Factory pattern implementation for different payment methods"
```

## Polish Language Examples

### Proste przykłady po polsku
```bash
gollm generate "Napisz funkcję w Pythonie, która oblicza średnią z listy liczb"
gollm generate "Stwórz klasę Pracownik z polami imię, nazwisko i wynagrodzenie"
```

### Zaawansowane użycie
```bash
gollm generate "Napisz skrypt, który czyta plik CSV i generuje wykres słupkowy"
gollm generate "Stwórz aplikację webową do zarządzania zadaniami z użyciem Flask"
```

## Integration Examples

### Dockerfile Generation
```bash
gollm generate "Create a Dockerfile for a Python Flask application"
```

### GitHub Actions Workflow
```bash
gollm generate "Generate a GitHub Actions workflow for Python project with testing"
```

### Configuration Files
```bash
gollm generate "Create a comprehensive .gitignore file for a Python project"
gollm generate "Generate a pyproject.toml file for a modern Python package"
```

## Testing Examples

### Unit Testing
```bash
gollm generate "Create unit tests for a user authentication system"
```

### Integration Testing
```bash
gollm generate "Write integration tests for a REST API using pytest"
```

### Test-Driven Development
```bash
gollm generate "Implement a stack data structure using TDD approach"
```

## Debugging Help

### Error Analysis
```bash
gollm "I'm getting 'IndexError: list index out of range' in my Python code. How to fix it?"
```

### Code Review
```bash
gollm "Review this Python code for potential issues and suggest improvements"
```

### Performance Optimization
```bash
gollm generate "Optimize this Python function for better performance" --iterations 8
```

## Project Structure Examples

### Simple Package
```bash
gollm generate "Create a Python package structure for a utility library"
```

### Complex Application
```bash
gollm generate "Design a modular Flask application structure with blueprints"
```

### Microservices
```bash
gollm generate "Design a microservice architecture for an e-commerce system"
```
