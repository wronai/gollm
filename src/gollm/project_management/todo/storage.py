"""Storage utilities for todo tasks."""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from .models import Task
from .formatter import format_todo_file

logger = logging.getLogger('gollm.todo.storage')


def save_tasks_to_markdown(tasks: List[Task], file_path: str) -> bool:
    """Save tasks to a markdown file.
    
    Args:
        tasks: List of Task objects
        file_path: Path to save the markdown file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Format tasks as markdown
        content = format_todo_file(tasks)
        
        # Ensure directory exists
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to file
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info(f"Saved {len(tasks)} tasks to {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving tasks to markdown: {str(e)}")
        return False


def save_tasks_to_json(tasks: List[Task], file_path: str) -> bool:
    """Save tasks to a JSON file.
    
    Args:
        tasks: List of Task objects
        file_path: Path to save the JSON file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Convert tasks to dictionaries
        task_dicts = [task.to_dict() for task in tasks]
        
        # Ensure directory exists
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to file
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(task_dicts, f, indent=2)
            
        logger.info(f"Saved {len(tasks)} tasks to {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving tasks to JSON: {str(e)}")
        return False


def load_tasks_from_json(file_path: str) -> List[Task]:
    """Load tasks from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        List of Task objects
    """
    tasks = []
    path = Path(file_path)
    
    if not path.exists():
        logger.warning(f"JSON file not found at {file_path}")
        return tasks
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            task_dicts = json.load(f)
            
        tasks = [Task.from_dict(task_dict) for task_dict in task_dicts]
        logger.info(f"Loaded {len(tasks)} tasks from {file_path}")
        
    except Exception as e:
        logger.error(f"Error loading tasks from JSON: {str(e)}")
    
    return tasks
