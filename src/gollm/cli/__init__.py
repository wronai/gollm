"""Command Line Interface for GoLLM.

This module provides a modular CLI structure for GoLLM, with commands organized
into separate modules for better maintainability and extensibility.
"""

import logging
import sys
from pathlib import Path

import click

from ..main import GollmCore
from .commands.config import config_command, status_command
from .commands.direct import direct_group
from .commands.generate import generate_command
from .commands.project import metrics_command, next_task_command, trend_command
from .commands.validate import validate_command, validate_project_command

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)


@click.group()
@click.option("--config", default="gollm.json", help="Path to config file")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option(
    "--log-level",
    type=click.Choice(
        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False
    ),
    help="Set specific logging level",
)
@click.option("--show-prompt", is_flag=True, help="Show full prompt content in logs")
@click.option(
    "--show-response", is_flag=True, help="Show full LLM response content in logs"
)
@click.option("--show-metadata", is_flag=True, help="Show request metadata in logs")
@click.pass_context
def cli(ctx, config, verbose, log_level, show_prompt, show_response, show_metadata):
    """goLLM - Go Learn, Lead, Master!"""
    # Configure logging level
    if log_level:
        log_level = getattr(logging, log_level.upper())
    else:
        log_level = logging.DEBUG if verbose else logging.INFO

    # Configure logging format
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
        force=True,  # Override any existing configuration
    )

    # Enable HTTP request logging if verbose
    if verbose:
        http_logger = logging.getLogger("aiohttp.client")
        http_logger.setLevel(logging.DEBUG)
        http_logger.propagate = True

    ctx.ensure_object(dict)
    ctx.obj["gollm"] = GollmCore(config)
    ctx.obj["verbose"] = verbose
    ctx.obj["show_prompt"] = show_prompt
    ctx.obj["show_response"] = show_response
    ctx.obj["show_metadata"] = show_metadata


# Register commands
cli.add_command(validate_command)
cli.add_command(validate_project_command)
cli.add_command(generate_command)
cli.add_command(next_task_command)
cli.add_command(metrics_command)
cli.add_command(trend_command)
cli.add_command(config_command)
cli.add_command(status_command)

# Register command groups
cli.add_command(direct_group)

if __name__ == "__main__":
    cli()
