"""Todo management package for GoLLM.

This package provides functionality for managing todo items, including
parsing todo files, creating tasks from code violations, and tracking
task completion.
"""

from .manager import TodoManager
from .models import Task, TaskPriority, TaskStatus

__all__ = ['TodoManager', 'Task', 'TaskPriority', 'TaskStatus']
