"""End-to-end tests for code generation with direct execution.

These tests verify that GoLLM can generate Python code and that the
generated code can be executed successfully.
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from tests.conftest import llm_test



class TestCodeGenerationRun(unittest.TestCase):
    """Test code generation with direct execution."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up after tests."""
        os.chdir(self.original_dir)
        self.temp_dir.cleanup()

    def run_gollm_command(self, prompt, test_name):
        """Run gollm generate command with the given prompt."""
        # Create a temporary output file
        output_file = os.path.join(self.temp_dir, f"output_{test_name}.py")
        
        # Run gollm generate with the prompt and -o flag
        result = subprocess.run(
            ["gollm", "generate", prompt, "-o", output_file],
            capture_output=True,
            text=True,
            cwd=self.temp_dir
        )
        
        self.assertEqual(result.returncode, 0, f"gollm generate failed: {result.stderr}")
        self.assertTrue(os.path.exists(output_file), f"Output file {output_file} was not created")
        
        # Execute the generated Python code
        python_result = subprocess.run(
            ["python", output_file],
            capture_output=True,
            text=True,
            cwd=self.temp_dir
        )
        
        self.assertEqual(python_result.returncode, 0, f"Python execution failed: {python_result.stderr}\nGenerated code:\n{open(output_file).read()}")

        return python_result

    @llm_test(timeout=30)
    def test_simple_function(self):
        """Test generating a simple function that adds two numbers."""
        prompt = "Create a function that adds two numbers and test it with the values 5 and 7"
        result = self.run_gollm_command(prompt, "simple_function")
        self.assertIn("12", result.stdout, "Expected output containing the sum 5+7=12")

    @llm_test(timeout=30)
    def test_user_class(self):
        """Test generating a User class with basic functionality."""
        prompt = "Stwórz klasę użytkownika z polami imię, nazwisko, email i metodą do wyświetlania pełnych danych"
        result = self.run_gollm_command(prompt, "user_class")
        self.assertIn("użytkownik", result.stdout.lower(), "Expected output containing user information")

    @llm_test(timeout=30)
    def test_factorial_recursive(self):
        """Test generating a recursive factorial function."""
        prompt = "Create a recursive factorial function and test it with the value 5"
        result = self.run_gollm_command(prompt, "factorial_recursive")
        self.assertIn("120", result.stdout, "Expected output containing factorial of 5 (120)")

    @llm_test(timeout=30)
    def test_fibonacci_sequence(self):
        """Test generating a function that returns Fibonacci sequence."""
        prompt = "Create a function that returns the first 10 numbers in the Fibonacci sequence"
        result = self.run_gollm_command(prompt, "fibonacci_sequence")
        self.assertIn("0, 1, 1, 2, 3, 5, 8, 13, 21, 34", result.stdout, "Expected output containing Fibonacci sequence")

    @llm_test(timeout=30)
    def test_string_manipulation(self):
        """Test generating a function that manipulates strings."""
        prompt = "Create a function that counts the occurrences of each word in a sentence and test it"
        result = self.run_gollm_command(prompt, "string_manipulation")
        # Just check that it runs without errors, output will vary

    @llm_test(timeout=30)
    def test_simple_calculator(self):
        """Test generating a simple calculator class."""
        prompt = "Create a Calculator class with methods for addition, subtraction, multiplication, and division"
        result = self.run_gollm_command(prompt, "simple_calculator")
        self.assertIn("Calculator", result.stdout, "Expected output containing calculator operations")
        operations = ["add", "subtract", "multiply", "divide"]
        for op in operations:
            self.assertIn(op, result.stdout.lower(), f"Expected output containing '{op}' operation")

    @llm_test(timeout=30)
    def test_list_comprehension(self):
        """Test generating code using list comprehension."""
        prompt = "Create a function that uses list comprehension to filter even numbers from a list and test it"
        result = self.run_gollm_command(prompt, "list_comprehension")
        self.assertIn("even", result.stdout.lower(), "Expected output containing filtered even numbers")

    @llm_test(timeout=30)
    def test_file_operations(self):
        """Test generating code that performs file operations."""
        prompt = "Create a function that writes numbers 1 to 10 to a file and another function that reads and prints them"
        result = self.run_gollm_command(prompt, "file_operations")
        # Check that numbers appear in the output
        for num in range(1, 11):
            self.assertIn(str(num), result.stdout, f"Expected output containing number {num}")

    @llm_test(timeout=30)
    def test_exception_handling(self):
        """Test generating code with exception handling."""
        prompt = "Create a function that demonstrates try/except/finally blocks for division by zero"
        result = self.run_gollm_command(prompt, "exception_handling")
        # Check that exception handling is mentioned in the output
        self.assertIn("except", result.stdout.lower(), "Expected output containing exception handling")

    @llm_test(timeout=30)
    def test_class_inheritance(self):
        """Test generating code with class inheritance."""
        prompt = "Create a base Shape class and derived Circle and Rectangle classes with area methods"
        result = self.run_gollm_command(prompt, "class_inheritance")
        # Check for class names and area calculations
        expected_terms = ["shape", "circle", "rectangle", "area"]
        for term in expected_terms:
            self.assertIn(term, result.stdout.lower(), f"Expected output containing '{term}'")


if __name__ == "__main__":
    unittest.main()
