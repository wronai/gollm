
# src/gollm/validation/execution_monitor.py
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ExecutionResult:
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    memory_usage: Optional[int] = None
    traceback: Optional[str] = None

class ExecutionMonitor:
    """Monitoruje wykonanie kodu i zbiera metryki"""
    
    def __init__(self, config):
        self.config = config
        self.execution_history = []
    
    def run_with_capture(self, command: str, working_dir: str = ".", timeout: int = 30) -> ExecutionResult:
        """Uruchamia komendę z przechwytywaniem wszystkich danych"""
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command.split(),
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            execution_result = ExecutionResult(
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=execution_time,
                traceback=self._extract_traceback(result.stderr)
            )
            
            self.execution_history.append(execution_result)
            return execution_result
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                exit_code=124,
                stdout="",
                stderr=f"Execution timeout after {timeout} seconds",
                execution_time=timeout
            )
        except Exception as e:
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr=str(e),
                execution_time=time.time() - start_time
            )
    
    def _extract_traceback(self, stderr: str) -> Optional[str]:
        """Wyodrębnia traceback z stderr"""
        lines = stderr.split('\n')
        traceback_lines = []
        capturing = False
        
        for line in lines:
            if line.startswith('Traceback'):
                capturing = True
            if capturing:
                traceback_lines.append(line)
        
        return '\n'.join(traceback_lines) if traceback_lines else None