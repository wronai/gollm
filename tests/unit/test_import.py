#!/usr/bin/env python3

import sys
import os

def main():
    print("Python Environment Test")
    print("======================")
    print(f"Python Executable: {sys.executable}")
    print(f"Python Version: {sys.version}")
    print(f"\nPython Path:")
    for p in sys.path:
        print(f"  - {p}")
    
    print("\nTrying to import gollm...")
    try:
        import gollm
        print("Successfully imported gollm!")
        print(f"gollm module path: {gollm.__file__}")
    except ImportError as e:
        print(f"Failed to import gollm: {e}")
    except Exception as e:
        print(f"Error importing gollm: {e}")

if __name__ == "__main__":
    main()
