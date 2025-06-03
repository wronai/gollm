"""Migration utilities for transitioning to the new Ollama provider architecture.

This module provides utilities to help migrate from the old monolithic
Ollama adapter to the new modular architecture with HTTP and gRPC support.
"""

import logging
import os
import shutil
from typing import Any, Dict, Optional

from .config import OllamaConfig

logger = logging.getLogger("gollm.ollama.migration")


def migrate_config(old_config: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate an old configuration to the new format.

    Args:
        old_config: Old configuration dictionary

    Returns:
        Updated configuration dictionary compatible with the new architecture
    """
    # Start with a copy of the old config
    new_config = old_config.copy()

    # Map old keys to new keys
    key_mapping = {
        "ollama_url": "base_url",
        "ollama_model": "model",
        "ollama_timeout": "timeout",
        "ollama_max_tokens": "max_tokens",
        "ollama_temperature": "temperature",
    }

    # Update keys based on mapping
    for old_key, new_key in key_mapping.items():
        if old_key in new_config:
            if new_key not in new_config:
                new_config[new_key] = new_config.pop(old_key)

    # Add new configuration options with defaults
    if "adapter_type" not in new_config:
        new_config["adapter_type"] = "http"

    if "use_grpc" not in new_config:
        # Default to False to maintain backward compatibility
        new_config["use_grpc"] = False

    # Ensure API type is set (chat or generate)
    if "api_type" not in new_config:
        new_config["api_type"] = "chat"  # Default to chat API

    return new_config


def create_ollama_config(config_dict: Dict[str, Any]) -> OllamaConfig:
    """Create an OllamaConfig from a configuration dictionary.

    Args:
        config_dict: Configuration dictionary

    Returns:
        OllamaConfig instance
    """
    # Migrate the configuration if needed
    migrated_config = migrate_config(config_dict)

    # Create and return the config object
    return OllamaConfig.from_dict(migrated_config)


def backup_old_files():
    """Create backups of old files before replacing them.

    Returns:
        True if backup was successful, False otherwise
    """
    try:
        # Get the base directory
        base_dir = os.path.dirname(os.path.abspath(__file__))

        # Files to backup
        files_to_backup = [
            os.path.join(base_dir, "provider.py"),
            os.path.join(base_dir, "adapter.py"),
            os.path.join(base_dir, "__init__.py"),
        ]

        # Create backups
        for file_path in files_to_backup:
            if os.path.exists(file_path):
                backup_path = f"{file_path}.bak"
                shutil.copy2(file_path, backup_path)
                logger.info(f"Created backup of {file_path} at {backup_path}")

        return True
    except Exception as e:
        logger.error(f"Failed to create backups: {str(e)}")
        return False


def apply_migration():
    """Apply the migration by replacing old files with new ones.

    Returns:
        True if migration was successful, False otherwise
    """
    try:
        # Backup old files first
        if not backup_old_files():
            logger.error("Failed to create backups, aborting migration")
            return False

        # Get the base directory
        base_dir = os.path.dirname(os.path.abspath(__file__))

        # Files to replace
        files_to_replace = [
            ("provider_new.py", "provider.py"),
            ("init_new.py", "__init__.py"),
        ]

        # Replace files
        for source, target in files_to_replace:
            source_path = os.path.join(base_dir, source)
            target_path = os.path.join(base_dir, target)

            if os.path.exists(source_path):
                shutil.copy2(source_path, target_path)
                logger.info(f"Replaced {target_path} with {source_path}")
            else:
                logger.warning(f"Source file {source_path} not found")

        # Remove old adapter.py as it's now replaced by the http and grpc modules
        adapter_path = os.path.join(base_dir, "adapter.py")
        if os.path.exists(adapter_path):
            # We already have a backup, so we can safely remove it
            os.remove(adapter_path)
            logger.info(
                f"Removed {adapter_path} (replaced by http/adapter.py and grpc/adapter.py)"
            )

        return True
    except Exception as e:
        logger.error(f"Failed to apply migration: {str(e)}")
        return False


def rollback_migration():
    """Rollback the migration by restoring backup files.

    Returns:
        True if rollback was successful, False otherwise
    """
    try:
        # Get the base directory
        base_dir = os.path.dirname(os.path.abspath(__file__))

        # Files to restore
        files_to_restore = [
            "provider.py",
            "adapter.py",
            "__init__.py",
        ]

        # Restore backups
        for file_name in files_to_restore:
            file_path = os.path.join(base_dir, file_name)
            backup_path = f"{file_path}.bak"

            if os.path.exists(backup_path):
                shutil.copy2(backup_path, file_path)
                logger.info(f"Restored {file_path} from {backup_path}")
            else:
                logger.warning(f"Backup file {backup_path} not found")

        return True
    except Exception as e:
        logger.error(f"Failed to rollback migration: {str(e)}")
        return False


def is_migration_needed() -> bool:
    """Check if migration is needed.

    Returns:
        True if migration is needed, False otherwise
    """
    # Get the base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Check if new directories exist
    http_dir = os.path.join(base_dir, "http")
    grpc_dir = os.path.join(base_dir, "grpc")

    # If both directories exist but old adapter.py still exists, migration is needed
    adapter_path = os.path.join(base_dir, "adapter.py")

    return (
        os.path.exists(http_dir)
        and os.path.exists(grpc_dir)
        and os.path.exists(adapter_path)
    )
