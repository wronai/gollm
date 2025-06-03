# src/gollm/config/config.py
import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any

@dataclass
class ValidationRules:
    max_function_lines: int = 50
    max_file_lines: int = 300
    max_cyclomatic_complexity: int = 10
    max_line_length: int = 88
    forbid_print_statements: bool = True
    forbid_global_variables: bool = True
    require_docstrings: bool = True
    require_type_hints: bool = False
    max_function_params: int = 5
    naming_convention: str = "snake_case"

@dataclass
class ProjectManagement:
    todo_integration: bool = True
    auto_create_tasks: bool = True
    todo_file: str = "TODO.md"
    changelog_integration: bool = True
    auto_update_changelog: bool = True
    changelog_file: str = "CHANGELOG.md"
    
@dataclass
class LLMIntegration:
    enabled: bool = True
    model_name: str = "gpt-4"
    max_iterations: int = 3
    token_limit: int = 4000
    auto_fix_attempts: int = 2
    api_provider: str = "openai"
    providers: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        # Initialize providers if None
        if self.providers is None:
            self.providers = {}
        
        # Convert providers to dict if it's not already
        if not isinstance(self.providers, dict):
            self.providers = {}
            
        # Filter out any non-dict provider configs
        self.providers = {
            k: v for k, v in self.providers.items() 
            if isinstance(v, dict) and k in ['ollama', 'openai']
        }
        
        # Handle Ollama provider configuration
        if 'ollama' in self.providers:
            self.providers['ollama'] = {
                k: v for k, v in self.providers['ollama'].items()
                if k in ['enabled', 'model', 'base_url', 'temperature', 'max_tokens', 'timeout']
            }

@dataclass
class GollmConfig:
    validation_rules: ValidationRules
    project_management: ProjectManagement
    llm_integration: LLMIntegration
    project_root: str = "."
    debug_logging: bool = False
    
    @classmethod
    def load(cls, config_path: str = "gollm.json") -> "GollmConfig":
        """Load configuration from JSON file with environment variable support.
        
        Args:
            config_path: Path to the JSON config file
            
        Returns:
            GollmConfig: Loaded configuration with environment variables resolved
        """
        config_file = Path(config_path)
        
        # Load environment variables from .env file if it exists
        env_file = Path(".env")
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        try:
                            key, value = line.split('=', 1)
                            os.environ[key] = value.strip('\'"')
                        except ValueError:
                            continue
        
        if not config_file.exists():
            # Create default config if it doesn't exist
            default_config = cls.default()
            default_config.save(config_path)
            return default_config
        
        with open(config_file, 'r') as f:
            data = json.load(f)
        
        # Helper function to recursively resolve environment variables in config
        def resolve_env_vars(config):
            if isinstance(config, dict):
                return {k: resolve_env_vars(v) for k, v in config.items()}
            elif isinstance(config, list):
                return [resolve_env_vars(item) for item in config]
            elif isinstance(config, str) and config.startswith('${') and '}' in config:
                # Handle ${VAR:default} syntax
                var_part = config[2:].split('}')[0]  # Extract VAR:default
                if ':' in var_part:
                    var_name, default = var_part.split(':', 1)
                    return os.environ.get(var_name, default)
                else:
                    return os.environ.get(var_part, config)  # Fallback to original if not found
            return config
        
        # Resolve environment variables in the config
        data = resolve_env_vars(data)
        
        # Extract llm_integration data and ensure it's a dict
        llm_data = data.get('llm_integration', {})
        if not isinstance(llm_data, dict):
            llm_data = {}
            
        # Create LLMIntegration instance with the data
        llm_integration = LLMIntegration(
            enabled=llm_data.get('enabled', True),
            model_name=llm_data.get('model_name', 'gpt-4'),
            max_iterations=llm_data.get('max_iterations', 3),
            token_limit=llm_data.get('token_limit', 4000),
            auto_fix_attempts=llm_data.get('auto_fix_attempts', 2),
            api_provider=llm_data.get('api_provider', 'ollama'),
            providers=llm_data.get('providers')
        )
        
        return cls(
            validation_rules=ValidationRules(**data.get('validation_rules', {})),
            project_management=ProjectManagement(**data.get('project_management', {})),
            llm_integration=llm_integration,
            project_root=data.get('project_root', '.'),
            debug_logging=data.get('debug_logging', False)
        )
    
    @classmethod
    def default(cls) -> "GollmConfig":
        """Zwraca domyślną konfigurację"""
        return cls(
            validation_rules=ValidationRules(),
            project_management=ProjectManagement(),
            llm_integration=LLMIntegration()
        )
    
    def save(self, config_path: str = "gollm.json"):
        """Zapisuje konfigurację do pliku JSON"""
        with open(config_path, 'w') as f:
            json.dump(asdict(self), f, indent=2)
