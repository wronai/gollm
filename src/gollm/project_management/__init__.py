"""
Project management automation for goLLM

This module handles automatic project documentation management:
- TODO list creation and prioritization
- CHANGELOG generation and updates
- Task tracking and completion
- Project progress monitoring
"""

from .todo_manager import TodoManager, Task
from .changelog_manager import ChangelogManager
from .task_prioritizer import TaskPrioritizer, TaskContext

__all__ = [
    "TodoManager",
    "Task",
    "ChangelogManager", 
    "TaskPrioritizer",
    "TaskContext"
]