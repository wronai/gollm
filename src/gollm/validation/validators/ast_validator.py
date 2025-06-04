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

        # Initialize rules if not already done
        if not hasattr(self, 'rules'):
            from ..rules import ValidationRules
            self.rules = ValidationRules(self.config.validation_rules)
            
        # Check naming convention
        if self.config.validation_rules.enforce_naming_conventions:
            naming_checker = getattr(self.rules, '_check_naming_convention', None)
            if naming_checker and callable(naming_checker):
                violations = naming_checker(node, {})
                for violation in violations:
                    self.violations.append(
                        Violation(
                            type=violation['type'],
                            message=violation['message'],
                            file_path=self.file_path,
                            line_number=violation.get('line_number', node.lineno),
                            severity=violation.get('severity', 'info'),
                            suggested_fix=violation.get('suggested_fix')
                        )
                    )

        # Check function length
        if hasattr(node, "end_lineno") and hasattr(node, "lineno"):
            func_lines = node.end_lineno - node.lineno
            if func_lines > self.config.validation_rules.max_function_lines:
                self.violations.append(
                    Violation(
                        type="function_too_long",
                        message=f"Function '{node.name}' has {func_lines} lines, maximum allowed is {self.config.validation_rules.max_function_lines}",
                        file_path=self.file_path,
                        line_number=node.lineno,
                        severity="warning",
                        suggested_fix="Consider breaking this function into smaller functions",
                    )
                )

        # Check function complexity using the rules engine
        complexity_checker = getattr(self.rules, '_check_complexity', None)
        if complexity_checker and callable(complexity_checker):
            violations = complexity_checker(node, {})
            for violation in violations:
                self.violations.append(
                    Violation(
                        type=violation['type'],
                        message=violation['message'],
                        file_path=self.file_path,
                        line_number=violation.get('line_number', node.lineno),
                        severity=violation.get('severity', 'warning'),
                        suggested_fix=violation.get('suggested_fix')
                    )
                )
            
        # Check parameter count
        param_checker = getattr(self.rules, '_check_parameter_count', None)
        if param_checker and callable(param_checker):
            violations = param_checker(node, {})
            for violation in violations:
                self.violations.append(
                    Violation(
                        type=violation['type'],
                        message=violation['message'],
                        file_path=self.file_path,
                        line_number=violation.get('line_number', node.lineno),
                        severity=violation.get('severity', 'warning'),
                        suggested_fix=violation.get('suggested_fix')
                    )
                )
                
        # Check docstrings if required
        if self.config.validation_rules.require_docstrings:
            docstring_checker = getattr(self.rules, '_check_docstrings', None)
            if docstring_checker and callable(docstring_checker):
                violations = docstring_checker(node, {})
                for violation in violations:
                    self.violations.append(
                        Violation(
                            type=violation['type'],
                            message=violation['message'],
                            file_path=self.file_path,
                            line_number=violation.get('line_number', node.lineno),
                            severity=violation.get('severity', 'info'),
                            suggested_fix=violation.get('suggested_fix')
                        )
                    )

        # Visit function body
        self.generic_visit(node)
        self.current_function = prev_function

    def visit_ClassDef(self, node: ast.ClassDef):
        """Validates class definitions.

        Args:
            node: AST node for class definition
        """
        # Check naming convention for class
        if self.config.validation_rules.enforce_naming_conventions and hasattr(self, 'rules'):
            naming_checker = getattr(self.rules, '_check_naming_convention', None)
            if naming_checker and callable(naming_checker):
                violations = naming_checker(node, {})
                for violation in violations:
                    self.violations.append(
                        Violation(
                            type=violation['type'],
                            message=violation['message'],
                            file_path=self.file_path,
                            line_number=violation.get('line_number', node.lineno),
                            severity=violation.get('severity', 'info'),
                            suggested_fix=violation.get('suggested_fix')
                        )
                    )
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        """Validates name nodes.

        Args:
            node: AST node for a name
        """
        # Check naming convention for variables
        if (self.config.validation_rules.enforce_naming_conventions and 
            hasattr(self, 'rules') and 
            isinstance(node.ctx, ast.Store)):
            
            naming_checker = getattr(self.rules, '_check_naming_convention', None)
            if naming_checker and callable(naming_checker):
                violations = naming_checker(node, {})
                for violation in violations:
                    self.violations.append(
                        Violation(
                            type=violation['type'],
                            message=violation['message'],
                            file_path=self.file_path,
                            line_number=violation.get('line_number', node.lineno),
                            severity=violation.get('severity', 'info'),
                            suggested_fix=violation.get('suggested_fix')
                        )
                    )
        
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global):
        """Checks usage of global variables.

        Args:
            node: AST node for global statement
        """
        for name in node.names:
            self.global_vars.append(name)
            if self.config.validation_rules.forbid_globals:
                self.violations.append(
                    Violation(
                        type="global_usage",
                        message=f"Global variable '{name}' used in function '{self.current_function}'",
                        file_path=self.file_path,
                        line_number=node.lineno,
                        severity="warning",
                        suggested_fix="Consider using function parameters or class attributes instead of globals",
                    )
                )

        self.generic_visit(node)

    def visit_Try(self, node: ast.Try):
        """Checks exception handling.

        Args:
            node: AST node for try statement
        """
        for handler in node.handlers:
            if handler.type is None and self.config.validation_rules.forbid_bare_except:
                self.violations.append(
                    Violation(
                        type="bare_except",
                        message="Bare 'except:' clause used",
                        file_path=self.file_path,
                        line_number=handler.lineno,
                        severity="warning",
                        suggested_fix="Specify the exception type(s) to catch",
                    )
                )

        self.generic_visit(node)

    def visit_Global(self, node):
        """Checks for global variable declarations."""
        if self.config.validation_rules.forbid_global_variables:
            # Use the global variables checker from rules
            global_checker = getattr(self.rules, '_check_global_variables', None)
            if global_checker and callable(global_checker):
                violations = global_checker(node, {})
                for violation in violations:
                    self.violations.append(
                        Violation(
                            type=violation['type'],
                            message=violation['message'],
                            file_path=self.file_path,
                            line_number=violation.get('line_number', node.lineno),
                            severity=violation.get('severity', 'warning'),
                            suggested_fix=violation.get('suggested_fix')
                        )
                    )
        self.generic_visit(node)
        
    def visit_Print(self, node):
        """Checks for print statements."""
        if self.config.validation_rules.forbid_print_statements:
            # Use the print statement checker from rules
            print_checker = getattr(self.rules, '_check_print_statements', None)
            if print_checker and callable(print_checker):
                violations = print_checker(node, {})
                for violation in violations:
                    self.violations.append(
                        Violation(
                            type=violation['type'],
                            message=violation['message'],
                            file_path=self.file_path,
                            line_number=violation.get('line_number', node.lineno),
                            severity=violation.get('severity', 'warning'),
                            suggested_fix=violation.get('suggested_fix')
                        )
                    )
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
                if isinstance(node.func, ast.Name) and node.func.id == "raise":
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
