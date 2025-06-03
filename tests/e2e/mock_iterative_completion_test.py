#!/usr/bin/env python3
"""
Mock tests for the iterative code completion feature.

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
        """Detect incomplete functions in Python code.
        
        Args:
            code: Python code to analyze
            
        Returns:
            List of dictionaries with information about incomplete functions
        """
        incomplete_funcs = []
        
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check if function body is empty or just contains 'pass' or '...'
                    if not node.body:
                        incomplete_funcs.append({
                            'name': node.name,
                            'lineno': node.lineno,
                            'body': '',
                            'signature': MockIncompleteCodeDetector._get_function_signature(code, node)
                        })
                        continue
                        
                    # Check for pass, ellipsis, or TODO comments
                    body_src = '\n'.join(MockIncompleteCodeDetector._get_function_body_lines(code, node))
                    if (MockIncompleteCodeDetector._contains_only_pass(node) or
                        MockIncompleteCodeDetector._contains_ellipsis(body_src) or
                        MockIncompleteCodeDetector._contains_placeholder_comment(body_src)):
                        incomplete_funcs.append({
                            'name': node.name,
                            'lineno': node.lineno,
                            'body': body_src,
                            'signature': MockIncompleteCodeDetector._get_function_signature(code, node)
                        })
        except SyntaxError:
            # If code has syntax errors, we can't parse it properly
            pass
            
        return incomplete_funcs
    
    @staticmethod
    def _contains_only_pass(node: ast.FunctionDef) -> bool:
        """Check if function body only contains 'pass' statement."""
        if len(node.body) != 1:
            return False
        return isinstance(node.body[0], ast.Pass)
    
    @staticmethod
    def _contains_ellipsis(body_src: str) -> bool:
        """Check if function body contains ellipsis (...) placeholder."""
        return '...' in body_src
    
    @staticmethod
    def _contains_placeholder_comment(body_src: str) -> bool:
        """Check if function body contains placeholder comments like TODO or FIXME."""
        placeholder_patterns = [
            r'#\s*TODO', r'#\s*FIXME', r'#\s*IMPLEMENT', r'#\s*NOT\s*IMPLEMENTED'
        ]
        for pattern in placeholder_patterns:
            if re.search(pattern, body_src, re.IGNORECASE):
                return True
        return False
    
    @staticmethod
    def _get_function_signature(code: str, node: ast.FunctionDef) -> str:
        """Extract function signature from source code."""
        code_lines = code.split('\n')
        # Get the line with the function definition
        func_line = code_lines[node.lineno - 1]
        return func_line
    
    @staticmethod
    def _get_function_body_lines(code: str, node: ast.FunctionDef) -> List[str]:
        """Extract function body lines from source code."""
        code_lines = code.split('\n')
        # Find the end of the function by indentation level
        start_line = node.lineno
        body_lines = []
        
        # Skip the function definition line
        for line in code_lines[start_line:]:
            if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                break
            body_lines.append(line)
            
        return body_lines


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
        updated_code = original_code
        
        try:
            tree = ast.parse(original_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name in completed_funcs:
                    # Find the function in the original code
                    func_lines = original_code.split('\n')[node.lineno-1:node.end_lineno]
                    original_func = '\n'.join(func_lines)
                    # Replace with the completed function
                    updated_code = updated_code.replace(original_func, completed_funcs[node.name])
        except SyntaxError:
            # If code has syntax errors, try simple string replacement
            for func_name, func_code in completed_funcs.items():
                pattern = fr'def\s+{func_name}\s*\([^)]*\)\s*:[^\n]*\n(?:\s+[^\n]*\n)*'
                updated_code = re.sub(pattern, func_code, updated_code)
                
        return updated_code
    
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
    
    async def process_code_iteratively(self, code: str) -> Tuple[str, int]:
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


class TestIterativeCodeCompletion(unittest.IsolatedAsyncioTestCase):
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
        
        # At least one function should have a TODO comment
        todo_funcs = [func for func in incomplete_funcs if 'TODO' in func.get('body', '')]
        self.assertGreater(len(todo_funcs), 0, "Should detect at least one function with TODO comment")
    
    def test_prompt_formatting(self):
        """Test formatting of completion prompts."""
        code = textwrap.dedent("""
        def factorial(n):
            pass
        """)
        
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
        """)
        
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
        """)
        
        completed_funcs = {
            'factorial': 'def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)'
        }
        
        orchestrator = MockLLMOrchestrator()
        merged_code = orchestrator.merge_completed_functions(original_code, completed_funcs)
        
        self.assertIn('if n <= 1:', merged_code)
        self.assertIn('# TODO: Implement', merged_code)  # Fibonacci still incomplete
    
    async def test_iterative_completion_simple(self):
        """Test iterative completion of a simple function."""
        code = textwrap.dedent("""
        def add(a, b):
            pass
        """)
        
        completed_code, iterations = await self.orchestrator.process_code_iteratively(code)
        
        self.assertEqual(iterations, 1)
        self.assertIn('return a + b', completed_code)
    
    async def test_iterative_completion_multiple(self):
        """Test iterative completion of multiple functions."""
        code = textwrap.dedent("""
        def add(a, b):
            pass
            
        def factorial(n):
            # TODO: Implement factorial
            
        def fibonacci(n):
            ...
        """)
        
        completed_code, iterations = await self.orchestrator.process_code_iteratively(code)
        
        self.assertEqual(iterations, 1)  # Should complete all in one iteration
        self.assertIn('return a + b', completed_code)
        self.assertIn('return n * factorial(n-1)', completed_code)
        self.assertIn('sequence.append(sequence[i-1] + sequence[i-2])', completed_code)
    
    async def test_end_to_end_factorial(self):
        """End-to-end test for factorial function completion and execution."""
        # Initial code with incomplete factorial function
        initial_code = textwrap.dedent("""
        def factorial(n):
            # TODO: Implement factorial calculation
            pass
            
        # Test the function
        result = factorial(5)
        print(f"Factorial of 5 is {result}")
        """)
        
        # Write to a temporary file
        temp_file = os.path.join(self.temp_dir.name, "factorial.py")
        with open(temp_file, "w") as f:
            f.write(initial_code)
        
        # Process the code iteratively
        completed_code, _ = await self.orchestrator.process_code_iteratively(initial_code)
        
        # Write the completed code to the file
        with open(temp_file, "w") as f:
            f.write(completed_code)
        
        # Execute the completed code
        import subprocess
        result = subprocess.run(["python", temp_file], capture_output=True, text=True)
        
        # Check that it ran successfully and produced the expected output
        self.assertEqual(result.returncode, 0)
        self.assertIn("Factorial of 5 is 120", result.stdout)


if __name__ == "__main__":
    import asyncio
    
    # Create a custom test runner that supports async tests
    class AsyncTestRunner(unittest.TextTestRunner):
        def run(self, test):
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(self._run_async(test))
            return result
            
        async def _run_async(self, test):
            return super().run(test)
    
    # Run the tests with the async test runner
    unittest.main(testRunner=AsyncTestRunner())
