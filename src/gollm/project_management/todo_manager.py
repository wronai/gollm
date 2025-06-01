# src/gollm/project_management/todo_manager.py
import re
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class Task:
    id: str
    title: str
    description: str
    priority: str
    status: str = "pending"
    created_at: str = ""
    estimated_effort: str = ""
    related_files: List[str] = None
    approach_suggestions: List[str] = None
    
    def __post_init__(self):
        if self.related_files is None:
            self.related_files = []
        if self.approach_suggestions is None:
            self.approach_suggestions = []

class TodoManager:
    """Zarządza listą TODO i automatycznie tworzy zadania z naruszeń"""
    
    def __init__(self, config):
        self.config = config
        self.todo_file = Path(config.project_management.todo_file)
        self.tasks = []
        self._load_tasks()
    
    def _load_tasks(self):
        """Ładuje zadania z pliku TODO.md"""
        if not self.todo_file.exists():
            self._create_default_todo_file()
            return
        
        with open(self.todo_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.tasks = self._parse_todo_content(content)
    
    def _create_default_todo_file(self):
        """Tworzy domyślny plik TODO.md"""
        template = """# TODO List - Project Tasks

## 🔴 HIGH Priority

## 🟡 MEDIUM Priority

## 🟢 LOW Priority

---
*This file is automatically managed by goLLM*
"""
        with open(self.todo_file, 'w', encoding='utf-8') as f:
            f.write(template)
    
    def _parse_todo_content(self, content: str) -> List[Task]:
        """Parsuje zawartość pliku TODO i zwraca listę zadań"""
        tasks = []
        current_priority = "LOW"
        
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Sprawdź sekcję priorytetów
            if '🔴' in line or 'HIGH' in line.upper():
                current_priority = "HIGH"
            elif '🟡' in line or 'MEDIUM' in line.upper():
                current_priority = "MEDIUM"
            elif '🟢' in line or 'LOW' in line.upper():
                current_priority = "LOW"
            
            # Sprawdź czy to zadanie
            task_match = re.match(r'- \[([ x])\] \*\*(.*?)\*\*', line)
            if task_match:
                status = "completed" if task_match.group(1) == 'x' else "pending"
                title = task_match.group(2)
                
                # Zbierz szczegóły zadania
                description_lines = []
                i += 1
                while i < len(lines) and lines[i].strip().startswith('-'):
                    description_lines.append(lines[i].strip()[1:].strip())
                    i += 1
                
                task = Task(
                    id=f"task-{len(tasks)+1:03d}",
                    title=title,
                    description='\n'.join(description_lines),
                    priority=current_priority,
                    status=status
                )
                tasks.append(task)
                continue
            
            i += 1
        
        return tasks
    
    def add_task_from_violation(self, violation_type: str, details: Dict[str, Any]) -> Task:
        """Tworzy zadanie na podstawie naruszenia jakości kodu"""
        priority_map = {
            "file_too_long": "HIGH",
            "function_too_long": "MEDIUM", 
            "forbidden_print": "MEDIUM",
            "missing_docstring": "LOW",
            "high_complexity": "HIGH",
            "too_many_parameters": "MEDIUM"
        }
        
        suggestion_map = {
            "file_too_long": ["Split into smaller modules", "Extract classes to separate files"],
            "function_too_long": ["Break into smaller functions", "Extract helper methods"],
            "forbidden_print": ["Replace with logging", "Use proper logging levels"],
            "missing_docstring": ["Add Google-style docstring", "Document parameters and return values"],
            "high_complexity": ["Simplify logic", "Extract sub-functions", "Use early returns"],
            "too_many_parameters": ["Use dataclass", "Create configuration object"]
        }
        
        priority = priority_map.get(violation_type, "MEDIUM")
        suggestions = suggestion_map.get(violation_type, [])
        
        task = Task(
            id=f"gollm-{datetime.now().strftime('%Y%m%d')}-{len(self.tasks)+1:03d}",
            title=f"Fix {violation_type.replace('_', ' ')} in {details.get('file_path', 'unknown')}",
            description=f"Location: {details.get('file_path')}:{details.get('line_number', 0)}\n" +
                       f"Issue: {details.get('message', 'No description')}\n" +
                       f"Auto-fix available: {'Yes' if details.get('auto_fix_available') else 'No'}",
            priority=priority,
            created_at=datetime.now().isoformat(),
            estimated_effort=self._estimate_effort(violation_type),
            related_files=[details.get('file_path', '')],
            approach_suggestions=suggestions
        )
        
        self.tasks.append(task)
        self._save_tasks()
        return task
    
    def _estimate_effort(self, violation_type: str) -> str:
        """Szacuje czas potrzebny na naprawę"""
        effort_map = {
            "file_too_long": "2-4 hours",
            "function_too_long": "30-60 minutes",
            "forbidden_print": "5-10 minutes",
            "missing_docstring": "15-30 minutes",
            "high_complexity": "1-3 hours",
            "too_many_parameters": "45-90 minutes"
        }
        return effort_map.get(violation_type, "30 minutes")
    
    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """Zwraca następne zadanie do wykonania"""
        pending_tasks = [t for t in self.tasks if t.status == "pending"]
        
        if not pending_tasks:
            return None
        
        # Sortuj według priorytetu
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        sorted_tasks = sorted(pending_tasks, 
                            key=lambda t: priority_order.get(t.priority, 3))
        
        next_task = sorted_tasks[0]
        return {
            "id": next_task.id,
            "title": next_task.title,
            "description": next_task.description,
            "priority": next_task.priority,
            "estimated_effort": next_task.estimated_effort,
            "related_files": next_task.related_files,
            "approach_suggestions": next_task.approach_suggestions
        }
    
    def complete_task(self, task_id: str):
        """Oznacza zadanie jako ukończone"""
        for task in self.tasks:
            if task.id == task_id:
                task.status = "completed"
                break
        self._save_tasks()
    
    def get_stats(self) -> Dict[str, int]:
        """Zwraca statystyki zadań"""
        pending = len([t for t in self.tasks if t.status == "pending"])
        completed = len([t for t in self.tasks if t.status == "completed"])
        high_priority = len([t for t in self.tasks 
                           if t.status == "pending" and t.priority == "HIGH"])
        
        return {
            "total": len(self.tasks),
            "pending": pending,
            "completed": completed,
            "high_priority": high_priority
        }
    
    def _save_tasks(self):
        """Zapisuje zadania do pliku TODO.md"""
        content = self._generate_todo_content()
        with open(self.todo_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_todo_content(self) -> str:
        """Generuje zawartość pliku TODO.md"""
        content = f"# TODO List - Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Grupuj zadania według priorytetu
        for priority, emoji in [("HIGH", "🔴"), ("MEDIUM", "🟡"), ("LOW", "🟢")]:
            priority_tasks = [t for t in self.tasks if t.priority == priority]
            
            if priority_tasks:
                content += f"## {emoji} {priority} Priority\n\n"
                
                for task in priority_tasks:
                    status_mark = "x" if task.status == "completed" else " "
                    content += f"- [{status_mark}] **{task.title}**\n"
                    
                    if task.description:
                        for line in task.description.split('\n'):
                            if line.strip():
                                content += f"  - {line.strip()}\n"
                    
                    if task.estimated_effort:
                        content += f"  - **Estimated Effort:** {task.estimated_effort}\n"
                    
                    if task.approach_suggestions:
                        content += f"  - **Suggested Approach:** {', '.join(task.approach_suggestions)}\n"
                    
                    content += "\n"
        
        content += "\n---\n*This file is automatically managed by goLLM*\n"
        return content
