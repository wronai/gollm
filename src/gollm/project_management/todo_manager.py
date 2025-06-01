# src/gollm/project_management/todo_manager.py
import re
import os
import json
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
            "too_many_parameters": "45-90 minutes",
            "code_generation": "15-60 minutes",
            "code_review": "10-30 minutes"
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
        pending = [t for t in self.tasks if t.status == "pending"]
        completed = [t for t in self.tasks if t.status == "completed"]
        high_priority = [t for t in self.tasks 
                       if t.status == "pending" and t.priority == "HIGH"]
        code_gen_tasks = [t for t in self.tasks if t.id.startswith("gen-")]
        
        return {
            "total": len(self.tasks),
            "pending": len(pending),
            "completed": len(completed),
            "high_priority": len(high_priority),
            "code_generation_tasks": len(code_gen_tasks)
        }
    
    def _save_tasks(self):
        """Zapisuje zadania do pliku TODO.md"""
        content = self._generate_todo_content()
        with open(self.todo_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _format_description(self, description: str, context: Dict[str, Any]) -> str:
        """Formatuje opis zadania w czytelny sposób"""
        lines = [f"{description}"]
        
        # Dodaj kontekst w formie punktowanej listy
        if context:
            lines.append("\n**Context:**")
            
            # Obsłuż różne typy kontekstu
            if 'request' in context:
                lines.append(f"- Task: {context['request']}")
                
            if 'context' in context and isinstance(context['context'], dict):
                ctx = context['context']
                if 'is_critical' in ctx:
                    lines.append(f"- Priority: {'🔴 HIGH' if ctx['is_critical'] else '🟡 MEDIUM'}")
                if 'related_files' in ctx and ctx['related_files']:
                    files = ", ".join(f'`{f}`' for f in ctx['related_files'] if f)
                    lines.append(f"- Related files: {files}")
        
        return "\n".join(lines)

    def add_code_generation_task(self, description: str, context: Dict[str, Any]) -> Task:
        """Dodaje zadanie generowania kodu"""
        task = Task(
            id=f"gen-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            title=f"[CodeGen] {description[:50]}",
            description=self._format_description(description, context),
            priority="HIGH" if context.get('is_critical') else "MEDIUM",
            created_at=datetime.now().isoformat(),
            estimated_effort=self._estimate_effort("code_generation"),
            related_files=context.get('related_files', [])
        )
        self.tasks.append(task)
        self._save_tasks()
        return task

    def _format_result_details(self, result: Dict[str, Any]) -> str:
        """Formatuje szczegóły wyniku w czytelny sposób"""
        lines = []
        
        if 'output_file' in result and result['output_file'] != 'unknown.py':
            lines.append(f"- 📄 **Output file:** `{result['output_file']}`")
            
        if 'quality_score' in result:
            score = result['quality_score']
            emoji = "🟢" if score >= 90 else "🟡" if score >= 70 else "🔴"
            lines.append(f"- {emoji} **Code quality:** {score}/100")
        
        if 'violations' in result and result['violations']:
            lines.append("\n**Fixed issues:**")
            for violation in result['violations']:
                v_type = violation.get('type', 'Issue')
                v_msg = violation.get('message', 'No details')
                lines.append(f"  - {v_type}: {v_msg}")
        
        return "\n".join(lines)

    def update_code_generation_task(self, task_id: str, result: Dict[str, Any]):
        """Aktualizuje zadanie po wygenerowaniu kodu"""
        for task in self.tasks:
            if task.id == task_id:
                result_details = self._format_result_details(result)
                if result_details:
                    task.description += "\n\n" + result_details
                
                task.status = "completed"
                self._save_tasks()
                return True
        return False

    def _generate_todo_content(self) -> str:
        """Generuje zawartość pliku TODO.md"""
        stats = self.get_stats()
        
        content = f"# 📋 TODO List - Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"**Status:** {stats['completed']}✓ {stats['pending']}⏳ • "
        content += f"**Priority:** {stats['high_priority']}🔴 • "
        content += f"**Code Gen:** {stats['code_generation_tasks']}🔄\n\n"
        
        # Grupuj zadania według priorytetu
        for priority, emoji in [("HIGH", "🔴"), ("MEDIUM", "🟡"), ("LOW", "🟢")]:
            priority_tasks = [t for t in self.tasks if t.priority == priority]
            
            if priority_tasks:
                content += f"## {emoji} {priority} Priority ({len(priority_tasks)} tasks)\n\n"
                
                for task in priority_tasks:
                    status_emoji = "✅" if task.status == "completed" else "⏳"
                    content += f"- [{'x' if task.status == 'completed' else ' '}] **{status_emoji} {task.title}**"
                    
                    if task.id.startswith("gen-") and task.status == "pending":
                        content += " 🆕"
                    
                    content += "\n"
                    
                    if task.description:
                        for line in task.description.split('\n'):
                            if line.strip():
                                content += f"  - {line.strip()}\n"
                    
                    if task.estimated_effort:
                        content += f"  - ⏱️ **Effort:** {task.estimated_effort}\n"
                    
                    if task.approach_suggestions:
                        content += f"  - 💡 **Suggestions:** {', '.join(task.approach_suggestions)}\n"
                    
                    if task.related_files:
                        files = ", ".join(f"`{f}`" for f in task.related_files if f)
                        if files:
                            content += f"  - 📂 **Files:** {files}\n"
                    
                    content += "\n"
        
        # Dodaj statystyki na dole
        content += "---\n"
        content += "*This file is automatically managed by goLLM* • "
        content += f"*{stats['completed']} of {stats['total']} tasks completed*"
        
        return content
