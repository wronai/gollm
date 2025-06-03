"""
Project management automation for goLLM

This module handles automatic project documentation management:
- TODO list creation and prioritization
- CHANGELOG generation and updates
- Task tracking and completion
- Project progress monitoring
"""

from .changelog_manager import ChangelogManager
from .task_prioritizer import TaskContext, TaskPrioritizer
from .todo import Task, TaskPriority, TaskStatus, TodoManager

__all__ = [
    "TodoManager",
    "Task",
    "TaskPriority",
    "TaskStatus",
    "ChangelogManager",
    "TaskPrioritizer",
    "TaskContext",
]
