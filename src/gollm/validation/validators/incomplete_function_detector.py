"""Incomplete function detector module.

This module provides functionality to detect incomplete or placeholder functions
in generated code and flag them for further completion.
"""

import ast
import logging
import re
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger("gollm.validation.code.incomplete_detector")


def contains_incomplete_functions(code: str) -> Tuple[bool, List[Dict[str, str]]]:
    """Check if the code contains incomplete functions.

    An incomplete function is defined as one that:
    1. Contains only 'pass' statements
    2. Contains placeholder comments like '# TODO', '# FIXME', etc.
    3. Contains ellipsis (...) as the only statement
    4. Has an empty function body

    Args:
        code: The Python code to analyze

    Returns:
        Tuple of (has_incomplete_functions, list_of_incomplete_functions)
        Each incomplete function is a dict with 'name', 'body', and 'signature' keys
    """
    if not code or code.isspace():
        return False, []

    # Try to parse with AST to find incomplete functions
    try:
        tree = ast.parse(code)
    except SyntaxError:
        # If code has syntax errors, we can't reliably detect incomplete functions
        logger.warning("Cannot detect incomplete functions due to syntax errors")
        return False, []

    incomplete_functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Get function name
            func_name = node.name
            
            # Get function body
            body_nodes = node.body
            
            # Check if function is incomplete
            is_incomplete = False
            
            # Case 1: Empty function or only 'pass' statement
            if not body_nodes or (
                len(body_nodes) == 1 and isinstance(body_nodes[0], ast.Pass)
            ):
                is_incomplete = True
            
            # Case 2: Only docstring and/or pass
            elif (
                len(body_nodes) <= 2 
                and any(isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str) for n in body_nodes)
                and all(isinstance(n, ast.Expr) or isinstance(n, ast.Pass) for n in body_nodes)
            ):
                is_incomplete = True
            
            # Case 3: Contains ellipsis
            elif any(
                isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and n.value.value == ...
                for n in body_nodes
            ):
                is_incomplete = True
                
            # Case 4: Contains TODO/FIXME comments
            elif _contains_placeholder_comments(code, node):
                is_incomplete = True
                
            # Get function source code
            if is_incomplete:
                # Extract function signature
                func_args = []
                for arg in node.args.args:
                    arg_name = arg.arg
                    # Get type annotation if available
                    if arg.annotation:
                        arg_type = ast.unparse(arg.annotation)
                        func_args.append(f"{arg_name}: {arg_type}")
                    else:
                        func_args.append(arg_name)
                
                # Add *args if present
                if node.args.vararg:
                    func_args.append(f"*{node.args.vararg.arg}")
                
                # Add **kwargs if present
                if node.args.kwarg:
                    func_args.append(f"**{node.args.kwarg.arg}")
                
                # Build function signature
                signature = f"def {func_name}({', '.join(func_args)})"
                
                # Get return type annotation if available
                if node.returns:
                    return_type = ast.unparse(node.returns)
                    signature += f" -> {return_type}"
                    
                signature += ":"
                
                # Get function source
                func_lines = code.splitlines()[node.lineno-1:node.end_lineno]
                func_body = "\n".join(func_lines)
                
                # Add to incomplete functions list
                incomplete_functions.append({
                    "name": func_name,
                    "signature": signature,
                    "body": func_body,
                    "lineno": node.lineno,
                    "end_lineno": node.end_lineno
                })
                
                logger.info(f"Found incomplete function: {func_name}")
    
    return bool(incomplete_functions), incomplete_functions


def _contains_placeholder_comments(code: str, node: ast.FunctionDef) -> bool:
    """Check if function contains placeholder comments like TODO or FIXME.
    
    Args:
        code: The full source code
        node: The function definition node
        
    Returns:
        True if placeholder comments are found, False otherwise
    """
    # Get function lines
    func_lines = code.splitlines()[node.lineno-1:node.end_lineno]
    func_text = "\n".join(func_lines)
    
    # Look for TODO, FIXME, etc. in comments
    placeholder_patterns = [
        r'#\s*TODO',
        r'#\s*FIXME',
        r'#\s*XXX',
        r'#\s*IMPLEMENT',
        r'#\s*NOT IMPLEMENTED',
        r'#\s*TO BE IMPLEMENTED',
        r'#\s*PLACEHOLDER',
    ]
    
    for pattern in placeholder_patterns:
        if re.search(pattern, func_text, re.IGNORECASE):
            return True
    
    return False


def format_for_completion(incomplete_functions: List[Dict[str, str]], code: str) -> str:
    """Format the code with incomplete functions for LLM completion.
    
    This function prepares a prompt for the LLM to complete the incomplete functions.
    
    Args:
        incomplete_functions: List of incomplete functions detected
        code: The original code
        
    Returns:
        Formatted code with instructions for LLM completion
    """
    if not incomplete_functions:
        return code
    
    # Create a prompt for the LLM
    prompt = """The following code contains incomplete functions that need to be implemented.
    Please complete the functions marked with TODO comments below:
    
    """
    
    # Add the original code with TODO markers
    code_lines = code.splitlines()
    
    # Track line offsets due to added comments
    line_offset = 0
    
    # Sort incomplete functions by line number to process them in order
    sorted_functions = sorted(incomplete_functions, key=lambda f: f["lineno"])
    
    for func in sorted_functions:
        # Add TODO comment before the function
        insert_line = func["lineno"] - 1 + line_offset
        code_lines.insert(insert_line, f"# TODO: Implement the {func['name']} function below")
        line_offset += 1
    
    # Join the modified code lines
    modified_code = "\n".join(code_lines)
    
    return prompt + modified_code


def extract_completed_functions(original_code: str, completed_code: str) -> str:
    """Extract completed functions from LLM response and merge them with original code.
    
    Args:
        original_code: The original code with incomplete functions
        completed_code: The LLM response with completed functions
        
    Returns:
        Merged code with completed functions
    """
    try:
        # Parse both code versions
        original_tree = ast.parse(original_code)
        completed_tree = ast.parse(completed_code)
    except SyntaxError:
        logger.error("Syntax error in completed code, cannot merge functions")
        return original_code
    
    # Extract function definitions from both trees
    original_funcs = {}
    completed_funcs = {}
    
    for node in ast.walk(original_tree):
        if isinstance(node, ast.FunctionDef):
            original_funcs[node.name] = node
    
    for node in ast.walk(completed_tree):
        if isinstance(node, ast.FunctionDef):
            completed_funcs[node.name] = node
    
    # Replace incomplete functions with completed ones
    result_code = original_code
    has_incomplete, incomplete_list = contains_incomplete_functions(original_code)
    
    if has_incomplete:
        for func_info in incomplete_list:
            func_name = func_info["name"]
            if func_name in completed_funcs and func_name in original_funcs:
                # Get the completed function source
                completed_node = completed_funcs[func_name]
                completed_source = ast.unparse(completed_node)
                
                # Replace in the original code
                original_lines = result_code.splitlines()
                start_line = func_info["lineno"] - 1
                end_line = func_info["end_lineno"]
                
                # Replace the function definition
                result_code = "\n".join(
                    original_lines[:start_line] + 
                    [completed_source] + 
                    original_lines[end_line:]
                )
    
    return result_code
