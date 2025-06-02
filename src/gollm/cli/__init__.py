"""Command Line Interface for GoLLM.

This module provides a modular CLI structure for GoLLM, with commands organized
into separate modules for better maintainability and extensibility.
"""

import click
import logging
import sys
from pathlib import Path

from ..main import GollmCore
from .commands.direct import direct_group
from .commands.generate import generate_command
from .commands.validate import validate_command, validate_project_command
from .commands.project import next_task_command, metrics_command, trend_command
from .commands.config import config_command, status_command

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)

@click.group()
@click.option('--config', default='gollm.json', help='Path to config file')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, config, verbose):
    """goLLM - Go Learn, Lead, Master!"""
    # Configure logging level
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.getLogger().setLevel(log_level)
    
    # Enable HTTP request logging if verbose
    if verbose:
        http_logger = logging.getLogger('aiohttp.client')
        http_logger.setLevel(logging.DEBUG)
        http_logger.propagate = True
    
    ctx.ensure_object(dict)
    ctx.obj['gollm'] = GollmCore(config)
    ctx.obj['verbose'] = verbose

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

if __name__ == '__main__':
    cli()
