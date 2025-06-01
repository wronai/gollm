#!/usr/bin/env python3

import os
import sys
import subprocess
import platform

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, check=True, 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE,
                             text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

def main():
    print("=== Environment Diagnostics ===\n")
    
    # Basic system info
    print("System Information:")
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Machine: {platform.machine()}")
    print(f"Processor: {platform.processor()}")
    print()
    
    # Python info
    print("Python Information:")
    print(f"Executable: {sys.executable}")
    print(f"Version: {sys.version}")
    print(f"Version Info: {sys.version_info}")
    print(f"Prefix: {sys.prefix}")
    print(f"Base Prefix: {sys.base_prefix}")
    print(f"Exec Prefix: {sys.exec_prefix}")
    print()
    
    # Path information
    print("Python Path:")
    for i, path in enumerate(sys.path, 1):
        print(f"  {i}. {path}")
    print()
    
    # Check for gollm package
    print("Checking for gollm package:")
    try:
        import gollm
        print(f"  Found gollm at: {gollm.__file__}")
        print(f"  Version: {getattr(gollm, '__version__', 'Not specified')}")
    except ImportError as e:
        print(f"  Could not import gollm: {e}")
    print()
    
    # Check which python
    print("Which python3:")
    print(f"  {run_command('which python3')}")
    
    # Check pip list
    print("\nInstalled packages:")
    print(run_command("pip list"))

if __name__ == "__main__":
    main()
