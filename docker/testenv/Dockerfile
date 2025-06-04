# Use Python 3.12 slim as the base image
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements files
COPY requirements.txt .
COPY requirements-dev.txt .

# Install Python dependencies and setuptools
RUN pip install --no-cache-dir setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Copy the entire project
COPY . .

# Install the package in development mode
RUN pip install -e .

# Set environment variables
ENV PYTHONPATH=/app
ENV OLLAMA_HOST=http://ollama:11434
ENV GOLLM_TEST_TIMEOUT=30
ENV GOLLM_MODEL=tinyllama:latest
ENV PYTHONUNBUFFERED=1

# Install test dependencies
RUN pip install pytest-timeout pytest-cov

# Create a non-root user and switch to it
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Default command to keep the container running
CMD ["tail", "-f", "/dev/null"]
