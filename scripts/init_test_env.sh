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

# Wait for Ollama to be healthy
echo "⏳ Waiting for Ollama to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    STATUS=$(docker inspect --format='{{.State.Health.Status}}' ollama 2>/dev/null || echo "starting")
    
    if [ "$STATUS" = "healthy" ]; then
        echo "✅ Ollama is ready!"
        break
    elif [ "$STATUS" = "unhealthy" ]; then
        echo "❌ Ollama is unhealthy. Check logs with: docker-compose logs ollama"
        exit 1
    else
        echo "⏳ Waiting for Ollama to be ready... (Status: $STATUS, Attempt $((RETRY_COUNT + 1))/$MAX_RETRIES)"
        RETRY_COUNT=$((RETRY_COUNT + 1))
        sleep 5
    fi

done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ Timed out waiting for Ollama to be ready"
    echo "📋 Ollama logs:"
    docker-compose logs ollama
    exit 1
fi

# Pull the tinyllama model
echo "📥 Pulling tinyllama model..."
docker-compose exec -T ollama ollama pull tinyllama

echo "✨ Test environment is ready!"
echo "You can now run tests with: make docker-test"
echo "Or open a shell in the test environment with: make docker-shell"
echo "View logs with: make docker-logs"
