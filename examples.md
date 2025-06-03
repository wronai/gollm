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

## Web Development

### Flask Web Application
```bash
gollm generate "Create a simple Flask web app with a single endpoint that returns current time"
```

### FastAPI Endpoint
```bash
gollm generate "Generate a FastAPI endpoint that accepts JSON and returns a greeting"
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

## Polish Language Examples

### Proste przykłady po polsku
```bash
gollm generate "Napisz funkcję w Pythonie, która oblicza średnią z listy liczb"
gollm generate "Stwórz klasę Pracownik z polami imię, nazwisko i wynagrodzenie"
```

### Zaawansowane użycie
```bash
gollm generate "Napisz skrypt, który czyta plik CSV i generuje wykres słupkowy"
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

## Debugging Help

### Error Analysis
```bash
gollm "I'm getting 'IndexError: list index out of range' in my Python code. How to fix it?"
```

### Code Review
```bash
gollm "Review this Python code for potential issues and suggest improvements"
```
