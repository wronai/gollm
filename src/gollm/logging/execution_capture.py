# src/gollm/logging/execution_capture.py
import os
import subprocess
import time
from dataclasses import dataclass
from typing import Optional

import psutil


@dataclass
class ExecutionResult:
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    memory_peak: Optional[int] = None


class ExecutionCapture:
    """Przechwytuje wykonanie procesów z metrykami"""

    def run_command(
        self, command: str, working_dir: str = ".", timeout: int = 60
    ) -> ExecutionResult:
        """Uruchamia komendę i przechwytuje wszystkie metryki"""

        start_time = time.time()
        memory_peak = 0

        try:
            # Uruchom proces
            process = subprocess.Popen(
                command.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=working_dir,
            )

            # Monitoruj wykorzystanie pamięci
            try:
                psutil_process = psutil.Process(process.pid)
                while process.poll() is None:
                    try:
                        memory_info = psutil_process.memory_info()
                        memory_peak = max(memory_peak, memory_info.rss)
                        time.sleep(0.1)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        break
            except Exception:
                pass  # Ignoruj błędy monitorowania pamięci

            # Czekaj na zakończenie
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                exit_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                exit_code = -1
                stderr += f"\nProcess killed due to timeout ({timeout}s)"

            execution_time = time.time() - start_time

            return ExecutionResult(
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                execution_time=execution_time,
                memory_peak=memory_peak if memory_peak > 0 else None,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr=f"Execution failed: {str(e)}",
                execution_time=execution_time,
            )
