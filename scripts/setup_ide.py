# scripts/setup_ide.py
#!/usr/bin/env python3
"""
Konfiguruje integrację goLLM z IDE
"""

import json
import os
from pathlib import Path

def setup_vscode():
    """Konfiguruje VS Code dla goLLM"""
    
    vscode_dir = Path.cwd() / ".vscode"
    vscode_dir.mkdir(exist_ok=True)
    
    # settings.json
    settings = {
        "python.linting.enabled": True,
        "python.linting.gollmEnabled": True,
        "python.linting.gollmPath": "gollm",
        "python.linting.gollmArgs": ["validate"],
        "files.saveFormat": "gollm-format",
        "editor.formatOnSave": True,
        "editor.codeActionsOnSave": {
            "source.organizeImports": True,
            "source.fixAll.gollm": True
        },
        "gollm.realTimeValidation": True,
        "gollm.blockSaveOnViolations": True,
        "gollm.autoFixOnSave": True
    }
    
    settings_file = vscode_dir / "settings.json"
    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=2)
    
    # tasks.json
    tasks = {
        "version": "2.0.0",
        "tasks": [
            {
                "label": "goLLM: Validate Project",
                "type": "shell",
                "command": "gollm",
                "args": ["validate-project"],
                "group": "build",
                "presentation": {
                    "echo": True,
                    "reveal": "always",
                    "focus": False,
                    "panel": "shared"
                }
            },
            {
                "label": "goLLM: Fix All Issues",
                "type": "shell", 
                "command": "gollm",
                "args": ["fix", "--auto"],
                "group": "build"
            },
            {
                "label": "goLLM: Show Status",
                "type": "shell",
                "command": "gollm", 
                "args": ["status"],
                "group": "build"
            }
        ]
    }
    
    tasks_file = vscode_dir / "tasks.json"
    with open(tasks_file, 'w') as f:
        json.dump(tasks, f, indent=2)
    
    # launch.json dla debugowania
    launch = {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "goLLM: Debug Validation",
                "type": "python",
                "request": "launch",
                "module": "gollm.cli",
                "args": ["validate-project", "--debug"],
                "console": "integratedTerminal"
            }
        ]
    }
    
    launch_file = vscode_dir / "launch.json"
    with open(launch_file, 'w') as f:
        json.dump(launch, f, indent=2)
    
    print("✅ VS Code configuration created")
    print(f"📁 Config location: {vscode_dir}")
    print("💡 Install the goLLM VS Code extension for full integration")

def setup_ide(editor="vscode"):
    """Główna funkcja konfiguracji IDE"""
    
    if editor.lower() == "vscode":
        setup_vscode()
    else:
        print(f"❌ IDE '{editor}' not yet supported")
        print("🔧 Supported IDEs: vscode")
        return False
    
    return True

if __name__ == "__main__":
    import sys
    editor = sys.argv[1] if len(sys.argv) > 1 else "vscode"
    setup_ide(editor)
