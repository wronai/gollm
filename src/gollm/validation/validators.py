# src/gollm/validation/validators.py
import ast
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..config.config import GollmConfig, ValidationRules

@dataclass
class Violation:
    type: str
    message: str
    file_path: str
    line_number: int
    severity: str = "error"
    suggested_fix: Optional[str] = None

class CodeValidator:
    def __init__(self, config: GollmConfig):
        self.config = config
        self.rules = ValidationRules(config.validation_rules)
    
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """Waliduje pojedynczy plik Python"""
        path = Path(file_path)
        
        if not path.exists():
            return {"violations": [Violation(
                type="file_not_found",
                message=f"File {file_path} not found",
                file_path=file_path,
                line_number=0
            )]}
        
        if path.suffix != '.py':
            return {"violations": []}
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            violations = []
            violations.extend(self._validate_content(content, file_path))
            violations.extend(self._validate_ast(content, file_path))
            
            result = {
                "file_path": file_path,
                "violations": violations,
                "lines_count": len(content.splitlines()),
                "quality_score": self._calculate_quality_score(violations),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Record metrics if metrics_tracker is available
            if hasattr(self, 'metrics_tracker'):
                self.metrics_tracker.record_metrics({
                    'quality_score': result['quality_score'],
                    'violations_count': len(violations),
                    'file': file_path,
                    'timestamp': result['timestamp']
                })
            
            return result
            
        except Exception as e:
            return {"violations": [Violation(
                type="parse_error",
                message=f"Error parsing file: {str(e)}",
                file_path=file_path,
                line_number=0
            )]}
    
    def validate_project(self) -> Dict[str, Any]:
        """Waliduje wszystkie pliki Python w projekcie"""
        project_root = Path(self.config.project_root)
        python_files = list(project_root.rglob("*.py"))
        
        results = {}
        total_violations = 0
        
        for py_file in python_files:
            # Pomijaj pliki w katalogach .git, __pycache__, etc.
            if any(part.startswith('.') or part == '__pycache__' 
                   for part in py_file.parts):
                continue
            
            file_result = self.validate_file(str(py_file))
            results[str(py_file)] = file_result
            total_violations += len(file_result['violations'])
        
        return {
            "files": results,
            "total_violations": total_violations,
            "files_count": len(results),
            "overall_quality_score": self._calculate_project_quality_score(results)
        }
    
    def _validate_content(self, content: str, file_path: str) -> List[Violation]:
        """Waliduje zawartość pliku bez parsowania AST"""
        violations = []
        lines = content.splitlines()
        
        # Sprawdź długość pliku
        if len(lines) > self.config.validation_rules.max_file_lines:
            violations.append(Violation(
                type="file_too_long",
                message=f"File has {len(lines)} lines (max: {self.config.validation_rules.max_file_lines})",
                file_path=file_path,
                line_number=len(lines),
                suggested_fix="Consider splitting into smaller modules"
            ))
        
        # Sprawdź print statements
        if self.config.validation_rules.forbid_print_statements:
            for i, line in enumerate(lines, 1):
                if re.search(r'\bprint\s*\(', line.strip()):
                    violations.append(Violation(
                        type="forbidden_print",
                        message="Print statement found",
                        file_path=file_path,
                        line_number=i,
                        suggested_fix="Use logging instead of print"
                    ))
        
        return violations
    
    def _validate_ast(self, content: str, file_path: str) -> List[Violation]:
        """Waliduje kod używając AST"""
        violations = []
        
        try:
            tree = ast.parse(content)
            visitor = ASTValidator(self.config, file_path)
            visitor.visit(tree)
            violations.extend(visitor.violations)
        except SyntaxError as e:
            violations.append(Violation(
                type="syntax_error",
                message=f"Syntax error: {e.msg}",
                file_path=file_path,
                line_number=e.lineno or 0
            ))
        
        return violations
    
    def _calculate_quality_score(self, violations: List[Violation]) -> int:
        """Oblicza ocenę jakości kodu (0-100)"""
        if not violations:
            return 100
        
        penalty = 0
        for violation in violations:
            if violation.severity == "critical":
                penalty += 20
            elif violation.severity == "error":
                penalty += 10
            elif violation.severity == "warning":
                penalty += 5
            else:
                penalty += 2
        
        return max(0, 100 - penalty)
    
    def _calculate_project_quality_score(self, results: Dict[str, Any]) -> int:
        """Oblicza ogólną ocenę jakości projektu"""
        if not results:
            return 100
        
        scores = [result.get('quality_score', 0) for result in results.values()]
        return sum(scores) // len(scores) if scores else 0

class ASTValidator(ast.NodeVisitor):
    def __init__(self, config: GollmConfig, file_path: str):
        self.config = config
        self.file_path = file_path
        self.violations = []
        self.current_function = None
        self.global_vars = []
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Waliduje definicje funkcji"""
        self.current_function = node
        
        # Sprawdź długość funkcji
        function_lines = node.end_lineno - node.lineno + 1
        if function_lines > self.config.validation_rules.max_function_lines:
            self.violations.append(Violation(
                type="function_too_long",
                message=f"Function '{node.name}' has {function_lines} lines (max: {self.config.validation_rules.max_function_lines})",
                file_path=self.file_path,
                line_number=node.lineno,
                suggested_fix="Consider breaking into smaller functions"
            ))
        
        # Sprawdź liczbę parametrów
        param_count = len(node.args.args)
        if param_count > self.config.validation_rules.max_function_params:
            self.violations.append(Violation(
                type="too_many_parameters",
                message=f"Function '{node.name}' has {param_count} parameters (max: {self.config.validation_rules.max_function_params})",
                file_path=self.file_path,
                line_number=node.lineno,
                suggested_fix="Consider using a dataclass or configuration object"
            ))
        
        # Sprawdź obecność docstring
        if self.config.validation_rules.require_docstrings:
            if not ast.get_docstring(node):
                self.violations.append(Violation(
                    type="missing_docstring",
                    message=f"Function '{node.name}' is missing docstring",
                    file_path=self.file_path,
                    line_number=node.lineno,
                    severity="warning",
                    suggested_fix="Add docstring describing function purpose and parameters"
                ))
        
        # Sprawdź złożoność cyklomatyczną
        complexity = self._calculate_complexity(node)
        if complexity > self.config.validation_rules.max_cyclomatic_complexity:
            self.violations.append(Violation(
                type="high_complexity",
                message=f"Function '{node.name}' has complexity {complexity} (max: {self.config.validation_rules.max_cyclomatic_complexity})",
                file_path=self.file_path,
                line_number=node.lineno,
                severity="error",
                suggested_fix="Simplify function logic or extract sub-functions"
            ))
        
        self.generic_visit(node)
        self.current_function = None
    
    def visit_Global(self, node: ast.Global):
        """Sprawdza użycie globalnych zmiennych"""
        if self.config.validation_rules.forbid_global_variables:
            for name in node.names:
                self.violations.append(Violation(
                    type="forbidden_global",
                    message=f"Global variable '{name}' is not allowed",
                    file_path=self.file_path,
                    line_number=node.lineno,
                    suggested_fix="Use class attributes or pass as parameters"
                ))
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Oblicza złożoność cyklomatyczną funkcji"""
        complexity = 1  # Podstawowa ścieżka
        
        for child in ast.walk(node):
            # Każda decyzja zwiększa złożoność
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # And/Or dodają dodatkowe ścieżki
                complexity += len(child.values) - 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
        
        return complexity
