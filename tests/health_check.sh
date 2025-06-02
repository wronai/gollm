#!/bin/bash

# Health check script for goLLM application
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a service is running
is_service_running() {
    local service_name=$1
    if systemctl is-active --quiet "$service_name"; then
        return 0
    else
        return 1
    fi
}

# Function to check if a port is in use
is_port_used() {
    local port=$1
    if command_exists netstat; then
        netstat -tuln | grep -q ":$port "
    else
        lsof -i ":$port" >/dev/null 2>&1
    fi
}

# Function to run a simple API test
run_api_test() {
    local endpoint="$1"
    local expected_status="${2:-200}"
    
    if command_exists curl; then
        status_code=$(curl -s -o /dev/null -w "%{http_code}" "$endpoint")
        if [ "$status_code" -eq "$expected_status" ]; then
            echo -e "${GREEN}✓${NC} API test passed: $endpoint"
            return 0
        else
            echo -e "${RED}✗${NC} API test failed: $endpoint (expected $expected_status, got $status_code)"
            return 1
        fi
    else
        echo "curl not available, skipping API tests"
        return 1
    fi
}

# Main health checks
echo "Running health checks..."

# 1. Check Python version
if command_exists python3; then
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
    echo "Python version: $python_version"
else
    echo -e "${RED}✗${NC} Python 3 is not installed"
    exit 1
fi

# 2. Check if required Python packages are installed
required_packages=("gollm" "pytest" "pytest-asyncio")
for pkg in "${required_packages[@]}"; do
    if python3 -c "import $pkg" &>/dev/null; then
        echo -e "${GREEN}✓${NC} $pkg is installed"
    else
        echo -e "${RED}✗${NC} $pkg is not installed"
        exit 1
    fi
done

# 3. Check if Ollama service is running
if is_service_running "ollama"; then
    echo -e "${GREEN}✓${NC} Ollama service is running"
else
    echo -e "${YELLOW}⚠${NC} Ollama service is not running"
fi

# 4. Check if required ports are available
required_ports=(11434)  # Add other required ports as needed
for port in "${required_ports[@]}"; do
    if is_port_used "$port"; then
        echo -e "${GREEN}✓${NC} Port $port is in use"
    else
        echo -e "${RED}✗${NC} Port $port is not in use"
    fi
done

# 5. Run API tests if applicable
# run_api_test "http://localhost:8000/health" 200

# 6. Run unit tests
if command_exists pytest; then
    echo "Running unit tests..."
    if python -m pytest tests/unit/ -v; then
        echo -e "${GREEN}✓${NC} Unit tests passed"
    else
        echo -e "${RED}✗${NC} Unit tests failed"
        exit 1
    fi
else
    echo "pytest not found, skipping unit tests"
fi

echo -e "\n${GREEN}✓ All health checks completed successfully!${NC}"
