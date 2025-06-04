#!/usr/bin/env python3
"""
Script to move test files and update imports.
"""
import os
import re
import shutil
from pathlib import Path

# Define source and destination directories
ROOT_DIR = Path(__file__).parent.parent
TEST_DIR = ROOT_DIR / 'tests'
SRC_TEST_DIR = ROOT_DIR / 'src' / 'gollm' / 'tests'

# Test file patterns to move
TEST_PATTERNS = [
    'test_*.py',
]

# Files to exclude (already in correct location)
EXCLUDE_FILES = {
    'conftest.py',
    '__init__.py',
    'test_utils.py',
}

def get_import_path(file_path: Path, new_dir: Path) -> str:
    """Convert file path to import path."""
    rel_path = file_path.relative_to(ROOT_DIR).with_suffix('')
    return str(rel_path).replace(os.path.sep, '.')

def update_imports(file_path: Path, old_imports: dict):
    """Update imports in a file."""
    if not file_path.exists():
        return
        
    content = file_path.read_text(encoding='utf-8')
    
    # Replace imports
    for old_imp, new_imp in old_imports.items():
        # Handle different import styles
        patterns = [
            (f'import {old_imp}\b', f'import {new_imp}'),
            (f'from {old_imp}\b', f'from {new_imp}'),
        ]
        for pattern, repl in patterns:
            content = re.sub(pattern, repl, content)
    
    file_path.write_text(content, encoding='utf-8')

def move_test_files():
    """Move test files and update imports."""
    moved_files = {}
    
    # Find all test files in root
    root_test_files = []
    for pattern in TEST_PATTERNS:
        root_test_files.extend(Path(ROOT_DIR).glob(pattern))
    
    # Filter out excluded files and files already in test directories
    test_files = [
        f for f in root_test_files 
        if f.name not in EXCLUDE_FILES and 
        not str(f).startswith(str(TEST_DIR)) and
        not str(f).startswith(str(SRC_TEST_DIR))
    ]
    
    if not test_files:
        print("No test files to move.")
        return
    
    # Create unit test directory if it doesn't exist
    unit_test_dir = TEST_DIR / 'unit'
    unit_test_dir.mkdir(parents=True, exist_ok=True)
    
    # Move files and track old/new paths
    for src_file in test_files:
        # Determine destination directory
        if 'e2e' in str(src_file):
            dest_dir = TEST_DIR / 'e2e'
        elif 'integration' in str(src_file):
            dest_dir = TEST_DIR / 'integration'
        else:
            dest_dir = unit_test_dir
            
        dest_file = dest_dir / src_file.name
        
        # Handle name conflicts
        counter = 1
        while dest_file.exists():
            stem = src_file.stem
            suffix = src_file.suffix
            dest_file = dest_dir / f"{stem}_{counter}{suffix}"
            counter += 1
        
        # Move the file
        print(f"Moving {src_file} -> {dest_file}")
        shutil.move(str(src_file), str(dest_file))
        moved_files[src_file.stem] = dest_file.stem
        
        # Update imports in the moved file
        update_imports(dest_file, moved_files)
    
    # Update imports in all test files
    for test_file in TEST_DIR.rglob('test_*.py'):
        update_imports(test_file, moved_files)
    
    print("\nTest files moved and imports updated successfully!")

if __name__ == "__main__":
    move_test_files()
