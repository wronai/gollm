"""Code validator module.

This module provides the main CodeValidator class for validating code quality.
"""

import ast
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...config.config import GollmConfig, ValidationRules
from ...validation.common import Violation
from .ast_validator import ASTValidator


class CodeValidator:
    """Main code validator class for validating Python code quality."""

    def __init__(self, config: GollmConfig):
        self.config = config
        self.rules = ValidationRules(config.validation_rules)

    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """Validates a single Python file.

        Args:
            file_path: Path to the file to validate

        Returns:
            Dictionary with validation results
        """
        path = Path(file_path)

        if not path.exists():
            return {
                "violations": [
                    Violation(
                        type="file_not_found",
                        message=f"File {file_path} not found",
                        file_path=file_path,
                        line_number=0,
                    )
                ]
            }

        if path.suffix != ".py":
            return {"violations": []}

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            violations = []
            violations.extend(self._validate_content(content, file_path))
            violations.extend(self._validate_ast(content, file_path))

            result = {
                "file_path": file_path,
                "violations": violations,
                "lines_count": len(content.splitlines()),
                "quality_score": self._calculate_quality_score(violations),
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Record metrics if metrics_tracker is available
            if hasattr(self, "metrics_tracker"):
                self.metrics_tracker.record_metrics(
                    {
                        "quality_score": result["quality_score"],
                        "violations_count": len(violations),
                        "file": file_path,
                        "timestamp": result["timestamp"],
                    }
                )

            return result

        except Exception as e:
            return {
                "violations": [
                    Violation(
                        type="parse_error",
                        message=f"Error parsing file: {str(e)}",
                        file_path=file_path,
                        line_number=0,
                    )
                ]
            }

    def validate_project(self, staged_only: bool = False) -> Dict[str, Any]:
        """Validates Python files in the project.

        Args:
            staged_only: If True, only validate files staged in git

        Returns:
            Dictionary with project validation results
        """
        project_root = Path(self.config.project_root)
        
        # Get all Python files or only staged files if requested
        if staged_only:
            import subprocess
            try:
                # Get list of staged files from git
                result = subprocess.run(
                    ["git", "-C", str(project_root), "diff", "--name-only", "--cached"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                staged_files = result.stdout.strip().split('\n')
                # Filter for Python files and convert to Path objects
                python_files = [
                    project_root / file for file in staged_files 
                    if file.endswith(".py") and file.strip()
                ]
            except subprocess.CalledProcessError as e:
                import logging
                logging.error(f"Failed to get staged files: {e}")
                # Fall back to all Python files if git command fails
                python_files = list(project_root.rglob("*.py"))
        else:
            # Get all Python files in the project
            python_files = list(project_root.rglob("*.py"))

        results = {}
        total_violations = 0

        for py_file in python_files:
            # Skip files in .git, __pycache__, etc.
            if any(
                part.startswith(".") or part == "__pycache__" for part in py_file.parts
            ):
                continue

            file_result = self.validate_file(str(py_file))
            results[str(py_file)] = file_result
            total_violations += len(file_result["violations"])

        return {
            "files": results,
            "total_violations": total_violations,
            "files_count": len(results),
            "overall_quality_score": self._calculate_project_quality_score(results),
        }

    def _validate_content(self, content: str, file_path: str) -> List[Violation]:
        """Validates file content without parsing AST.

        Args:
            content: File content to validate
            file_path: Path to the file

        Returns:
            List of violations
        """
        violations = []
        lines = content.splitlines()

        # Check file length
        if len(lines) > self.rules.max_file_lines:
            violations.append(
                Violation(
                    type="file_too_long",
                    message=f"File has {len(lines)} lines, maximum allowed is {self.rules.max_file_lines}",
                    file_path=file_path,
                    line_number=0,
                    severity="warning",
                )
            )

        # Check line length
        for i, line in enumerate(lines, 1):
            if len(line) > self.rules.max_line_length:
                violations.append(
                    Violation(
                        type="line_too_long",
                        message=f"Line {i} has {len(line)} characters, maximum allowed is {self.rules.max_line_length}",
                        file_path=file_path,
                        line_number=i,
                        severity="warning",
                    )
                )

        # Check for print statements
        if self.rules.forbid_print_statements:
            for i, line in enumerate(lines, 1):
                if re.search(r"\bprint\s*\(", line) and not line.strip().startswith(
                    "#"
                ):
                    violations.append(
                        Violation(
                            type="print_statement",
                            message="Print statements should be avoided in production code",
                            file_path=file_path,
                            line_number=i,
                            severity="warning",
                            suggested_fix="Use logging instead of print statements",
                        )
                    )

        return violations

    def _validate_ast(self, content: str, file_path: str) -> List[Violation]:
        """Validates file using AST parsing.

        Args:
            content: File content to validate
            file_path: Path to the file

        Returns:
            List of violations
        """
        try:
            tree = ast.parse(content)
            validator = ASTValidator(self.config, file_path)
            validator.visit(tree)
            return validator.violations
        except SyntaxError as e:
            return [
                Violation(
                    type="syntax_error",
                    message=f"Syntax error: {str(e)}",
                    file_path=file_path,
                    line_number=e.lineno if hasattr(e, "lineno") else 0,
                )
            ]
        except Exception as e:
            return [
                Violation(
                    type="ast_error",
                    message=f"Error during AST validation: {str(e)}",
                    file_path=file_path,
                    line_number=0,
                )
            ]

    def _calculate_quality_score(self, violations: List[Violation]) -> float:
        """Calculates quality score based on violations.

        Args:
            violations: List of violations to score

        Returns:
            Quality score between 0 and 100 (higher is better)
        """
        if not violations:
            return 100.0  # Perfect score for no violations

        # Weight violations by severity
        weights = {"error": 10.0, "warning": 5.0, "info": 2.0}
        
        # Calculate total penalty points
        penalty = sum(weights.get(v.severity.lower(), 3.0) for v in violations)
        
        # Cap penalty to avoid negative scores
        max_penalty = 100.0
        penalty = min(penalty, max_penalty)
        
        # Calculate score (100 is perfect, 0 is worst)
        score = max(0.0, 100.0 - penalty)
        return round(score, 2)
        
    def _calculate_project_quality_score(self, results: Dict[str, Any]) -> float:
        """Calculates overall project quality score.

        Args:
            results: Dictionary with file validation results

        Returns:
            Project quality score between 0 and 100
        """
        if not results:
            return 100.0

        file_scores = [
            result.get("quality_score", 0.0)
            for result in results.values()
            if isinstance(result, dict)
        ]

        if not file_scores:
            return 0.0

        return round(sum(file_scores) / len(file_scores), 2)
