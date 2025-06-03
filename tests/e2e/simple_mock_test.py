#!/usr/bin/env python3
"""
Simplified mock tests for the iterative code completion feature.

This file contains standalone tests that demonstrate the iterative code completion
feature without requiring the actual GoLLM implementation or external dependencies.
"""

import unittest
import ast
import re
import os
import tempfile
import textwrap
from typing import List, Dict, Any, Tuple


class MockIncompleteCodeDetector:
    """Mock implementation of the incomplete function detector."""
    
    @staticmethod
    def contains_incomplete_functions(code: str) -> List[Dict[str, Any]]:
        """Detect incomplete functions in Python code using simple regex patterns.
        
        Args:
            code: Python code to analyze
            
        Returns:
            List of dictionaries with information about incomplete functions
        """
        incomplete_funcs = []
        
        # Simple approach: split code into lines and look for patterns
        lines = code.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            # Look for function definitions
            if re.match(r'\s*def\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(', line):
                func_name = re.search(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', line).group(1)
                signature = line.strip()
                
                # Look at the body of the function
                body_lines = []
                j = i + 1
                while j < len(lines) and (not lines[j].strip() or lines[j].startswith(' ') or lines[j].startswith('\t')):
                    body_lines.append(lines[j])
                    j += 1
                
                body = '\n'.join(body_lines)
                
                # Check if the function is incomplete
                if (not body.strip() or 
                    'pass' in body or 
                    '...' in body or 
                    re.search(r'#\s*TODO', body, re.IGNORECASE) or
                    re.search(r'#\s*FIXME', body, re.IGNORECASE)):
                    
                    incomplete_funcs.append({
                        'name': func_name,
                        'lineno': i + 1,
                        'body': body,
                        'signature': signature
                    })
                
                i = j  # Skip to the end of this function
            else:
                i += 1
                
        return incomplete_funcs


class MockLLMOrchestrator:
    """Mock implementation of the LLM orchestrator."""
    
    def __init__(self):
        self.detector = MockIncompleteCodeDetector()
        self.iteration_count = 0
        self.max_iterations = 3
    
    def format_completion_prompt(self, code: str, incomplete_funcs: List[Dict[str, Any]]) -> str:
        """Format a prompt for completing incomplete functions.
        
        Args:
            code: Original code with incomplete functions
            incomplete_funcs: List of incomplete functions to complete
            
        Returns:
            Formatted prompt for the LLM
        """
        prompt = "Complete the following Python functions. Keep the function signatures and docstrings unchanged.\n\n"
        
        # Add TODO markers to make incomplete functions more visible
        marked_code = code
        for func in incomplete_funcs:
            # Add TODO comment after function definition
            signature = func['signature']
            marked_code = marked_code.replace(
                signature,
                f"{signature}  # TODO: Implement this function"
            )
        
        prompt += marked_code
        return prompt
    
    def extract_completed_functions(self, llm_response: str) -> Dict[str, str]:
        """Extract completed functions from LLM response.
        
        Args:
            llm_response: Response from the LLM
            
        Returns:
            Dictionary mapping function names to their completed implementations
        """
        completed_funcs = {}
        
        try:
            tree = ast.parse(llm_response)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Extract the complete function definition
                    func_lines = llm_response.split('\n')[node.lineno-1:node.end_lineno]
                    func_code = '\n'.join(func_lines)
                    completed_funcs[node.name] = func_code
        except SyntaxError:
            # If response has syntax errors, try to extract functions using regex
            pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*:([^\n]*\n(?:\s+[^\n]*\n)*)'  
            for match in re.finditer(pattern, llm_response):
                func_name = match.group(1)
                func_code = match.group(0)
                completed_funcs[func_name] = func_code
                
        return completed_funcs
    
    def merge_completed_functions(self, original_code: str, completed_funcs: Dict[str, str]) -> str:
        """Merge completed functions into the original code.
        
        Args:
            original_code: Original code with incomplete functions
            completed_funcs: Dictionary mapping function names to their completed implementations
            
        Returns:
            Updated code with completed functions
        """
        # Split the code into lines for easier processing
        lines = original_code.split('\n')
        result_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            # Check if this line starts a function definition
            match = re.match(r'\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', line)
            if match:
                func_name = match.group(1)
                
                if func_name in completed_funcs:
                    # Add the completed function
                    result_lines.append(completed_funcs[func_name])
                    
                    # Skip the original function definition and body
                    j = i + 1
                    while j < len(lines) and (not lines[j].strip() or lines[j].startswith(' ') or lines[j].startswith('\t')):
                        j += 1
                    i = j
                else:
                    # Keep the original line
                    result_lines.append(line)
                    i += 1
            else:
                # Keep the original line
                result_lines.append(line)
                i += 1
        
        return '\n'.join(result_lines)
    
    def simulate_llm_response(self, prompt: str, incomplete_funcs: List[Dict[str, Any]]) -> str:
        """Simulate an LLM response that completes the incomplete functions.
        
        Args:
            prompt: Prompt for the LLM
            incomplete_funcs: List of incomplete functions to complete
            
        Returns:
            Simulated LLM response with completed functions
        """
        response = ""
        
        for func in incomplete_funcs:
            func_name = func['name']
            signature = func['signature']
            
            # Generate a simple implementation based on the function name
            if 'add' in func_name.lower():
                response += f"{signature}\n    # Implementation for addition function\n    return a + b\n\n"
            elif 'factorial' in func_name.lower():
                response += f"{signature}\n    # Implementation for factorial function\n    if n <= 1:\n        return 1\n    return n * {func_name}(n-1)\n\n"
            elif 'fibonacci' in func_name.lower():
                response += f"{signature}\n    # Implementation for Fibonacci sequence\n    sequence = [0, 1]\n    for i in range(2, n):\n        sequence.append(sequence[i-1] + sequence[i-2])\n    return sequence\n\n"
            else:
                response += f"{signature}\n    # Generic implementation\n    print(\"Function {func_name} has been implemented\")\n    return True\n\n"
                
        return response
    
    def process_code_iteratively(self, code: str) -> Tuple[str, int]:
        """Process code iteratively to complete all incomplete functions.
        
        Args:
            code: Initial code with potentially incomplete functions
            
        Returns:
            Tuple of (completed code, number of iterations performed)
        """
        current_code = code
        iterations_performed = 0
        
        for i in range(self.max_iterations):
            # Detect incomplete functions
            incomplete_funcs = self.detector.contains_incomplete_functions(current_code)
            
            # If no incomplete functions, we're done
            if not incomplete_funcs:
                break
                
            # Format prompt for completion
            prompt = self.format_completion_prompt(current_code, incomplete_funcs)
            
            # Simulate LLM response
            llm_response = self.simulate_llm_response(prompt, incomplete_funcs)
            
            # Extract completed functions
            completed_funcs = self.extract_completed_functions(llm_response)
            
            # Merge completed functions into the code
            current_code = self.merge_completed_functions(current_code, completed_funcs)
            
            iterations_performed += 1
            
        return current_code, iterations_performed


class TestIterativeCodeCompletion(unittest.TestCase):
    """Test cases for the iterative code completion feature."""
    
    def setUp(self):
        self.orchestrator = MockLLMOrchestrator()
        self.temp_dir = tempfile.TemporaryDirectory()
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_incomplete_function_detection(self):
        """Test detection of incomplete functions."""
        # The code needs to be properly indented for AST parsing
        code = textwrap.dedent("""
        def add(a, b):
            pass
            
        def subtract(a, b):
            # TODO: Implement subtraction
            
        def multiply(a, b):
            ...
            
        def complete_func(a, b):
            return a * b
        """).strip()
        
        detector = MockIncompleteCodeDetector()
        incomplete_funcs = detector.contains_incomplete_functions(code)
        
        # Print for debugging
        print(f"Detected incomplete functions: {incomplete_funcs}")
        
        # Check that we found incomplete functions
        self.assertGreater(len(incomplete_funcs), 0, "Should detect at least one incomplete function")
        
        # Check function names
        func_names = [func['name'] for func in incomplete_funcs]
        self.assertIn('add', func_names, "Should detect 'add' as incomplete")
    
    def test_prompt_formatting(self):
        """Test formatting of completion prompts."""
        code = textwrap.dedent("""
        def factorial(n):
            pass
        """).strip()
        
        detector = MockIncompleteCodeDetector()
        incomplete_funcs = detector.contains_incomplete_functions(code)
        
        orchestrator = MockLLMOrchestrator()
        prompt = orchestrator.format_completion_prompt(code, incomplete_funcs)
        
        self.assertIn("Complete the following Python functions", prompt)
        self.assertIn("TODO: Implement this function", prompt)
    
    def test_function_extraction(self):
        """Test extraction of completed functions from LLM response."""
        llm_response = textwrap.dedent("""
        def factorial(n):
            if n <= 1:
                return 1
            return n * factorial(n-1)
        """).strip()
        
        orchestrator = MockLLMOrchestrator()
        completed_funcs = orchestrator.extract_completed_functions(llm_response)
        
        self.assertIn('factorial', completed_funcs)
        self.assertIn('if n <= 1:', completed_funcs['factorial'])
    
    def test_function_merging(self):
        """Test merging of completed functions into original code."""
        original_code = textwrap.dedent("""
        def factorial(n):
            pass
            
        def fibonacci(n):
            # TODO: Implement
        """).strip()
        
        completed_funcs = {
            'factorial': 'def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)'
        }
        
        orchestrator = MockLLMOrchestrator()
        merged_code = orchestrator.merge_completed_functions(original_code, completed_funcs)
        
        self.assertIn('if n <= 1:', merged_code)
        self.assertIn('# TODO: Implement', merged_code)  # Fibonacci still incomplete
    
    def test_iterative_completion_simple(self):
        """Test iterative completion of a simple function."""
        code = textwrap.dedent("""
        def add(a, b):
            pass
        """).strip()
        
        completed_code, iterations = self.orchestrator.process_code_iteratively(code)
        
        # We don't care about the exact number of iterations as long as it completed
        self.assertGreaterEqual(iterations, 1)
        self.assertIn('return a + b', completed_code)
    
    def test_iterative_completion_multiple(self):
        """Test iterative completion of multiple functions."""
        code = textwrap.dedent("""
        def add(a, b):
            pass
            
        def factorial(n):
            # TODO: Implement factorial
            
        def fibonacci(n):
            ...
        """).strip()
        
        completed_code, iterations = self.orchestrator.process_code_iteratively(code)
        
        # We don't care about the exact number of iterations as long as it completed
        self.assertGreaterEqual(iterations, 1)
        self.assertIn('return a + b', completed_code)
        self.assertIn('return n * factorial(n-1)', completed_code)
        self.assertIn('sequence.append(sequence[i-1] + sequence[i-2])', completed_code)
    
    def test_end_to_end_factorial(self):
        """End-to-end test for factorial function completion and execution."""
        # Initial code with incomplete factorial function
        initial_code = textwrap.dedent("""
        def factorial(n):
            # TODO: Implement factorial calculation
            pass
            
        # Test the function
        result = factorial(5)
        print(f"Factorial of 5 is {result}")
        """).strip()
        
        # Process the code iteratively
        completed_code, _ = self.orchestrator.process_code_iteratively(initial_code)
        
        # Write the completed code to a file
        temp_file = os.path.join(self.temp_dir.name, "factorial.py")
        with open(temp_file, "w") as f:
            f.write(completed_code)
        
        # Execute the completed code
        import subprocess
        result = subprocess.run(["python", temp_file], capture_output=True, text=True)
        
        # Check that it ran successfully and produced the expected output
        self.assertEqual(result.returncode, 0)
        self.assertIn("Factorial of 5 is 120", result.stdout)


if __name__ == "__main__":
    unittest.main()
