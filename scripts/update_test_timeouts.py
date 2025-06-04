#!/usr/bin/env python3
"""
Script to add LLM test timeouts to test files.
"""
import re
from pathlib import Path

# Define test directories
TEST_DIR = Path(__file__).parent.parent / 'tests'
E2E_DIR = TEST_DIR / 'e2e'

# Import statement to add
IMPORT_STATEMENT = 'from tests.conftest import llm_test\n\n'

# Decorator to add to test functions
DECORATOR = '@llm_test(timeout=30)\n'

def update_test_file(file_path: Path):
    """Update a test file with LLM test decorators."""
    try:
        content = file_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        print(f"Skipping non-text file: {file_path}")
        return
    
    # Skip if already updated
    if 'from tests.conftest import llm_test' in content:
        return
    
    # Add import statement after the last import or docstring
    import_match = list(re.finditer(r'^(import |from \w+ import )', content, re.MULTILINE))
    if import_match:
        last_import = import_match[-1]
        insert_pos = last_import.end()
        while content[insert_pos] != '\n':
            insert_pos += 1
        content = content[:insert_pos+1] + IMPORT_STATEMENT + content[insert_pos+1:]
    else:
        # No imports found, add after docstring
        docstring_match = re.search(r'^\s*(""".*?"""|\'\'\'.*?\'\'\')\s*$', content, re.DOTALL | re.MULTILINE)
        if docstring_match:
            insert_pos = docstring_match.end()
            content = content[:insert_pos] + '\n' + IMPORT_STATEMENT + content[insert_pos:]
        else:
            # No docstring either, add at the beginning
            content = IMPORT_STATEMENT + content
    
    # Add decorator to test functions
    lines = content.splitlines()
    in_class = False
    class_indent = ''
    
    for i, line in enumerate(lines):
        # Track class definition
        class_match = re.match(r'^(\s*)class\s+\w+\s*(\([^)]*\))?\s*:', line)
        if class_match:
            in_class = True
            class_indent = class_match.group(1)
            continue
        
        # Look for test functions
        test_match = re.match(r'^(\s*)def\s+(test_\w+)\s*\(', line)
        if test_match and (in_class or not class_indent):
            indent = test_match.group(1)
            # Skip if already has a decorator
            if i > 0 and any(d in lines[i-1] for d in ['@pytest.mark', '@llm_test']):
                continue
            # Add decorator
            lines[i] = f"{indent}{DECORATOR}{line}"
    
    # Write updated content
    file_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f"Updated {file_path}")

def main():
    """Main function to update all test files."""
    # Update e2e tests
    for test_file in E2E_DIR.glob('test_*.py'):
        update_test_file(test_file)
    
    print("\nTest files updated with LLM test timeouts.")

if __name__ == "__main__":
    main()
