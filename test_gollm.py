#!/usr/bin/env python3

import sys
import os
import subprocess

def main():
    print("Testing goLLM installation...")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    
    print("\nTrying to import gollm...")
    try:
        import gollm
        print(f"Successfully imported gollm from: {gollm.__file__}")
        
        print("\nTrying to run gollm status...")
        try:
            from gollm.cli import cli
            print("Successfully imported gollm.cli")
            
            # Run the status command
            print("\nRunning 'gollm status':")
            import sys
            sys.argv = ['gollm', 'status']
            cli()
            
        except Exception as e:
            print(f"Error running gollm status: {e}")
            
    except ImportError as e:
        print(f"Error importing gollm: {e}")
        
        # Try to find the package
        print("\nSearching for gollm in sys.path:")
        for path in sys.path:
            gollm_path = os.path.join(path, 'gollm')
            if os.path.exists(gollm_path):
                print(f"Found gollm at: {gollm_path}")
                
        print("\nInstalled packages:")
        try:
            import pkg_resources
            installed_packages = [d.project_name for d in pkg_resources.working_set]
            print("\n".join(installed_packages))
        except Exception as e:
            print(f"Error listing packages: {e}")

if __name__ == "__main__":
    main()
