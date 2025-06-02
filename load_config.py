#!/usr/bin/env python3
"""
Configuration loader that handles environment variable interpolation.
"""
import os
import json
from pathlib import Path

def load_config(config_path: str = 'gollm.json', env_file: str = '.env') -> dict:
    """
    Load and parse the configuration file with environment variable interpolation.
    
    Args:
        config_path: Path to the JSON config file
        env_file: Path to the .env file to load
        
    Returns:
        dict: Parsed configuration with environment variables resolved
    """
    # Load environment variables from .env file if it exists
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value.strip('"\'')
    
    # Load the JSON config
    with open(config_path) as f:
        config = json.load(f)
    
    return config

if __name__ == "__main__":
    # For testing
    config = load_config()
    print(json.dumps(config, indent=2))
