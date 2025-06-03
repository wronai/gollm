"""Parsing utilities for todo files and task creation."""

import logging
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .models import Task, TaskPriority, TaskStatus

logger = logging.getLogger("gollm.todo.parser")


def parse_todo_file(file_path: str) -> List[Task]:
    """Parse a TODO.md file into a list of Task objects.

    Args:
        file_path: Path to the TODO.md file

    Returns:
        List of Task objects
    """
    tasks = []
    path = Path(file_path)

    if not path.exists():
        logger.warning(f"TODO file not found at {file_path}")
        return tasks

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract task sections using regex
        task_pattern = r"## \[(PENDING|IN_PROGRESS|COMPLETED|SKIPPED)\] (.+?)\n([\s\S]*?)(?=\n## \[|$)"
        task_matches = re.finditer(task_pattern, content)

        for match in task_matches:
            status_str, title, details = match.groups()
            status = TaskStatus(status_str)

            # Extract task ID
            id_match = re.search(r"ID: ([\w-]+)", details)
            task_id = id_match.group(1) if id_match else str(uuid.uuid4())

            # Extract priority
            priority_match = re.search(r"Priority: (LOW|MEDIUM|HIGH)", details)
            priority = (
                TaskPriority(priority_match.group(1))
                if priority_match
                else TaskPriority.MEDIUM
            )

            # Extract description
            description_match = re.search(
                r"### Description\n([\s\S]*?)(?=\n###|$)", details
            )
            description = (
                description_match.group(1).strip() if description_match else ""
            )

            # Extract related files
            related_files = []
            files_match = re.search(
                r"### Related Files\n([\s\S]*?)(?=\n###|$)", details
            )
            if files_match:
                files_content = files_match.group(1).strip()
                file_lines = files_content.split("\n")
                for line in file_lines:
                    if line.strip().startswith("- "):
                        file_path = line.strip()[2:].strip()
                        related_files.append(file_path)

            # Extract approach suggestions
            suggestions = []
            suggestions_match = re.search(
                r"### Approach\n([\s\S]*?)(?=\n###|$)", details
            )
            if suggestions_match:
                suggestions_content = suggestions_match.group(1).strip()
                suggestion_lines = suggestions_content.split("\n")
                for line in suggestion_lines:
                    if line.strip().startswith("- "):
                        suggestion = line.strip()[2:].strip()
                        suggestions.append(suggestion)

            # Extract dates
            created_match = re.search(
                r"Created: (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?)", details
            )
            created_at = (
                datetime.fromisoformat(created_match.group(1))
                if created_match
                else datetime.now()
            )

            updated_match = re.search(
                r"Updated: (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?)", details
            )
            updated_at = (
                datetime.fromisoformat(updated_match.group(1))
                if updated_match
                else None
            )

            completed_match = re.search(
                r"Completed: (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?)", details
            )
            completed_at = (
                datetime.fromisoformat(completed_match.group(1))
                if completed_match
                else None
            )

            # Extract effort
            effort_match = re.search(r"Estimated Effort: (\w+)", details)
            estimated_effort = effort_match.group(1) if effort_match else "Medium"

            # Extract source
            source_match = re.search(r"Source: (\w+)", details)
            source = source_match.group(1) if source_match else "manual"

            # Create task
            task = Task(
                id=task_id,
                title=title,
                description=description,
                priority=priority,
                status=status,
                related_files=related_files,
                approach_suggestions=suggestions,
                estimated_effort=estimated_effort,
                created_at=created_at,
                updated_at=updated_at,
                completed_at=completed_at,
                source=source,
            )

            tasks.append(task)

    except Exception as e:
        logger.error(f"Error parsing TODO file: {str(e)}")

    return tasks


def create_task_from_violation(violation: Dict[str, Any], file_path: str) -> Task:
    """Create a task from a code violation.

    Args:
        violation: Violation dictionary
        file_path: Path to the file with the violation

    Returns:
        Task object
    """
    violation_type = violation.get("type", "unknown")
    message = violation.get("message", "No description")
    line = violation.get("line_number", 0)

    # Generate a title based on violation type and file
    title = f"Fix {violation_type} in {Path(file_path).name}"

    # Generate a description
    description = f"Fix the following {violation_type} on line {line}:\n{message}"

    # Determine priority based on violation type
    priority = (
        TaskPriority.HIGH
        if violation_type == "error"
        else TaskPriority.MEDIUM if violation_type == "warning" else TaskPriority.LOW
    )

    # Generate suggestions based on violation type
    suggestions = []
    if "unused import" in message.lower():
        suggestions.append("Remove the unused import")
    elif "undefined name" in message.lower():
        suggestions.append("Define the variable or import the name")
    elif "line too long" in message.lower():
        suggestions.append("Break the line into multiple lines")
        suggestions.append("Use line continuation with backslashes or parentheses")

    return Task(
        id=str(uuid.uuid4()),
        title=title,
        description=description,
        priority=priority,
        status=TaskStatus.PENDING,
        related_files=[file_path],
        approach_suggestions=suggestions,
        estimated_effort="Low",
        source="violation",
    )
