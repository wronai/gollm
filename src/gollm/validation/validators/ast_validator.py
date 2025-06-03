"""AST validator module.

This module provides AST-based validation for Python code.
"""

import ast
from typing import List, Optional

from ...config.config import GollmConfig
from ...validation.common import Violation


class ASTValidator(ast.NodeVisitor):
    """AST-based validator for Python code.
    
    This class traverses the AST of Python code to detect violations
    of coding standards and best practices.
    """
    
    def __init__(self, config: GollmConfig, file_path: str):
        self.config = config
        self.file_path = file_path
        self.violations = []
        self.current_function = None
        self.global_vars = []
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Validates function definitions.
        
        Args:
            node: AST node for function definition
        """
        prev_function = self.current_function
        self.current_function = node.name
        
        # Check function length
        if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
            func_lines = node.end_lineno - node.lineno
            if func_lines > self.config.validation_rules.max_function_lines:
                self.violations.append(Violation(
                    type="function_too_long",
                    message=f"Function '{node.name}' has {func_lines} lines, maximum allowed is {self.config.validation_rules.max_function_lines}",
                    file_path=self.file_path,
                    line_number=node.lineno,
                    severity="warning",
                    suggested_fix="Consider breaking this function into smaller functions"
                ))
        
        # Check function complexity
        complexity = self._calculate_complexity(node)
        if complexity > self.config.validation_rules.max_complexity:
            self.violations.append(Violation(
                type="function_too_complex",
                message=f"Function '{node.name}' has cyclomatic complexity of {complexity}, maximum allowed is {self.config.validation_rules.max_complexity}",
                file_path=self.file_path,
                line_number=node.lineno,
                severity="warning",
                suggested_fix="Consider simplifying this function or breaking it into smaller parts"
            ))
        
        # Visit function body
        self.generic_visit(node)
        self.current_function = prev_function
    
    def visit_Global(self, node: ast.Global):
        """Checks usage of global variables.
        
        Args:
            node: AST node for global statement
        """
        for name in node.names:
            self.global_vars.append(name)
            if self.config.validation_rules.forbid_globals:
                self.violations.append(Violation(
                    type="global_usage",
                    message=f"Global variable '{name}' used in function '{self.current_function}'",
                    file_path=self.file_path,
                    line_number=node.lineno,
                    severity="warning",
                    suggested_fix="Consider using function parameters or class attributes instead of globals"
                ))
        
        self.generic_visit(node)
    
    def visit_Try(self, node: ast.Try):
        """Checks exception handling.
        
        Args:
            node: AST node for try statement
        """
        for handler in node.handlers:
            if handler.type is None and self.config.validation_rules.forbid_bare_except:
                self.violations.append(Violation(
                    type="bare_except",
                    message="Bare 'except:' clause used",
                    file_path=self.file_path,
                    line_number=handler.lineno,
                    severity="warning",
                    suggested_fix="Specify the exception type(s) to catch"
                ))
        
        self.generic_visit(node)
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculates cyclomatic complexity of a function.
        
        Args:
            node: AST node for function definition
            
        Returns:
            Cyclomatic complexity score
        """
        class ComplexityVisitor(ast.NodeVisitor):
            def __init__(self):
                self.complexity = 1  # Start with 1 for the function itself
            
            def visit_If(self, node):
                self.complexity += 1
                self.generic_visit(node)
            
            def visit_For(self, node):
                self.complexity += 1
                self.generic_visit(node)
            
            def visit_While(self, node):
                self.complexity += 1
                self.generic_visit(node)
            
            def visit_And(self, node):
                self.complexity += len(node.values) - 1
                self.generic_visit(node)
            
            def visit_Or(self, node):
                self.complexity += len(node.values) - 1
                self.generic_visit(node)
            
            def visit_BoolOp(self, node):
                self.complexity += len(node.values) - 1
                self.generic_visit(node)
            
            def visit_BinOp(self, node):
                # Only count boolean operations
                if isinstance(node.op, (ast.And, ast.Or)):
                    self.complexity += 1
                self.generic_visit(node)
            
            def visit_Call(self, node):
                # Check for exception-raising calls
                if isinstance(node.func, ast.Name) and node.func.id == 'raise':
                    self.complexity += 1
                self.generic_visit(node)
            
            def visit_Raise(self, node):
                self.complexity += 1
                self.generic_visit(node)
            
            def visit_Try(self, node):
                # Add 1 for try and 1 for each except handler
                self.complexity += 1 + len(node.handlers)
                self.generic_visit(node)
            
            def visit_ExceptHandler(self, node):
                self.complexity += 1
                self.generic_visit(node)
        
        visitor = ComplexityVisitor()
        visitor.visit(node)
        return visitor.complexity
