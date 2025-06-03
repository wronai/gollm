"""Validation commands for GoLLM CLI."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import click

from ..utils.formatting import format_violations

logger = logging.getLogger("gollm.commands.validate")


@click.command("validate")
@click.argument("file_path")
@click.pass_context
def validate_command(ctx, file_path):
    """Validate a single file.

    Checks the file for code quality issues, style violations, and other problems.

    Example: gollm validate src/my_file.py
    """
    gollm = ctx.obj["gollm"]
    result = gollm.validate_file(file_path)

    if result["violations"]:
        click.echo(f"u274c Found {len(result['violations'])} violations in {file_path}")
        for violation in result["violations"]:
            click.echo(f"  - {violation['type']}: {violation['message']}")
    else:
        click.echo(f"u2705 No violations found in {file_path}")


@click.command("validate-project")
@click.option("--staged-only", is_flag=True, help="Only validate files staged in git")
@click.pass_context
def validate_project_command(ctx, staged_only=False):
    """Validate entire project.

    Recursively checks all files in the project for code quality issues,
    style violations, and other problems.

    Example: gollm validate-project
    """
    gollm = ctx.obj["gollm"]
    result = gollm.validate_project(staged_only=staged_only)

    total_violations = sum(
        len(file_result["violations"]) for file_result in result["files"].values()
    )

    if total_violations > 0:
        click.echo(f"u274c Found {total_violations} violations across project")

        # Group by file
        for file_path, file_result in result["files"].items():
            if file_result["violations"]:
                click.echo(f"\nud83dudcc4 {file_path}:")
                click.echo(format_violations(file_result["violations"]))
    else:
        click.echo("u2705 No violations found in project")
