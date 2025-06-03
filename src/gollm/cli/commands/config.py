"""Configuration and status commands for GoLLM CLI."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import click

from ..utils.file_handling import load_config, save_config

logger = logging.getLogger("gollm.commands.config")


@click.command("config")
@click.option("--set", "-s", nargs=2, multiple=True, help="Set config key-value pairs")
@click.option("--get", "-g", help="Get config value for key")
@click.option("--list", "-l", "list_all", is_flag=True, help="List all config values")
@click.option("--reset", is_flag=True, help="Reset config to defaults")
@click.pass_context
def config_command(ctx, set, get, list_all, reset):
    """View or modify GoLLM configuration.

    Allows viewing and modifying configuration values.

    Examples:
      gollm config --list
      gollm config --set api_url http://localhost:11434
      gollm config --get api_url
    """
    gollm = ctx.obj["gollm"]
    config_path = gollm.config_path

    # Load current config
    config = load_config(config_path)

    # Handle reset
    if reset:
        # Default configuration
        default_config = {
            "api_url": "http://localhost:11434",
            "default_model": "deepseek-coder:1.3b",
            "timeout": 60,
            "adapter_type": "http",
            "use_grpc": False,
            "max_tokens": 1000,
            "temperature": 0.1,
        }
        save_config(config_path, default_config)
        click.echo("u2705 Configuration reset to defaults")
        return

    # Handle get
    if get:
        if get in config:
            value = config[get]
            if isinstance(value, dict):
                click.echo(json.dumps(value, indent=2))
            else:
                click.echo(value)
        else:
            click.echo(f"u26a0ufe0f Key '{get}' not found in config")
        return

    # Handle set
    if set:
        for key, value in set:
            # Try to parse as JSON if possible
            try:
                parsed_value = json.loads(value)
                config[key] = parsed_value
            except json.JSONDecodeError:
                # If not valid JSON, store as string
                config[key] = value

        save_config(config_path, config)
        click.echo("u2705 Configuration updated")
        return

    # Handle list
    if list_all or not (set or get or reset):
        click.echo("\nud83dudcd7 Current Configuration:\n")
        for key, value in sorted(config.items()):
            if isinstance(value, dict):
                click.echo(f"{key}:")
                for sub_key, sub_value in sorted(value.items()):
                    click.echo(f"  {sub_key}: {sub_value}")
            else:
                click.echo(f"{key}: {value}")


@click.command("status")
@click.pass_context
def status_command(ctx):
    """Show GoLLM status and health information.

    Displays the status of connected services, LLM providers, and system health.

    Example: gollm status
    """
    gollm = ctx.obj["gollm"]

    async def check_status():
        status = await gollm.check_status()

        click.echo("\nud83dudcca GoLLM Status:\n")

        # Overall status
        if status.get("overall_status") == "healthy":
            click.echo("u2705 Overall Status: Healthy")
        else:
            click.echo("u26a0ufe0f Overall Status: Issues Detected")

        # LLM Provider status
        click.echo("\nud83eudd16 LLM Providers:")
        for provider, provider_status in status.get("providers", {}).items():
            status_icon = (
                "u2705" if provider_status.get("available", False) else "u274c"
            )
            click.echo(
                f"  {status_icon} {provider}: {provider_status.get('status', 'Unknown')}"
            )

            # Show adapter type if available
            if "adapter_type" in provider_status:
                adapter_type = provider_status["adapter_type"]
                adapter_icon = "ud83dude80" if adapter_type == "grpc" else "ud83cudf10"
                click.echo(f"    {adapter_icon} Using {adapter_type.upper()} adapter")

            # Show models if available
            if "models" in provider_status and provider_status["models"]:
                click.echo(
                    f"    ud83dudcda Available models: {', '.join(provider_status['models'][:5])}"
                )
                if len(provider_status["models"]) > 5:
                    click.echo(
                        f"       ...and {len(provider_status['models']) - 5} more"
                    )

        # System status
        click.echo("\nud83dudcbb System:")
        click.echo(
            f"  ud83dudcbe Memory Usage: {status.get('system', {}).get('memory_usage', 'Unknown')}"
        )
        click.echo(
            f"  ud83dudd0c CPU Usage: {status.get('system', {}).get('cpu_usage', 'Unknown')}"
        )
        click.echo(
            f"  ud83dudcc2 Disk Space: {status.get('system', {}).get('disk_space', 'Unknown')}"
        )

    asyncio.run(check_status())
