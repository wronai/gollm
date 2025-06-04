# src/gollm/validation/rules.py
import ast
from dataclasses import dataclass
from typing import Any, Callable, Dict

from ..config.config import ValidationRules as ConfigRules


class ValidationRules:
    """Centralne miejsce dla wszystkich reguł walidacji"""

    def __init__(self, config_rules: ConfigRules):
        self.config = config_rules
        # Add default value for enforce_naming_conventions if not present
        if not hasattr(self.config, 'enforce_naming_conventions'):
            self.config.enforce_naming_conventions = True
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
            "naming_convention": self._check_naming_convention,
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

    def _check_parameter_count(self, node, context):
        """Sprawdza liczbę parametrów funkcji.
        
        Args:
            node: Węzeł funkcji do sprawdzenia
            context: Kontekst walidacji
            
        Returns:
            Lista naruszeń lub pusta lista jeśli nie znaleziono problemów
        """
        violations = []
        
        # Handle function definition nodes
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            num_params = len(node.args.args)
            max_params = getattr(self.config, 'max_function_params', 5)
            
            if num_params > max_params:
                violations.append({
                    'type': 'too_many_parameters',
                    'message': f'Function "{node.name}" has {num_params} parameters, maximum allowed is {max_params}',
                    'line_number': getattr(node, 'lineno', 0),
                    'severity': 'warning',
                    'suggested_fix': f'Refactor the function to have {max_params} or fewer parameters'
                })
        # Handle call nodes (for checking function calls with too many arguments)
        elif isinstance(node, ast.Call) and hasattr(node, 'func') and hasattr(node, 'args'):
            num_args = len(node.args) + len([kw for kw in node.keywords if kw.arg is not None])
            max_args = getattr(self.config, 'max_function_params', 5)
            
            if num_args > max_args:
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                    
                violations.append({
                    'type': 'too_many_arguments',
                    'message': f'Function call to "{func_name}" has {num_args} arguments, maximum allowed is {max_args}',
                    'line_number': getattr(node, 'lineno', 0),
                    'severity': 'warning',
                    'suggested_fix': f'Refactor the function call to pass {max_args} or fewer arguments'
                })
            
        return violations
        
    def _check_print_statements(self, node, context):
        """Sprawdza obecność instrukcji print w kodzie.
        
        Args:
            node: Węzeł AST do sprawdzenia
            context: Kontekst walidacji
            
        Returns:
            Lista naruszeń lub pusta lista jeśli nie znaleziono problemów
        """
        violations = []
        
        # Sprawdź czy to wywołanie funkcji print
        if (isinstance(node, ast.Expr) and 
            isinstance(node.value, ast.Call) and 
            isinstance(node.value.func, ast.Name) and 
            node.value.func.id == 'print'):
            
            violations.append({
                'type': 'forbidden_print',
                'message': 'Print statements should be avoided in production code',
                'line_number': getattr(node, 'lineno', 0),
                'severity': 'warning',
                'suggested_fix': 'Use logging instead of print statements'
            })
            
        return violations
        
    def _check_docstrings(self, node, context):
        """Sprawdza czy funkcje i klasy mają docstringi.
        
        Args:
            node: Węzeł AST do sprawdzenia (FunctionDef lub ClassDef)
            context: Kontekst walikacji
            
        Returns:
            Lista naruszeń lub pusta lista jeśli nie znaleziono problemów
        """
        violations = []
        
        # Sprawdź czy to funkcja lub klasa
        if not isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            return violations
            
        # Sprawdź czy ma docstring
        if not (node.body and 
               isinstance(node.body[0], ast.Expr) and 
               isinstance(node.body[0].value, ast.Constant) and 
               isinstance(node.body[0].value.value, str)):
            
            node_type = 'Function' if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else 'Class'
            violations.append({
                'type': 'missing_docstring',
                'message': f'{node_type} "{node.name}" is missing a docstring',
                'line_number': getattr(node, 'lineno', 0),
                'severity': 'info',
                'suggested_fix': f'Add a docstring to the {node_type.lower()} {node.name}'
            })
            
        return violations
        
    def _check_naming_convention(self, node, context):
        """Sprawdza konwencje nazewnicze w kodzie.
        
        Args:
            node: Węzeł AST do sprawdzenia
            context: Kontekst walidacji
            
        Returns:
            Lista naruszeń lub pusta lista jeśli nie znaleziono problemów
        """
        violations = []
        
        # Sprawdź nazwę funkcji
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name
            if not name.islower() and not name.startswith('__'):
                violations.append({
                    'type': 'naming_convention',
                    'message': f'Function name "{name}" should be lowercase with words separated by underscores',
                    'line_number': getattr(node, 'lineno', 0),
                    'severity': 'info',
                    'suggested_fix': f'Rename the function to "{name.lower()}"'
                })
        
        # Sprawdź nazwę klasy
        elif isinstance(node, ast.ClassDef):
            name = node.name
            if not name[0].isupper() or '_' in name:
                violations.append({
                    'type': 'naming_convention',
                    'message': f'Class name "{name}" should use CamelCase',
                    'line_number': getattr(node, 'lineno', 0),
                    'severity': 'info',
                    'suggested_fix': f'Rename the class to "{name.title().replace("_", "")}"'
                })
        
        # Sprawdź nazwy zmiennych
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            name = node.id
            if not name.islower() and not name.isupper() and not name.startswith('_'):
                violations.append({
                    'type': 'naming_convention',
                    'message': f'Variable name "{name}" should be lowercase with words separated by underscores',
                    'line_number': getattr(node, 'lineno', 0),
                    'severity': 'info',
                    'suggested_fix': f'Rename the variable to "{name.lower()}"'
                })
        
        return violations
        
    def _check_global_variables(self, node, context):
        """Sprawdza użycie zmiennych globalnych w kodzie.
        
        Args:
            node: Węzeł AST do sprawdzenia
            context: Kontekst walidacji
            
        Returns:
            Lista naruszeń lub pusta lista jeśli nie znaleziono problemów
        """
        violations = []
        
        # Sprawdź czy to deklaracja global
        if isinstance(node, ast.Global):
            for name in node.names:
                violations.append({
                    'type': 'global_variable',
                    'message': f'Global variable "{name}" should be avoided',
                    'line_number': getattr(node, 'lineno', 0),
                    'severity': 'warning',
                    'suggested_fix': 'Consider passing the variable as a parameter or using a class attribute instead.'
                })
                
        # Sprawdź czy to przypisanie do zmiennej globalnej
        if (isinstance(node, ast.Assign) and 
            any(isinstance(target, ast.Name) and isinstance(target.ctx, ast.Store) 
                for target in ast.walk(node))):
            
            # Sprawdź czy to zmienna globalna (niezdefiniowana w zakresie lokalnym)
            for target in node.targets:
                if (isinstance(target, ast.Name) and 
                    isinstance(target.ctx, ast.Store) and 
                    not any(isinstance(parent, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)) 
                           for parent in ast.walk(node))):
                    
                    violations.append({
                        'type': 'global_variable',
                        'message': f'Global variable "{target.id}" should be avoided',
                        'line_number': getattr(node, 'lineno', 0),
                        'severity': 'warning',
                        'suggested_fix': 'Consider moving this variable into a function or class.'
                    })
        
        return violations
        
    def _check_complexity(self, node, context):
        """Sprawdza złożoność cyklomatyczną funkcji.
        
        Args:
            node: Węzeł funkcji do sprawdzenia
            context: Kontekst walidacji
            
        Returns:
            Lista naruszeń lub pusta lista jeśli nie znaleziono problemów
        """
        violations = []
        
        # Upewnij się, że to funkcja
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return violations
            
        # Użyj wbudowanej metody do obliczenia złożoności cyklomatycznej
        complexity = 1  # Start with 1 for the function itself
        
        # Zlicz punkty decyzyjne
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.And, ast.Or, ast.ExceptHandler, 
                                ast.With, ast.AsyncWith, ast.AsyncFor)):
                complexity += 1
                
        # Pobierz maksymalną dozwoloną złożoność z konfiguracji
        max_complexity = getattr(self.config, 'max_cyclomatic_complexity', 10)
        
        if complexity > max_complexity:
            violations.append({
                'type': 'function_too_complex',
                'message': f'Function "{node.name}" has a cyclomatic complexity of {complexity}, '
                         f'which is higher than the maximum allowed {max_complexity}',
                'line_number': getattr(node, 'lineno', 0),
                'severity': 'warning',
                'suggested_fix': 'Refactor the function to reduce its complexity by breaking it into smaller functions.'
            })
            
        return violations

