
# src/gollm/project_management/task_prioritizer.py
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class TaskContext:
    current_error: Optional[Dict] = None
    recent_changes: List[str] = None
    quality_score: int = 0
    
    def __post_init__(self):
        if self.recent_changes is None:
            self.recent_changes = []

class TaskPrioritizer:
    """Inteligentnie priorytetyzuje zadania na podstawie kontekstu"""
    
    def __init__(self):
        self.priority_weights = {
            "blocks_execution": 10,
            "high_frequency_error": 8,
            "quick_win": 6,
            "quality_impact": 4,
            "technical_debt": 2
        }
    
    def rank_tasks(self, tasks: List[Dict], context: TaskContext) -> List[Dict]:
        """Sortuje zadania według priorytetu z uwzględnieniem kontekstu"""
        scored_tasks = []
        
        for task in tasks:
            score = self._calculate_task_score(task, context)
            scored_tasks.append((task, score))
        
        # Sortuj według wyniku (malejąco)
        scored_tasks.sort(key=lambda x: x[1], reverse=True)
        
        return [task for task, score in scored_tasks]
    
    def _calculate_task_score(self, task: Dict, context: TaskContext) -> float:
        """Oblicza wynik priorytetu dla zadania"""
        score = 0.0
        
        # Podstawowy priorytet
        priority_scores = {"HIGH": 10, "MEDIUM": 5, "LOW": 1}
        score += priority_scores.get(task.get('priority', 'LOW'), 1)
        
        # Czy zadanie może naprawić aktualny błąd?
        if context.current_error and self._task_addresses_error(task, context.current_error):
            score += self.priority_weights["blocks_execution"]
        
        # Czy to szybka poprawka?
        if self._is_quick_win(task):
            score += self.priority_weights["quick_win"]
        
        # Wpływ na jakość
        quality_impact = self._estimate_quality_impact(task)
        score += quality_impact * self.priority_weights["quality_impact"]
        
        return score
    
    def _task_addresses_error(self, task: Dict, error: Dict) -> bool:
        """Sprawdza czy zadanie może naprawić aktualny błąd"""
        task_files = task.get('related_files', [])
        error_file = error.get('file_path', '')
        
        return error_file in task_files
    
    def _is_quick_win(self, task: Dict) -> bool:
        """Sprawdza czy zadanie to szybka poprawka"""
        effort = task.get('estimated_effort', '')
        quick_indicators = ['5-10 minutes', '15-30 minutes', 'minutes']
        
        return any(indicator in effort for indicator in quick_indicators)
    
    def _estimate_quality_impact(self, task: Dict) -> float:
        """Szacuje wpływ zadania na jakość kodu (0-1)"""
        high_impact_types = ['high_complexity', 'file_too_long', 'too_many_parameters']
        medium_impact_types = ['function_too_long', 'missing_docstring']
        
        task_title = task.get('title', '').lower()
        
        for high_type in high_impact_types:
            if high_type.replace('_', ' ') in task_title:
                return 1.0
        
        for medium_type in medium_impact_types:
            if medium_type.replace('_', ' ') in task_title:
                return 0.6
        
        return 0.3