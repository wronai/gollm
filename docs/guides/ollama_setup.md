# Setting Up Ollama with goLLM

## Overview

[Ollama](https://ollama.ai/) is a lightweight, extensible framework for running large language models locally. This guide explains how to set up Ollama for use with goLLM.

## Prerequisites

- Docker (for Ollama installation)
- At least 8GB RAM (16GB recommended)
- At least 10GB free disk space

## Installation

### 1. Install Ollama

#### Linux/macOS

```bash
# Download and install
curl -fsSL https://ollama.ai/install.sh | sh

# Start the Ollama service
ollama serve
```

#### Windows

Download and run the installer from [Ollama's website](https://ollama.ai/download).

### 2. Pull a Model

```bash
# List available models
ollama list

# Pull a model (e.g., CodeLlama)
ollama pull codellama:7b

# For better code generation, use a larger model
ollama pull codellama:34b
```

## Configuration

### 1. Update goLLM Configuration

Edit your `gollm.json` file to use Ollama:

```json
{
  "llm_integration": {
    "enabled": true,
    "default_provider": "ollama",
    "providers": {
      "ollama": {
        "base_url": "http://localhost:11434",
        "model": "codellama:7b",
        "temperature": 0.5
      }
    }
  }
}
```

### 2. Environment Variables (Optional)

```bash
# Set default model
export OLLAMA_MODEL=codellama:7b

# Set Ollama server URL (if different from default)
export OLLAMA_HOST=127.0.0.1:11434
```

## Usage

### Basic Usage

```bash
# Generate code with Ollama
gollm generate "Create a Python function to sort a list" --model ollama

# Chat with the model
gollm chat --model ollama
```

### Advanced Usage

#### Custom Model Configuration

Create a `Modelfile` to customize the model behavior:

```dockerfile
FROM codellama:7b

# Set system prompt
SYSTEM """
You are a helpful coding assistant. 
Follow these rules:
1. Write clean, efficient code
2. Include type hints and docstrings
3. Follow PEP 8 guidelines
"""

# Set parameters
PARAMETER temperature 0.7
PARAMETER top_k 40
PARAMETER top_p 0.9
```

Build and use the custom model:

```bash
# Build the model
ollama create mymodel -f Modelfile

# Use the custom model
gollm generate --model ollama:mymodel "Write a function to parse JSON"
```

## Performance Tuning

### GPU Acceleration

Ollama supports GPU acceleration with CUDA. To enable it:

```bash
# Install NVIDIA Container Toolkit
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update
sudo apt-get install -y nvidia-docker2

# Restart Docker
sudo systemctl restart docker

# Run Ollama with GPU support
docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

# Pull a model with GPU support
ollama pull codellama:7b-gpu
```

### Memory Optimization

For systems with limited RAM:

```bash
# Use smaller models
ollama pull codellama:7b

# Reduce context length
PARAMETER num_ctx 2048

# Use 4-bit quantization
ollama pull codellama:7b:q4_0
```

## Troubleshooting

### Common Issues

#### 1. Connection Refused

```bash
# Check if Ollama is running
ollama list

# If not, start the service
ollama serve
```

#### 2. Out of Memory

```bash
# Check available memory
free -h

# Use a smaller model
ollama pull codellama:7b
```

#### 3. Slow Performance

```bash
# Check GPU usage
nvidia-smi

# Increase Docker resources in Docker Desktop
# or limit model context length
PARAMETER num_ctx 2048
```

## Best Practices

1. **Model Selection**
   - Use smaller models (7B) for development
   - Switch to larger models (13B, 34B) for complex tasks

2. **Prompt Engineering**
   - Be specific in your prompts
   - Provide examples when possible
   - Use system prompts to set behavior

3. **Resource Management**
   - Monitor system resources
   - Close unused models: `ollama rm modelname`
   - Clear the model cache: `ollama rm --all`

## Next Steps

- [goLLM Documentation](../README.md)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [CodeLlama Models](https://github.com/facebookresearch/codellama)
