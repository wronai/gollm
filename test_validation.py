#!/usr/bin/env python3
"""
Test script for validating the output validator functionality.
"""

import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('validation_test.log')
    ]
)

# Add the src directory to the path so we can import gollm modules
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from gollm.validation.output_validator import validate_saved_code

# Test cases with escape sequences
test_cases = [
    {
        "name": "Python with newline escapes",
        "content": "def hello_world():\\n    print(\"Hello, World!\")\\n\\nif __name__ == \"__main__\":\\n    hello_world()",
        "filename": "test_newlines.py"
    },
    {
        "name": "Python with tab escapes",
        "content": "def hello_world():\\n\\tprint(\"Hello, World!\")\\n\\nif __name__ == \"__main__\":\\n\\thello_world()",
        "filename": "test_tabs.py"
    },
    {
        "name": "Python with unicode escapes",
        "content": "# Unicode test\\ndef print_unicode():\\n    print(\"\\u03B1\\u03B2\\u03B3\")  # Greek letters alpha, beta, gamma\\n\\nprint_unicode()",
        "filename": "test_unicode.py"
    }
]

# Run the tests
for test in test_cases:
    print(f"\n=== Testing: {test['name']} ===")
    
    # First save the content to a file
    filename = test["filename"]
    with open(filename, "w", encoding="utf-8") as f:
        f.write(test["content"])
    print(f"Saved original content to {filename}")
    
    # Now validate the saved file
    is_valid, issues, details = validate_saved_code(test["content"], filename)
    
    print(f"Validation result: {'PASSED' if is_valid else 'FAILED'}")
    if issues:
        print(f"Issues: {', '.join(issues)}")
    
    print("Details:")
    for key, value in details.items():
        if key != "diff_summary":  # Skip diff summary for brevity
            print(f"  {key}: {value}")
    
    # Now use the file handling module to save the content properly
    print("\nNow testing with gollm's file handling:")
    from gollm.cli.utils.file_handling import save_generated_files
    from gollm.validation.code_validator import validate_and_extract_code
    
    # First validate and extract code
    is_valid, validated_content, validation_issues = validate_and_extract_code(
        test["content"], 
        filename.split(".")[-1],
        {"strict_validation": False}
    )
    
    print(f"Code validation: {'PASSED' if is_valid else 'FAILED'}")
    if validation_issues:
        print(f"Validation issues: {', '.join(validation_issues)}")
    
    # Save the validated content to a new file
    fixed_filename = f"fixed_{filename}"
    with open(fixed_filename, "w", encoding="utf-8") as f:
        f.write(validated_content)
    print(f"Saved validated content to {fixed_filename}")
    
    # Now validate the fixed file
    is_valid, issues, details = validate_saved_code(test["content"], fixed_filename)
    
    print(f"Validation of fixed file: {'PASSED' if is_valid else 'FAILED'}")
    if issues:
        print(f"Issues: {', '.join(issues)}")
    
    print("Details:")
    for key, value in details.items():
        if key != "diff_summary":  # Skip diff summary for brevity
            print(f"  {key}: {value}")

print("\nTest completed. Check validation_test.log for detailed logs.")
