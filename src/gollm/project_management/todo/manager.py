"""Todo task management for GoLLM."""

import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .formatter import format_task_for_display
from .models import Task, TaskPriority, TaskStatus
from .parser import create_task_from_violation, parse_todo_file
from .storage import (load_tasks_from_json, save_tasks_to_json,
                      save_tasks_to_markdown)

logger = logging.getLogger("gollm.todo.manager")


class TodoManager:
    """Manages todo tasks for a project.

    This class handles loading, saving, creating, and updating tasks in a project's
    todo list. It supports creating tasks from code violations, user requests, and
    tracking task completion.
    """

    def __init__(self, project_root: str, todo_file: str = "TODO.md"):
        """Initialize the TodoManager.

        Args:
            project_root: Root directory of the project
            todo_file: Name of the todo file (default: TODO.md)
        """
        self.project_root = Path(project_root)
        self.todo_file = self.project_root / todo_file
        self.tasks: List[Task] = []
        self.loaded = False

        # Create cache directory if it doesn't exist
        self.cache_dir = self.project_root / ".gollm" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.json_cache = self.cache_dir / "todo_cache.json"

    def load_tasks(self, force_reload: bool = False) -> List[Task]:
        """Load tasks from the todo file.

        Args:
            force_reload: Whether to force reloading from the file

        Returns:
            List of Task objects
        """
        if self.loaded and not force_reload:
            return self.tasks

        # Try loading from JSON cache first for better performance
        if self.json_cache.exists() and not force_reload:
            cache_mtime = os.path.getmtime(self.json_cache)
            todo_mtime = (
                os.path.getmtime(self.todo_file) if self.todo_file.exists() else 0
            )

            # Use cache if it's newer than the todo file
            if cache_mtime > todo_mtime:
                self.tasks = load_tasks_from_json(str(self.json_cache))
                if self.tasks:
                    self.loaded = True
                    return self.tasks

        # Fall back to parsing the markdown file
        if self.todo_file.exists():
            self.tasks = parse_todo_file(str(self.todo_file))

            # Update the cache
            save_tasks_to_json(self.tasks, str(self.json_cache))
        else:
            self.tasks = []

        self.loaded = True
        return self.tasks

    def save_tasks(self) -> bool:
        """Save tasks to the todo file.

        Returns:
            True if successful, False otherwise
        """
        # Save to markdown file
        success = save_tasks_to_markdown(self.tasks, str(self.todo_file))

        # Update the cache
        if success:
            save_tasks_to_json(self.tasks, str(self.json_cache))

        return success

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Get a task by its ID.

        Args:
            task_id: ID of the task to find

        Returns:
            Task object if found, None otherwise
        """
        self.load_tasks()

        for task in self.tasks:
            if task.id == task_id:
                return task

        return None

    def add_task(self, task: Task) -> bool:
        """Add a new task to the todo list.

        Args:
            task: Task object to add

        Returns:
            True if successful, False otherwise
        """
        self.load_tasks()

        # Check if task with same ID already exists
        if any(t.id == task.id for t in self.tasks):
            logger.warning(f"Task with ID {task.id} already exists")
            return False

        self.tasks.append(task)
        return self.save_tasks()

    def update_task(self, task: Task) -> bool:
        """Update an existing task.

        Args:
            task: Task object with updated fields

        Returns:
            True if successful, False otherwise
        """
        self.load_tasks()

        for i, t in enumerate(self.tasks):
            if t.id == task.id:
                # Update the task's updated_at timestamp
                task.updated_at = datetime.now()

                # If completing the task, set completed_at
                if (
                    task.status in [TaskStatus.COMPLETED, TaskStatus.SKIPPED]
                    and not task.completed_at
                ):
                    task.completed_at = datetime.now()

                self.tasks[i] = task
                return self.save_tasks()

        logger.warning(f"Task with ID {task.id} not found")
        return False

    def delete_task(self, task_id: str) -> bool:
        """Delete a task from the todo list.

        Args:
            task_id: ID of the task to delete

        Returns:
            True if successful, False otherwise
        """
        self.load_tasks()

        initial_count = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.id != task_id]

        if len(self.tasks) < initial_count:
            return self.save_tasks()

        logger.warning(f"Task with ID {task_id} not found")
        return False

    def create_task_from_request(
        self,
        title: str,
        description: str,
        priority: Union[str, TaskPriority] = TaskPriority.MEDIUM,
        related_files: List[str] = None,
    ) -> Task:
        """Create a new task from a user request.

        Args:
            title: Task title
            description: Task description
            priority: Task priority
            related_files: List of related file paths

        Returns:
            Created Task object
        """
        # Convert string priority to enum if needed
        if isinstance(priority, str):
            priority = TaskPriority(priority)

        task = Task(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            priority=priority,
            status=TaskStatus.PENDING,
            related_files=related_files or [],
            approach_suggestions=[],
            estimated_effort="Medium",
            source="request",
        )

        # Add the task to the list
        self.add_task(task)

        return task

    def create_tasks_from_violations(
        self, violations: List[Dict[str, Any]], file_path: str
    ) -> List[Task]:
        """Create tasks from code violations.

        Args:
            violations: List of violation dictionaries
            file_path: Path to the file with violations

        Returns:
            List of created Task objects
        """
        self.load_tasks()
        created_tasks = []

        for violation in violations:
            task = create_task_from_violation(violation, file_path)

            # Check if a similar task already exists
            duplicate = False
            for existing_task in self.tasks:
                if (
                    existing_task.status != TaskStatus.COMPLETED
                    and existing_task.title == task.title
                    and file_path in existing_task.related_files
                ):
                    duplicate = True
                    break

            if not duplicate:
                self.add_task(task)
                created_tasks.append(task)

        return created_tasks

    def get_next_task(self) -> Optional[Task]:
        """Get the next highest priority pending task.

        Returns:
            Highest priority pending Task, or None if no pending tasks
        """
        self.load_tasks()

        # Filter for pending tasks
        pending_tasks = [t for t in self.tasks if t.status == TaskStatus.PENDING]

        if not pending_tasks:
            return None

        # Sort by priority (HIGH > MEDIUM > LOW)
        sorted_tasks = sorted(
            pending_tasks,
            key=lambda t: -["LOW", "MEDIUM", "HIGH"].index(t.priority.value),
        )

        return sorted_tasks[0] if sorted_tasks else None

    def complete_task(self, task_id: str, skip: bool = False) -> bool:
        """Mark a task as completed or skipped.

        Args:
            task_id: ID of the task to complete
            skip: Whether to mark as skipped instead of completed

        Returns:
            True if successful, False otherwise
        """
        task = self.get_task_by_id(task_id)

        if not task:
            logger.warning(f"Task with ID {task_id} not found")
            return False

        task.status = TaskStatus.SKIPPED if skip else TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        task.updated_at = datetime.now()

        return self.update_task(task)

    def get_task_stats(self) -> Dict[str, Any]:
        """Get statistics about the tasks.

        Returns:
            Dictionary of task statistics
        """
        self.load_tasks()

        # Count tasks by status
        pending_count = sum(1 for t in self.tasks if t.status == TaskStatus.PENDING)
        in_progress_count = sum(
            1 for t in self.tasks if t.status == TaskStatus.IN_PROGRESS
        )
        completed_count = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        skipped_count = sum(1 for t in self.tasks if t.status == TaskStatus.SKIPPED)

        # Count tasks by priority
        high_priority = sum(1 for t in self.tasks if t.priority == TaskPriority.HIGH)
        medium_priority = sum(
            1 for t in self.tasks if t.priority == TaskPriority.MEDIUM
        )
        low_priority = sum(1 for t in self.tasks if t.priority == TaskPriority.LOW)

        # Count tasks by source
        manual_tasks = sum(1 for t in self.tasks if t.source == "manual")
        violation_tasks = sum(1 for t in self.tasks if t.source == "violation")
        request_tasks = sum(1 for t in self.tasks if t.source == "request")

        return {
            "total": len(self.tasks),
            "by_status": {
                "pending": pending_count,
                "in_progress": in_progress_count,
                "completed": completed_count,
                "skipped": skipped_count,
            },
            "by_priority": {
                "high": high_priority,
                "medium": medium_priority,
                "low": low_priority,
            },
            "by_source": {
                "manual": manual_tasks,
                "violation": violation_tasks,
                "request": request_tasks,
            },
            "completion_rate": (
                (completed_count / len(self.tasks)) * 100 if self.tasks else 0
            ),
        }
