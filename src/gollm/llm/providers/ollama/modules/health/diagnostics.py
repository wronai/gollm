"""Diagnostics collection module for Ollama adapter."""

import json
import logging
import os
import platform
import sys
import time
from typing import Dict, Any, List, Optional

logger = logging.getLogger('gollm.ollama.health')

class DiagnosticsCollector:
    """Collects diagnostic information about the Ollama setup and environment."""
    
    def __init__(self, config: Dict[str, Any], client=None):
        """Initialize the diagnostics collector.
        
        Args:
            config: Configuration dictionary
            client: Optional HTTP client for making API requests
        """
        self.config = config
        self.client = client
        
    def collect_system_info(self) -> Dict[str, Any]:
        """Collect information about the system environment.
        
        Returns:
            Dictionary containing system information
        """
        system_info = {
            'platform': platform.platform(),
            'python_version': sys.version,
            'timestamp': time.time(),
            'cpu_count': os.cpu_count()
        }
        
        # Add environment variables (excluding sensitive ones)
        env_vars = {}
        for key, value in os.environ.items():
            # Skip sensitive environment variables
            if any(sensitive in key.lower() for sensitive in ['key', 'token', 'secret', 'password', 'auth']):
                continue
            env_vars[key] = value
            
        system_info['environment'] = env_vars
        
        return system_info
        
    def collect_config_info(self) -> Dict[str, Any]:
        """Collect information about the current configuration.
        
        Returns:
            Dictionary containing configuration information
        """
        # Create a sanitized copy of the config (removing sensitive information)
        sanitized_config = {}
        
        for key, value in self.config.items():
            # Skip sensitive config values
            if any(sensitive in key.lower() for sensitive in ['key', 'token', 'secret', 'password', 'auth']):
                sanitized_config[key] = '***REDACTED***'
            else:
                sanitized_config[key] = value
                
        return {
            'config': sanitized_config,
            'timestamp': time.time()
        }
        
    async def collect_api_info(self) -> Dict[str, Any]:
        """Collect information about the Ollama API.
        
        Returns:
            Dictionary containing API information
        """
        if not self.client:
            return {'error': 'No client available for API diagnostics'}
            
        api_info = {
            'base_url': self.client.config.base_url,
            'timestamp': time.time()
        }
        
        try:
            # Try to get version information
            version_info = await self.client._request('GET', '/api/version')
            api_info['version'] = version_info
            
            # Try to get model list
            models_info = await self.client._request('GET', '/api/tags')
            
            # Sanitize model information to avoid excessive data
            if 'models' in models_info:
                api_info['models_count'] = len(models_info['models'])
                api_info['models'] = [
                    {
                        'name': model.get('name', 'unknown'),
                        'size': model.get('size', 0),
                        'modified_at': model.get('modified_at', '')
                    }
                    for model in models_info.get('models', [])
                ]
                
        except Exception as e:
            api_info['error'] = str(e)
            
        return api_info
        
    async def collect_all_diagnostics(self) -> Dict[str, Any]:
        """Collect all available diagnostic information.
        
        Returns:
            Dictionary containing all diagnostic information
        """
        diagnostics = {
            'system': self.collect_system_info(),
            'config': self.collect_config_info(),
            'timestamp': time.time()
        }
        
        if self.client:
            diagnostics['api'] = await self.collect_api_info()
            
        logger.info("Collected diagnostics information")
        
        return diagnostics
        
    def save_diagnostics(self, path: str, diagnostics: Optional[Dict[str, Any]] = None) -> str:
        """Save diagnostics information to a file.
        
        Args:
            path: Directory to save the diagnostics file
            diagnostics: Optional diagnostics data (if not provided, will collect it)
            
        Returns:
            Path to the saved diagnostics file
        """
        os.makedirs(path, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"ollama_diagnostics_{timestamp}.json"
        filepath = os.path.join(path, filename)
        
        # Use provided diagnostics or collect them
        if diagnostics is None:
            import asyncio
            diagnostics = asyncio.run(self.collect_all_diagnostics())
            
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(diagnostics, f, indent=2)
            
        logger.info(f"Saved diagnostics to {filepath}")
        
        return filepath
