#!/usr/bin/env python3
"""
Migration script for transitioning to the new Ollama provider architecture.

This script helps users migrate from the old monolithic Ollama adapter
to the new modular architecture with HTTP and gRPC support.
"""

import argparse
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("gollm.ollama.migrate")


def setup_argparse():
    """Set up argument parser.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Migrate to the new Ollama provider architecture"
    )
    parser.add_argument(
        "--rollback", action="store_true", help="Rollback the migration"
    )
    parser.add_argument(
        "--check", action="store_true", help="Check if migration is needed"
    )
    parser.add_argument(
        "--force", action="store_true", help="Force migration even if not needed"
    )
    parser.add_argument(
        "--setup-grpc",
        action="store_true",
        help="Set up gRPC dependencies and generate protobuf code",
    )

    return parser.parse_args()


def main():
    """Main function."""
    args = setup_argparse()

    # Add the parent directory to sys.path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    # Import migration utilities
    try:
        from gollm.llm.providers.ollama.migration import (apply_migration,
                                                          is_migration_needed,
                                                          rollback_migration)
    except ImportError:
        logger.error(
            "Failed to import migration utilities. Make sure you're running this script from the correct directory."
        )
        sys.exit(1)

    # Check if migration is needed
    if args.check:
        if is_migration_needed():
            print("Migration is needed.")
            sys.exit(0)
        else:
            print("Migration is not needed.")
            sys.exit(0)

    # Rollback migration if requested
    if args.rollback:
        logger.info("Rolling back migration...")
        if rollback_migration():
            logger.info("Migration rolled back successfully.")
            sys.exit(0)
        else:
            logger.error("Failed to roll back migration.")
            sys.exit(1)

    # Apply migration if needed or forced
    if is_migration_needed() or args.force:
        logger.info("Applying migration...")
        if apply_migration():
            logger.info("Migration applied successfully.")
        else:
            logger.error("Failed to apply migration.")
            sys.exit(1)
    else:
        logger.info("Migration is not needed.")

    # Set up gRPC if requested
    if args.setup_grpc:
        logger.info("Setting up gRPC...")
        try:
            # Import and run the setup_grpc script
            grpc_dir = os.path.join(current_dir, "grpc")
            sys.path.insert(0, grpc_dir)

            try:
                from setup_grpc import main as setup_grpc_main

                setup_grpc_main()
            except ImportError:
                logger.error("Failed to import setup_grpc module.")
                sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to set up gRPC: {str(e)}")
            sys.exit(1)

    logger.info("Done.")


if __name__ == "__main__":
    main()
