#!/usr/bin/env python3
"""
Migration script to help transition from the old monolithic structure
to the new modular structure in GoLLM.

This script performs the following tasks:
1. Updates imports in existing files to use the new module structure
2. Migrates any existing TODO.md files to the new format
3. Provides information about the changes made
"""

import os
import re
import sys
import shutil
from pathlib import Path

# Add the src directory to the path so we can import gollm
src_dir = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_dir))

from gollm.project_management.todo.parser import parse_todo_file
from gollm.project_management.todo.storage import save_tasks_to_markdown


def update_imports(file_path):
    """Update imports in a file to use the new module structure.
    
    Args:
        file_path: Path to the file to update
        
    Returns:
        True if changes were made, False otherwise
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Define import replacements
    replacements = [
        # CLI imports
        (r'from gollm\.cli import', r'from gollm.cli.commands import'),
        # Todo imports
        (r'from gollm\.project_management\.todo_manager import (.*)', r'from gollm.project_management.todo import \1'),
        # Ollama adapter imports
        (r'from gollm\.llm\.ollama_adapter import', r'from gollm.llm.providers.ollama.adapter import'),
    ]
    
    # Apply replacements
    original_content = content
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # Check if any changes were made
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False


def migrate_todo_file(todo_path):
    """Migrate a TODO.md file to the new format.
    
    Args:
        todo_path: Path to the TODO.md file
        
    Returns:
        True if migration was successful, False otherwise
    """
    if not todo_path.exists():
        print(f"TODO file not found at {todo_path}")
        return False
    
    # Create a backup
    backup_path = todo_path.with_suffix('.md.bak')
    shutil.copy2(todo_path, backup_path)
    print(f"Created backup at {backup_path}")
    
    # Parse the existing file
    tasks = parse_todo_file(str(todo_path))
    
    if not tasks:
        print(f"No tasks found in {todo_path}")
        return False
    
    # Save using the new formatter
    success = save_tasks_to_markdown(tasks, str(todo_path))
    
    if success:
        print(f"Successfully migrated {len(tasks)} tasks in {todo_path}")
    else:
        print(f"Failed to migrate {todo_path}")
    
    return success


def main():
    """Main migration function."""
    project_root = Path(__file__).parent.parent
    src_dir = project_root / 'src' / 'gollm'
    
    print(f"Starting migration for project at {project_root}")
    
    # Update imports in Python files
    python_files = list(src_dir.glob('**/*.py'))
    updated_files = 0
    
    for file_path in python_files:
        if update_imports(file_path):
            print(f"Updated imports in {file_path.relative_to(project_root)}")
            updated_files += 1
    
    print(f"Updated imports in {updated_files} files")
    
    # Migrate TODO.md files
    todo_files = list(project_root.glob('**/TODO.md'))
    migrated_todos = 0
    
    for todo_path in todo_files:
        if migrate_todo_file(todo_path):
            migrated_todos += 1
    
    print(f"Migrated {migrated_todos} TODO.md files")
    
    # Print summary
    print("\nMigration Summary:")
    print(f"- Updated imports in {updated_files} files")
    print(f"- Migrated {migrated_todos} TODO.md files")
    print("\nNext steps:")
    print("1. Run tests to ensure everything works correctly")
    print("2. Update any custom scripts that import from the old structure")
    print("3. Review the changes and commit them to version control")


if __name__ == "__main__":
    main()
