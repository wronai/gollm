
# src/gollm/validation/rules.py
from dataclasses import dataclass
from typing import Dict, Any, Callable
from ..config.config import ValidationRules as ConfigRules

class ValidationRules:
    """Centralne miejsce dla wszystkich reguł walidacji"""
    
    def __init__(self, config_rules: ConfigRules):
        self.config = config_rules
        self.rules = self._build_rules_registry()
    
    def _build_rules_registry(self) -> Dict[str, Callable]:
        """Buduje rejestr wszystkich dostępnych reguł"""
        return {
            "max_function_lines": self._check_function_length,
            "max_file_lines": self._check_file_length,
            "forbid_print_statements": self._check_print_statements,
            "require_docstrings": self._check_docstrings,
            "max_function_params": self._check_parameter_count,
            "max_cyclomatic_complexity": self._check_complexity,
            "forbid_global_variables": self._check_global_variables,
            "naming_convention": self._check_naming_convention
        }
    
    def get_rule(self, rule_name: str) -> Callable:
        """Pobiera funkcję walidacyjną dla danej reguły"""
        return self.rules.get(rule_name)
    
    def _check_function_length(self, node, context):
        """Sprawdza długość funkcji"""
        # Implementacja w ASTValidator
        pass
    
    def _check_file_length(self, content, context):
        """Sprawdza długość pliku"""
        # Implementacja w CodeValidator
        pass
    
    # ... inne implementacje reguł
