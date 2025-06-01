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
        # Handle the case where providers might be passed from config
        if self.providers is None:
            self.providers = {}

@dataclass
class GollmConfig:
    validation_rules: ValidationRules
    project_management: ProjectManagement
    llm_integration: LLMIntegration
    project_root: str = "."
    
    @classmethod
    def load(cls, config_path: str = "gollm.json") -> "GollmConfig":
        """Ładuje konfigurację z pliku JSON"""
        config_file = Path(config_path)
        
        if not config_file.exists():
            # Utwórz domyślną konfigurację
            default_config = cls.default()
            default_config.save(config_path)
            return default_config
        
        with open(config_file, 'r') as f:
            data = json.load(f)
        
        return cls(
            validation_rules=ValidationRules(**data.get('validation_rules', {})),
            project_management=ProjectManagement(**data.get('project_management', {})),
            llm_integration=LLMIntegration(**data.get('llm_integration', {})),
            project_root=data.get('project_root', '.')
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
