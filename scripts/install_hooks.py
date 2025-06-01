#!/usr/bin/env python3
"""
Instaluje Git hooks dla goLLM
"""

import os
import shutil
from pathlib import Path

def install_git_hooks():
    """Instaluje Git hooks dla automatycznej walidacji"""
    
    project_root = Path.cwd()
    git_hooks_dir = project_root / ".git" / "hooks"
    gollm_hooks_dir = project_root / ".gollm" / "hooks"
    
    if not git_hooks_dir.exists():
        print("❌ Git repository not found. Initialize git first with 'git init'")
        return False
    
    # Utwórz katalog dla hooków goLLM jeśli nie istnieje
    gollm_hooks_dir.mkdir(parents=True, exist_ok=True)
    
    # Pre-commit hook
    pre_commit_content = '''#!/bin/sh
# goLLM Pre-commit Hook
echo "🔍 goLLM: Validating staged files..."

# Uruchom walidację goLLM
python -m gollm validate-project --staged-only

if [ $? -ne 0 ]; then
    echo "❌ goLLM validation failed. Fix issues before committing."
    echo "💡 Run 'gollm status' for details or 'gollm fix --auto' for auto-fixes"
    exit 1
fi

echo "✅ goLLM validation passed"
exit 0
'''
    
    # Post-commit hook
    post_commit_content = '''#!/bin/sh
# goLLM Post-commit Hook
echo "📝 goLLM: Updating project documentation..."

# Aktualizuj CHANGELOG z commit info
python -m gollm changelog update-from-commit

echo "✅ goLLM documentation updated"
'''
    
    # Zapisz hooki
    hooks_to_install = [
        ("pre-commit", pre_commit_content),
        ("post-commit", post_commit_content)
    ]
    
    for hook_name, hook_content in hooks_to_install:
        hook_path = git_hooks_dir / hook_name
        
        # Backup istniejącego hooka
        if hook_path.exists():
            backup_path = git_hooks_dir / f"{hook_name}.backup"
            shutil.copy2(hook_path, backup_path)
            print(f"📁 Backed up existing {hook_name} to {hook_name}.backup")
        
        # Zapisz nowy hook
        with open(hook_path, 'w') as f:
            f.write(hook_content)
        
        # Ustaw uprawnienia wykonania
        os.chmod(hook_path, 0o755)
        
        print(f"✅ Installed {hook_name} hook")
    
    print(f"🎉 goLLM Git hooks installed successfully!")
    print(f"📁 Hooks location: {git_hooks_dir}")
    return True

if __name__ == "__main__":
    install_git_hooks()

