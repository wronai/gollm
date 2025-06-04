#!/bin/bash

# Exit on error
set -e

echo "🚀 Initializing test environment..."

# Stop any existing containers
echo "🛑 Stopping any existing containers..."
docker-compose down -v 2>/dev/null || true

# Build the Docker containers
echo "🔨 Building Docker containers..."
docker-compose build

# Start Ollama in the background
echo "🚀 Starting Ollama service..."
docker-compose up -d ollama

# Get the host IP
HOST_IP=$(hostname -I | awk '{print $1}')
echo "🌐 Using host IP: $HOST_IP"

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
until docker-compose exec -T ollama curl -s http://localhost:11434/api/tags >/dev/null; do
    echo "⏳ Waiting for Ollama to be ready..."
    sleep 1
done

echo "✅ Ollama is ready!"

# Pull the required model
echo "📥 Pulling tinyllama model..."
docker-compose exec -T ollama ollama pull tinyllama

echo "✨ Test environment is ready!"
echo "You can now run tests with: make docker-test"
echo "Or open a shell in the test environment with: make docker-shell"
