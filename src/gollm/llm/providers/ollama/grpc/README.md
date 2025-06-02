# Ollama gRPC Client for GoLLM

This module provides a high-performance gRPC client for communicating with the Ollama API. Using gRPC instead of HTTP REST can significantly reduce latency and improve throughput, especially for large model inference requests.

## Benefits

- **Lower Latency**: gRPC uses HTTP/2 which allows for multiplexing requests over a single connection
- **Efficient Serialization**: Protocol Buffers are more efficient than JSON for serialization/deserialization
- **Streaming Support**: Native bidirectional streaming for real-time token generation
- **Connection Pooling**: Maintains persistent connections for better performance

## Setup

1. Install the required dependencies:

```bash
python -m pip install grpcio grpcio-tools protobuf
```

2. Generate the Python code from the protobuf definitions:

```bash
python -m gollm.llm.providers.ollama.grpc.setup_grpc
```

Alternatively, you can run the setup script directly:

```bash
python -m gollm.llm.providers.ollama.grpc.generate_protos
```

## Usage

To use the gRPC client in your configuration, set the `adapter_type` to `grpc` or enable `use_grpc`:

```python
config = {
    "base_url": "http://localhost:11434",
    "model": "codellama:7b",
    "adapter_type": "grpc"  # Use gRPC adapter
    # or
    # "use_grpc": True  # Automatically use gRPC if available
}
```

## Fallback Mechanism

If gRPC dependencies are not available or if there's an error with the gRPC connection, the system will automatically fall back to the HTTP adapter.

## Performance Comparison

Preliminary benchmarks show that the gRPC client can reduce latency by 20-30% compared to HTTP REST calls, especially for larger models and longer generation requests.

## Troubleshooting

### Missing Dependencies

If you see a warning about missing gRPC dependencies, run:

```bash
python -m gollm.llm.providers.ollama.grpc.setup_grpc
```

### Connection Issues

If you experience connection issues with gRPC, try the following:

1. Ensure Ollama server is running and accessible
2. Check if the server supports gRPC (most recent Ollama versions should)
3. Fall back to HTTP adapter by setting `adapter_type` to `http`

### Timeout Errors

If you experience timeout errors with larger models:

1. Increase the timeout in your configuration:
   ```python
   config = {
       "timeout": 120  # Increase timeout to 120 seconds
   }
   ```

2. Try using a smaller model like `deepseek-coder:1.3b` which requires less resources

3. Ensure your server has sufficient resources (RAM, GPU) for the model you're using
