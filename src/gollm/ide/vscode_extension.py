# src/gollm/ide/vscode_extension.py
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

class VSCodeExtension:
    """Integracja z Visual Studio Code"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.vscode_dir = self.project_root / ".vscode"
    
    def setup_integration(self) -> bool:
        """Konfiguruje integrację z VS Code"""
        try:
            self.vscode_dir.mkdir(exist_ok=True)
            
            # Utwórz wszystkie pliki konfiguracyjne
            self._create_settings()
            self._create_tasks()
            self._create_launch_config()
            self._create_extensions_recommendations()
            
            return True
        except Exception:
            return False
    
    def _create_settings(self):
        """Tworzy settings.json dla VS Code"""
        settings = {
            "python.defaultInterpreterPath": "./venv/bin/python",
            "python.linting.enabled": True,
            "python.linting.pylintEnabled": False,
            "python.linting.flake8Enabled": True,
            "python.linting.mypyEnabled": True,
            "python.formatting.provider": "black",
            "python.formatting.blackPath": "./venv/bin/black",
            "editor.formatOnSave": True,
            "editor.codeActionsOnSave": {
                "source.organizeImports": True,
                "source.fixAll": True
            },
            "files.associations": {
                "gollm.json": "jsonc"
            },
            "gollm.enabled": True,
            "gollm.validateOnSave": True,
            "gollm.validateOnType": True,
            "gollm.blockSaveOnViolations": True,
            "gollm.autoFixOnSave": True,
            "gollm.showQualityScore": True,
            "gollm.llmIntegration": True
        }
        
        settings_file = self.vscode_dir / "settings.json"
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
    
    def _create_tasks(self):
        """Tworzy tasks.json dla VS Code"""
        tasks = {
            "version": "2.0.0",
            "tasks": [
                {
                    "label": "goLLM: Validate Project",
                    "type": "shell",
                    "command": "${workspaceFolder}/venv/bin/python",
                    "args": ["-m", "gollm", "validate-project"],
                    "group": {
                        "kind": "build",
                        "isDefault": True
                    },
                    "presentation": {
                        "echo": True,
                        "reveal": "always",
                        "focus": False,
                        "panel": "shared",
                        "showReuseMessage": True,
                        "clear": False
                    },
                    "problemMatcher": []
                },
                {
                    "label": "goLLM: Show Status",
                    "type": "shell",
                    "command": "${workspaceFolder}/venv/bin/python",
                    "args": ["-m", "gollm", "status"],
                    "group": "build",
                    "presentation": {
                        "echo": True,
                        "reveal": "always",
                        "focus": true,
                        "panel": "shared"
                    }
                },
                {
                    "label": "goLLM: Auto Fix",
                    "type": "shell",
                    "command": "${workspaceFolder}/venv/bin/python",
                    "args": ["-m", "gollm", "fix", "--auto"],
                    "group": "build",
                    "presentation": {
                        "echo": True,
                        "reveal": "always",
                        "focus": true,
                        "panel": "shared"
                    }
                },
                {
                    "label": "goLLM: Next Task",
                    "type": "shell",
                    "command": "${workspaceFolder}/venv/bin/python",
                    "args": ["-m", "gollm", "next-task"],
                    "group": "build"
                },
                {
                    "label": "goLLM: Generate Code",
                    "type": "shell",
                    "command": "${workspaceFolder}/venv/bin/python",
                    "args": ["-m", "gollm", "generate", "${input:promptText}"],
                    "group": "build"
                }
            ],
            "inputs": [
                {
                    "id": "promptText",
                    "description": "Enter your code generation prompt",
                    "default": "Create a function to...",
                    "type": "promptString"
                }
            ]
        }
        
        tasks_file = self.vscode_dir / "tasks.json"
        with open(tasks_file, 'w') as f:
            json.dump(tasks, f, indent=2)
    
    def _create_launch_config(self):
        """Tworzy launch.json dla debugowania"""
        launch = {
            "version": "0.2.0",
            "configurations": [
                {
                    "name": "goLLM: Debug Validation",
                    "type": "python",
                    "request": "launch",
                    "module": "gollm.cli",
                    "args": ["validate-project", "--debug"],
                    "console": "integratedTerminal",
                    "cwd": "${workspaceFolder}",
                    "env": {
                        "PYTHONPATH": "${workspaceFolder}/src"
                    }
                },
                {
                    "name": "goLLM: Debug LLM",
                    "type": "python",
                    "request": "launch", 
                    "module": "gollm.cli",
                    "args": ["generate", "test function"],
                    "console": "integratedTerminal",
                    "cwd": "${workspaceFolder}",
                    "env": {
                        "PYTHONPATH": "${workspaceFolder}/src"
                    }
                },
                {
                    "name": "Python: Current File",
                    "type": "python",
                    "request": "launch",
                    "program": "${file}",
                    "console": "integratedTerminal",
                    "cwd": "${workspaceFolder}"
                }
            ]
        }
        
        launch_file = self.vscode_dir / "launch.json"
        with open(launch_file, 'w') as f:
            json.dump(launch, f, indent=2)
    
    def _create_extensions_recommendations(self):
        """Tworzy rekomendacje rozszerzeń"""
        extensions = {
            "recommendations": [
                "ms-python.python",
                "ms-python.flake8",
                "ms-python.mypy-type-checker",
                "ms-python.black-formatter",
                "ms-python.isort",
                "ms-vscode.vscode-json",
                "redhat.vscode-yaml",
                "eamodio.gitlens",
                "github.copilot"
            ]
        }
        
        extensions_file = self.vscode_dir / "extensions.json"
        with open(extensions_file, 'w') as f:
            json.dump(extensions, f, indent=2)
