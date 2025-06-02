"""Data models for todo management."""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import List, Dict, Any, Optional


class TaskPriority(str, Enum):
    """Priority levels for tasks."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TaskStatus(str, Enum):
    """Status values for tasks."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"


@dataclass
class Task:
    """Represents a task in the todo list.
    
    A task can be created from code violations, user requests, or manually.
    It includes metadata about the task, related files, and suggestions for
    approaching the task.
    """
    id: str
    title: str
    description: str
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    related_files: List[str] = field(default_factory=list)
    approach_suggestions: List[str] = field(default_factory=list)
    estimated_effort: str = "Medium"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    source: str = "manual"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary representation.
        
        Returns:
            Dictionary representation of the task
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "related_files": self.related_files,
            "approach_suggestions": self.approach_suggestions,
            "estimated_effort": self.estimated_effort,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "source": self.source,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create a task from dictionary representation.
        
        Args:
            data: Dictionary representation of the task
            
        Returns:
            Task instance
        """
        # Convert string representations to enum values
        priority = TaskPriority(data.get("priority", TaskPriority.MEDIUM.value))
        status = TaskStatus(data.get("status", TaskStatus.PENDING.value))
        
        # Parse datetime strings
        created_at = datetime.fromisoformat(data.get("created_at")) if data.get("created_at") else datetime.now()
        updated_at = datetime.fromisoformat(data.get("updated_at")) if data.get("updated_at") else None
        completed_at = datetime.fromisoformat(data.get("completed_at")) if data.get("completed_at") else None
        
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            priority=priority,
            status=status,
            related_files=data.get("related_files", []),
            approach_suggestions=data.get("approach_suggestions", []),
            estimated_effort=data.get("estimated_effort", "Medium"),
            created_at=created_at,
            updated_at=updated_at,
            completed_at=completed_at,
            source=data.get("source", "manual"),
            metadata=data.get("metadata", {})
        )
