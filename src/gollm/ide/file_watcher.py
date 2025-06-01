import asyncio
import os
import time
from pathlib import Path
from typing import Set, Callable, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class GollmFileHandler(FileSystemEventHandler):
    """Handler dla zdarzeń systemu plików"""
    
    def __init__(self, callback: Callable[[str, str], None]):
        self.callback = callback
        self.python_extensions = {'.py'}
        self.last_modified = {}
        self.debounce_time = 0.5  # 500ms debounce
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        if not self._is_python_file(file_path):
            return
        
        # Debouncing - ignoruj szybkie zmiany
        current_time = time.time()
        if file_path in self.last_modified:
            if current_time - self.last_modified[file_path] < self.debounce_time:
                return
        
        self.last_modified[file_path] = current_time
        self.callback(file_path, "modified")
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        if self._is_python_file(file_path):
            self.callback(file_path, "created")
    
    def _is_python_file(self, file_path: str) -> bool:
        """Sprawdza czy plik to Python"""
        return Path(file_path).suffix in self.python_extensions

class FileWatcher:
    """Monitoruje zmiany plików w projekcie"""
    
    def __init__(self, project_root: str, gollm_core):
        self.project_root = Path(project_root)
        self.gollm_core = gollm_core
        self.observer = Observer()
        self.is_watching = False
        self.exclude_patterns = {
            '__pycache__',
            '.git',
            '.venv',
            'venv',
            '.pytest_cache',
            '.gollm/cache'
        }
    
    def start_watching(self):
        """Rozpoczyna monitorowanie plików"""
        if self.is_watching:
            return
        
        handler = GollmFileHandler(self._on_file_changed)
        
        # Monitoruj główny katalog
        self.observer.schedule(
            handler,
            str(self.project_root),
            recursive=True
        )
        
        self.observer.start()
        self.is_watching = True
        print(f"🔍 goLLM file watcher started for {self.project_root}")
    
    def stop_watching(self):
        """Zatrzymuje monitorowanie plików"""
        if not self.is_watching:
            return
        
        self.observer.stop()
        self.observer.join()
        self.is_watching = False
        print("🛑 goLLM file watcher stopped")
    
    def _on_file_changed(self, file_path: str, event_type: str):
        """Callback wywoływany przy zmianie pliku"""
        try:
            # Sprawdź czy plik nie jest w wykluczonych katalogach
            if any(pattern in file_path for pattern in self.exclude_patterns):
                return
            
            print(f"📝 File {event_type}: {file_path}")
            
            # Waliduj plik
            result = self.gollm_core.validate_file(file_path)
            
            violations_count = len(result.get('violations', []))
            if violations_count > 0:
                print(f"❌ Found {violations_count} violations in {file_path}")
                
                # Utwórz zadania TODO z naruszeń
                if hasattr(self.gollm_core, 'todo_manager'):
                    for violation in result['violations'][:3]:  # Max 3 zadania na plik
                        self.gollm_core.todo_manager.add_task_from_violation(
                            violation.type,
                            {
                                'file_path': file_path,
                                'line_number': violation.line_number,
                                'message': violation.message
                            }
                        )
            else:
                print(f"✅ No violations in {file_path}")
                
        except Exception as e:
            print(f"⚠️ Error processing {file_path}: {e}")
    
    def __enter__(self):
        self.start_watching()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_watching()

# src/gollm/ide/__init__.py
"""
IDE Integration module for goLLM

Provides integration with popular IDEs including:
- Visual Studio Code
- Language Server Protocol support  
- File watching and real-time validation
"""

from .vscode_extension import VSCodeExtension
from .language_server import GollmLanguageServer
from .file_watcher import FileWatcher

__all__ = [
    "VSCodeExtension",
    "GollmLanguageServer", 
    "FileWatcher"
]