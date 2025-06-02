#!/usr/bin/env python3
"""
Script to generate Python code from protobuf definitions.
Requires the protoc compiler and grpcio-tools to be installed.
"""

import os
import subprocess
import sys

def generate_protos():
    """Generate Python code from protobuf definitions."""
    # Get the directory of this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Run protoc to generate Python code
    proto_file = os.path.join(current_dir, 'ollama.proto')
    output_dir = current_dir
    
    cmd = [
        sys.executable, '-m', 'grpc_tools.protoc',
        f'--proto_path={current_dir}',
        f'--python_out={output_dir}',
        f'--grpc_python_out={output_dir}',
        proto_file
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=True)
    
    if result.returncode == 0:
        print("Successfully generated Python code from protobuf definitions")
        # Fix imports in generated files
        fix_imports(output_dir)
    else:
        print(f"Failed to generate Python code: {result.stderr}")

def fix_imports(output_dir):
    """Fix imports in generated Python files."""
    # The generated files have incorrect imports
    pb2_file = os.path.join(output_dir, 'ollama_pb2.py')
    pb2_grpc_file = os.path.join(output_dir, 'ollama_pb2_grpc.py')
    
    # Fix imports in the grpc file
    if os.path.exists(pb2_grpc_file):
        with open(pb2_grpc_file, 'r') as f:
            content = f.read()
        
        # Replace import statements
        content = content.replace(
            'import ollama_pb2 as ollama__pb2',
            'from . import ollama_pb2 as ollama__pb2'
        )
        
        with open(pb2_grpc_file, 'w') as f:
            f.write(content)
        
        print(f"Fixed imports in {pb2_grpc_file}")

if __name__ == '__main__':
    generate_protos()
