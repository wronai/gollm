"""
Git hooks management for goLLM
"""

import os
import stat
from pathlib import Path
from typing import Dict, List


class GitHooks:
    """Manages Git hooks for goLLM integration"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.git_hooks_dir = self.project_root / ".git" / "hooks"
        self.gollm_hooks_dir = self.project_root / ".gollm" / "hooks"

    def install_hooks(self) -> bool:
        """Installs goLLM Git hooks"""
        if not self.git_hooks_dir.exists():
            return False

        hooks = {
            "pre-commit": self._get_pre_commit_script(),
            "post-commit": self._get_post_commit_script(),
            "pre-push": self._get_pre_push_script(),
        }

        for hook_name, script_content in hooks.items():
            hook_path = self.git_hooks_dir / hook_name

            # Backup existing hook
            if hook_path.exists():
                backup_path = self.git_hooks_dir / f"{hook_name}.backup"
                hook_path.rename(backup_path)

            # Install new hook
            with open(hook_path, "w") as f:
                f.write(script_content)

            # Make executable
            os.chmod(hook_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)

        return True

    def _get_pre_commit_script(self) -> str:
        """Returns pre-commit hook script"""
        return """#!/bin/sh
# goLLM Pre-commit Hook
echo "🔍 goLLM: Validating staged files..."

STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\\.py$')

if [ -z "$STAGED_FILES" ]; then
    echo "✅ No Python files to validate"
    exit 0
fi

VALIDATION_FAILED=0
for file in $STAGED_FILES; do
    echo "Validating: $file"
    python -m gollm validate "$file" --quiet
    if [ $? -ne 0 ]; then
        VALIDATION_FAILED=1
        echo "❌ Validation failed for: $file"
    fi
done

if [ $VALIDATION_FAILED -eq 1 ]; then
    echo "❌ goLLM validation failed"
    echo "💡 Fix with: gollm fix --auto"
    exit 1
fi

echo "✅ All staged files passed validation"
exit 0
"""

    def _get_post_commit_script(self) -> str:
        """Returns post-commit hook script"""
        return """#!/bin/sh
# goLLM Post-commit Hook
echo "📝 goLLM: Updating documentation..."

COMMIT_HASH=$(git rev-parse HEAD)
COMMIT_MSG=$(git log -1 --pretty=%B)

python -m gollm changelog add-commit-entry --hash "$COMMIT_HASH" --message "$COMMIT_MSG"
python -m gollm todo update-from-commit "$COMMIT_MSG"

echo "✅ Documentation updated"
"""

    def _get_pre_push_script(self) -> str:
        """Returns pre-push hook script"""
        return """#!/bin/sh
# goLLM Pre-push Hook
echo "🚀 goLLM: Final validation..."

python -m gollm validate-project --strict
if [ $? -ne 0 ]; then
    echo "❌ Project validation failed"
    exit 1
fi

echo "✅ Ready to push"
exit 0
"""
