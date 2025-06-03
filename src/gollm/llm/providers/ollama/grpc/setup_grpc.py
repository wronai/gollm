#!/usr/bin/env python3
"""
Setup script for gRPC dependencies and code generation.

This script installs the required dependencies for gRPC and generates
the Python code from the protobuf definitions.
"""

import os
import subprocess
import sys


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import grpc
        import grpc_tools

        return True
    except ImportError:
        return False


def install_dependencies():
    """Install required dependencies for gRPC."""
    print("Installing gRPC dependencies...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "grpcio", "grpcio-tools", "protobuf"],
        check=True,
    )
    print("Dependencies installed successfully.")


def generate_protos():
    """Generate Python code from protobuf definitions."""
    # Import the generate_protos function from generate_protos.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(current_dir)

    try:
        from generate_protos import generate_protos as gen_protos

        gen_protos()
        print("Proto files generated successfully.")
    except Exception as e:
        print(f"Error generating proto files: {str(e)}")
        return False

    return True


def main():
    """Main function to set up gRPC."""
    print("Setting up gRPC for Ollama...")

    # Check if dependencies are installed
    if not check_dependencies():
        print("Required dependencies not found.")
        install_dependencies()

    # Generate proto files
    if generate_protos():
        print("\ngRPC setup completed successfully!")
        print(
            "You can now use the OllamaGrpcAdapter for faster communication with Ollama."
        )
        print("\nExample usage in your config:")
        print("    'adapter_type': 'grpc'")
        print("    or")
        print("    'use_grpc': True")
    else:
        print("\nFailed to set up gRPC. Please check the errors above.")


if __name__ == "__main__":
    main()
