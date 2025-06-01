# src/gollm/logging/log_aggregator.py
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from .log_parser import LogParser
from .execution_capture import ExecutionCapture

@dataclass
class ExecutionContext:
    command: str
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    timestamp: str
    file_path: Optional[str] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    traceback: Optional[str] = None

class LogAggregator:
    """Agreguje i analizuje logi wykonania"""
    
    def __init__(self, config):
        self.config = config
        self.log_parser = LogParser()
        self.execution_capture = ExecutionCapture()
        self.logs_dir = Path(".gollm/cache/execution_logs")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.execution_history: List[ExecutionContext] = []
        self._load_history()
    
    def capture_execution(self, command: str, working_dir: str = ".") -> ExecutionContext:
        """Przechwytuje wykonanie komendy i analizuje wyniki"""
        
        # Wykonaj komendę z przechwytywaniem
        result = self.execution_capture.run_command(command, working_dir)
        
        # Parsuj logi
        parsed_error = None
        if result.stderr:
            parsed_error = self.log_parser.parse_error(result.stderr)
        
        # Utwórz kontekst
        context = ExecutionContext(
            command=command,
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            execution_time=result.execution_time,
            timestamp=datetime.now().isoformat(),
            error_type=parsed_error.get('type') if parsed_error else None,
            error_message=parsed_error.get('message') if parsed_error else None,
            traceback=parsed_error.get('traceback') if parsed_error else None
        )
        
        # Dodaj do historii
        self.execution_history.append(context)
        self._save_execution_log(context)
        
        return context
    
    def get_latest_execution_context(self) -> Dict[str, Any]:
        """Zwraca kontekst ostatniego wykonania"""
        if not self.execution_history:
            return {"status": "no_executions"}
        
        latest = self.execution_history[-1]
        
        context = {
            "last_execution": asdict(latest),
            "error_patterns": self._analyze_error_patterns(),
            "frequent_failures": self._get_frequent_failures(),
            "execution_trends": self._analyze_execution_trends()
        }
        
        return context
    
    def _analyze_error_patterns(self) -> List[Dict[str, Any]]:
        """Analizuje wzorce błędów"""
        error_counts = {}
        
        # Zbierz błędy z ostatnich 24h
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for execution in self.execution_history:
            exec_time = datetime.fromisoformat(execution.timestamp)
            if exec_time < cutoff_time:
                continue
            
            if execution.error_type:
                key = f"{execution.error_type}:{execution.error_message}"
                error_counts[key] = error_counts.get(key, 0) + 1
        
        # Sortuj według częstotliwości
        patterns = []
        for error_key, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
            error_type, error_message = error_key.split(':', 1)
            patterns.append({
                "error_type": error_type,
                "error_message": error_message,
                "frequency": count,
                "impact": "high" if count > 5 else "medium" if count > 2 else "low"
            })
        
        return patterns[:5]  # Top 5
    
    def _get_frequent_failures(self) -> List[str]:
        """Zwraca często niepowodzące się komendy"""
        command_failures = {}
        
        for execution in self.execution_history[-50:]:  # Ostatnie 50 wykonań
            if execution.exit_code != 0:
                cmd = execution.command.split()[0]  # Pierwsza część komendy
                command_failures[cmd] = command_failures.get(cmd, 0) + 1
        
        return [cmd for cmd, count in sorted(command_failures.items(), 
                                           key=lambda x: x[1], reverse=True)][:3]
    
    def _analyze_execution_trends(self) -> Dict[str, Any]:
        """Analizuje trendy wykonania"""
        if len(self.execution_history) < 2:
            return {"trend": "insufficient_data"}
        
        recent_executions = self.execution_history[-10:]
        success_rate = sum(1 for ex in recent_executions if ex.exit_code == 0) / len(recent_executions)
        avg_execution_time = sum(ex.execution_time for ex in recent_executions) / len(recent_executions)
        
        return {
            "success_rate": success_rate,
            "avg_execution_time": avg_execution_time,
            "total_executions": len(self.execution_history),
            "trend": "improving" if success_rate > 0.7 else "declining"
        }
    
    def _save_execution_log(self, context: ExecutionContext):
        """Zapisuje log wykonania do pliku"""
        log_file = self.logs_dir / f"execution_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(context)) + '\n')
    
    def _load_history(self):
        """Ładuje historię wykonań z ostatnich dni"""
        for log_file in sorted(self.logs_dir.glob("execution_*.jsonl"))[-7:]:  # Ostatnie 7 dni
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line.strip())
                            context = ExecutionContext(**data)
                            self.execution_history.append(context)
            except Exception:
                continue  # Ignoruj uszkodzone pliki logów
