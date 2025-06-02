"""
Project management automation for goLLM

This module handles automatic project documentation management:
- TODO list creation and prioritization
- CHANGELOG generation and updates
- Task tracking and completion
- Project progress monitoring
"""

from .todo import TodoManager, Task, TaskPriority, TaskStatus
from .changelog_manager import ChangelogManager
from .task_prioritizer import TaskPrioritizer, TaskContext

__all__ = [
    "TodoManager",
    "Task",
    "TaskPriority",
    "TaskStatus",
    "ChangelogManager", 
    "TaskPrioritizer",
    "TaskContext"
]