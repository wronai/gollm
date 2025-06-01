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
    
    print("\nTrying to import spyq...")
    try:
        import spyq
        print("Successfully imported spyq!")
        print(f"spyq module path: {spyq.__file__}")
    except ImportError as e:
        print(f"Failed to import spyq: {e}")
    except Exception as e:
        print(f"Error importing spyq: {e}")

if __name__ == "__main__":
    main()
