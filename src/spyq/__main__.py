#!/usr/bin/env python3
"""
goLLM command-line interface entry point.
This module allows the package to be run directly using `python -m gollm`.
"""

def main():
    """Run the CLI application."""
    from .cli import cli
    cli()

if __name__ == "__main__":
    main()
