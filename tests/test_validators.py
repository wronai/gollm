# tests/test_validators.py
import pytest
import tempfile
import os
from pathlib import Path

from gollm.validation.validators import CodeValidator, Violation
from gollm.config.config import GollmConfig

class TestCodeValidator:
    
    @pytest.fixture
    def config(self):
        """Test configuration"""
        return GollmConfig.default()
    
    @pytest.fixture
    def validator(self, config):
        """Test validator instance"""
        return CodeValidator(config)
    
    def test_validate_good_code(self, validator):
        """Test validation of good code"""
        good_code = '''
def add_numbers(a: int, b: int) -> int:
    """
    Adds two numbers together.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Sum of the two numbers
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Adding {a} and {b}")
    return a + b
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(good_code)
            temp_file = f.name
        
        try:
            result = validator.validate_file(temp_file)
            assert len(result['violations']) == 0
            assert result['quality_score'] > 90
        finally:
            os.unlink(temp_file)
    
    def test_validate_bad_code(self, validator):
        """Test validation of problematic code"""
        bad_code = '''
def bad_function(a, b, c, d, e, f, g):  # Too many parameters
    print("Bad code")  # Print statement
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:  # High complexity
                    if e > 0:
                        return a + b + c + d + e + f + g
    return 0
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(bad_code)
            temp_file = f.name
        
        try:
            result = validator.validate_file(temp_file)
            violations = result['violations']
            
            # Should detect multiple violations
            assert len(violations) > 0
            
            # Check for specific violation types
            violation_types = [v.type for v in violations]
            assert 'too_many_parameters' in violation_types
            assert 'forbidden_print' in violation_types
            
            # Quality score should be low
            assert result['quality_score'] < 80
            
        finally:
            os.unlink(temp_file)
    
    def test_validate_nonexistent_file(self, validator):
        """Test validation of non-existent file"""
        result = validator.validate_file("nonexistent.py")
        assert len(result['violations']) == 1
        assert result['violations'][0].type == "file_not_found"
    
    def test_violation_creation(self):
        """Test Violation dataclass"""
        violation = Violation(
            type="test_violation",
            message="Test message",
            file_path="test.py",
            line_number=10,
            severity="error",
            suggested_fix="Fix this"
        )
        
        assert violation.type == "test_violation"
        assert violation.message == "Test message"
        assert violation.file_path == "test.py"
        assert violation.line_number == 10
        assert violation.severity == "error"
        assert violation.suggested_fix == "Fix this"

# tests/test_todo_manager.py
import pytest
import tempfile
import os
from datetime import datetime

from gollm.project_management.todo_manager import TodoManager, Task
from gollm.config.config import GollmConfig

class TestTodoManager:
    
    @pytest.fixture
    def config(self):
        """Test configuration with temporary TODO file"""
        config = GollmConfig.default()
        # Use temporary file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            config.project_management.todo_file = f.name
        return config
    
    @pytest.fixture
    def todo_manager(self, config):
        """Test TodoManager instance"""
        return TodoManager(config)
    
    def test_task_creation(self):
        """Test Task dataclass creation"""
        task = Task(
            id="test-001",
            title="Test Task",
            description="Test description",
            priority="HIGH",
            status="pending"
        )
        
        assert task.id == "test-001"
        assert task.title == "Test Task"
        assert task.priority == "HIGH"
        assert task.status == "pending"
    
    def test_add_task_from_violation(self, todo_manager):
        """Test creating task from code violation"""
        task = todo_manager.add_task_from_violation(
            "function_too_long",
            {
                "file_path": "test.py",
                "line_number": 25,
                "message": "Function has 60 lines"
            }
        )
        
        assert task is not None
        assert "fix function too long in test.py" in task.title.lower()
        assert task.priority == "MEDIUM"  # Default for function_too_long
        assert "test.py" in task.related_files
    
    def test_get_next_task(self, todo_manager):
        """Test getting next priority task"""
        # Add tasks with different priorities
        high_task = todo_manager.add_task_from_violation(
            "high_complexity",
            {"file_path": "test.py", "line_number": 1, "message": "High complexity"}
        )
        
        low_task = todo_manager.add_task_from_violation(
            "missing_docstring", 
            {"file_path": "test.py", "line_number": 2, "message": "Missing docstring"}
        )
        
        # Should return high priority task first
        next_task = todo_manager.get_next_task()
        assert next_task is not None
        assert next_task['priority'] == 'HIGH'
    
    def test_complete_task(self, todo_manager):
        """Test completing a task"""
        task = todo_manager.add_task_from_violation(
            "function_too_long",
            {"file_path": "test.py", "line_number": 1, "message": "Test"}
        )
        
        # Complete the task
        todo_manager.complete_task(task.id)
        
        # Task should be marked completed
        completed_task = next((t for t in todo_manager.tasks if t.id == task.id), None)
        assert completed_task is not None
        assert completed_task.status == "completed"
    
    def test_get_stats(self, todo_manager):
        """Test getting TODO statistics"""
        # Add some tasks
        todo_manager.add_task_from_violation("high_complexity", {"file_path": "test.py", "line_number": 1, "message": "Test"})
        todo_manager.add_task_from_violation("missing_docstring", {"file_path": "test.py", "line_number": 2, "message": "Test"})
        
        stats = todo_manager.get_stats()
        
        assert "total" in stats
        assert "pending" in stats
        assert "completed" in stats
        assert "high_priority" in stats
        assert stats["total"] >= 2

# tests/test_changelog_manager.py
