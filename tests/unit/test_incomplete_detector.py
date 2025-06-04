#!/usr/bin/env python

"""
Simple script to test the incomplete function detector functionality.
"""

from gollm.validation.validators.incomplete_function_detector import (
    contains_incomplete_functions,
    format_for_completion,
    extract_completed_functions
)

# Test code with incomplete functions
test_code = '''
def complete_function(a, b):
    """This is a complete function."""
    return a + b

def incomplete_function1():
    """This function is incomplete."""
    pass

def incomplete_function2():
    """This function has ellipsis."""
    ...

def incomplete_function3():
    """This function has TODO comments."""
    # TODO: Implement this function
    return None
'''

# Test completed code
completed_code = '''
def complete_function(a, b):
    """This is a complete function."""
    return a + b

def incomplete_function1():
    """This function is incomplete."""
    # Now it's implemented
    result = 42
    return result

def incomplete_function2():
    """This function has ellipsis."""
    # Now it's implemented
    return "Hello, world!"

def incomplete_function3():
    """This function has TODO comments."""
    # Implementation complete
    data = process_data()
    return data
'''


def main():
    """Run tests for the incomplete function detector."""
    print("Testing incomplete function detector...\n")
    
    # Test detection of incomplete functions
    has_incomplete, incomplete_funcs = contains_incomplete_functions(test_code)
    print(f"Has incomplete functions: {has_incomplete}")
    print(f"Found {len(incomplete_funcs)} incomplete functions:")
    for func in incomplete_funcs:
        print(f"  - {func['name']}")
    
    # Test formatting for completion
    if has_incomplete:
        print("\nFormatting code for completion:")
        formatted_code = format_for_completion(incomplete_funcs, test_code)
        print(formatted_code[:200] + "...")
    
    # Test extracting completed functions
    print("\nExtracting and merging completed functions:")
    merged_code = extract_completed_functions(test_code, completed_code)
    print("\nMerged code snippet:")
    print(merged_code[:200] + "...")
    
    # Verify if incomplete functions were properly completed
    has_incomplete_after, incomplete_funcs_after = contains_incomplete_functions(merged_code)
    print(f"\nAfter merging - Has incomplete functions: {has_incomplete_after}")
    print(f"After merging - Found {len(incomplete_funcs_after)} incomplete functions")


if __name__ == "__main__":
    main()
