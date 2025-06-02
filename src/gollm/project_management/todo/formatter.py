"""Formatting utilities for todo tasks."""

from datetime import datetime
from typing import List, Dict, Any

from .models import Task, TaskStatus


def format_task_for_markdown(task: Task) -> str:
    """Format a task for writing to a markdown file.
    
    Args:
        task: Task object to format
        
    Returns:
        Markdown formatted task string
    """
    # Format related files as bullet points
    related_files_str = ""
    if task.related_files:
        related_files_str = "\n".join([f"- {file}" for file in task.related_files])
    
    # Format approach suggestions as bullet points
    suggestions_str = ""
    if task.approach_suggestions:
        suggestions_str = "\n".join([f"- {suggestion}" for suggestion in task.approach_suggestions])
    
    # Format dates
    created_str = task.created_at.isoformat()
    updated_str = task.updated_at.isoformat() if task.updated_at else ""
    completed_str = task.completed_at.isoformat() if task.completed_at else ""
    
    # Build the markdown
    markdown = f"## [{task.status.value}] {task.title}\n"
    markdown += f"ID: {task.id}\n"
    markdown += f"Priority: {task.priority.value}\n"
    markdown += f"Estimated Effort: {task.estimated_effort}\n"
    markdown += f"Created: {created_str}\n"
    
    if updated_str:
        markdown += f"Updated: {updated_str}\n"
        
    if completed_str and task.status in [TaskStatus.COMPLETED, TaskStatus.SKIPPED]:
        markdown += f"Completed: {completed_str}\n"
    
    markdown += f"Source: {task.source}\n\n"
    
    # Add description section
    markdown += "### Description\n"
    markdown += f"{task.description}\n\n"
    
    # Add related files section
    markdown += "### Related Files\n"
    markdown += f"{related_files_str or 'None'}\n\n"
    
    # Add approach section
    markdown += "### Approach\n"
    markdown += f"{suggestions_str or 'No specific approach suggestions.'}\n"
    
    return markdown


def format_todo_file(tasks: List[Task]) -> str:
    """Format a list of tasks into a complete TODO.md file.
    
    Args:
        tasks: List of Task objects
        
    Returns:
        Formatted TODO.md file content
    """
    # Start with header
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = f"# TODO List\n\nLast updated: {now}\n\n"
    
    # Add summary section
    pending_count = sum(1 for task in tasks if task.status == TaskStatus.PENDING)
    in_progress_count = sum(1 for task in tasks if task.status == TaskStatus.IN_PROGRESS)
    completed_count = sum(1 for task in tasks if task.status == TaskStatus.COMPLETED)
    skipped_count = sum(1 for task in tasks if task.status == TaskStatus.SKIPPED)
    
    content += "## Summary\n"
    content += f"- Pending: {pending_count}\n"
    content += f"- In Progress: {in_progress_count}\n"
    content += f"- Completed: {completed_count}\n"
    content += f"- Skipped: {skipped_count}\n\n"
    
    # Sort tasks by status and priority
    sorted_tasks = sorted(
        tasks,
        key=lambda t: (
            # Order: PENDING, IN_PROGRESS, COMPLETED, SKIPPED
            [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, 
             TaskStatus.COMPLETED, TaskStatus.SKIPPED].index(t.status),
            # Then by priority (HIGH first)
            -['LOW', 'MEDIUM', 'HIGH'].index(t.priority.value),
            # Then by creation date (newest first)
            -t.created_at.timestamp() if t.created_at else 0
        )
    )
    
    # Add each task
    for task in sorted_tasks:
        content += format_task_for_markdown(task) + "\n\n"
    
    return content


def format_task_for_display(task: Task) -> str:
    """Format a task for terminal display.
    
    Args:
        task: Task object to format
        
    Returns:
        Formatted task string for display
    """
    # Priority emoji
    priority_emoji = "🔴" if task.priority.value == "HIGH" else \
                    "🟡" if task.priority.value == "MEDIUM" else "🟢"
    
    # Status emoji
    status_emoji = "⏳" if task.status == TaskStatus.IN_PROGRESS else \
                  "✅" if task.status == TaskStatus.COMPLETED else \
                  "⏭️" if task.status == TaskStatus.SKIPPED else "📋"
    
    # Format related files
    related_files = '\n  '.join(
        [f"- {f}" for f in task.related_files]
    ) if task.related_files else "None"
    
    # Format suggestions
    suggestions = '\n  '.join(
        [f"- {s}" for s in task.approach_suggestions]
    ) if task.approach_suggestions else "No suggestions"
    
    return f"""Task: {task.title}
{priority_emoji} Priority: {task.priority.value}
{status_emoji} Status: {task.status.value}
⏱️ Estimated effort: {task.estimated_effort}

📝 Description:
{task.description}

📂 Related files:
  {related_files}

💡 Suggested approach:
  {suggestions}
"""
