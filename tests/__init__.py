# tests/__init__.py
"""
Test suite for SPYQ - Smart Python Quality Guardian
"""

# tests/fixtures/sample_config.json
{
  "validation_rules": {
    "max_function_lines": 25,
    "max_file_lines": 200,
    "max_cyclomatic_complexity": 8,
    "forbid_print_statements": true,
    "forbid_global_variables": true,
    "require_docstrings": true,
    "max_function_params": 4,
    "naming_convention": "snake_case"
  },
  "project_management": {
    "todo_integration": true,
    "auto_create_tasks": true,
    "todo_file": "test_todo.md",
    "changelog_integration": true,
    "auto_update_changelog": true,
    "changelog_file": "test_changelog.md"
  },
  "llm_integration": {
    "enabled": false,
    "model_name": "test-model",
    "max_iterations": 2,
    "token_limit": 2000
  },
  "enforcement": {
    "block_save": false,
    "block_execution": false,
    "auto_fix_enabled": false
  }
}

# tests/fixtures/sample_todo.md
# Test TODO List - Updated: 2025-06-01 10:00:00

## 🔴 HIGH Priority

### Critical Issues
- [ ] **Fix function parameter count in user_processor.py**
  - **Created:** 2025-06-01 10:00:00
  - **Location:** `src/user_processor.py:15`
  - **Parameters:** 8 (max: 4)
  - **Estimated Effort:** 45 minutes

## 🟡 MEDIUM Priority

### Code Quality
- [ ] **Replace print statements with logging**
  - **Created:** 2025-06-01 10:00:00
  - **Files:** 3 files affected
  - **Auto-fix Available:** ✅ Yes

## 🟢 LOW Priority

### Documentation
- [ ] **Add missing docstrings to utility functions**
  - **Created:** 2025-06-01 10:00:00
  - **Functions:** 5 functions need documentation

---
*This file is automatically managed by SPYQ*

# tests/fixtures/sample_changelog.md
# Test Changelog

All notable changes to this test project will be documented in this file.

## [Unreleased] - 2025-06-01

### Added
- **[SPYQ]** Initial test project setup
  - **Files:** `test_module.py`
  - **Quality Improvement:** +20 points

### Fixed
- **[SPYQ]** Resolved print statement violations
  - **Count:** 3 statements replaced with logging
  - **Quality Improvement:** +5 points

### Changed
- **[SPYQ]** Refactored large function into smaller methods
  - **Before:** 45 lines
  - **After:** 3 methods, max 15 lines each
  - **Complexity Reduction:** 8 → 4

---
*This changelog is automatically maintained by SPYQ*

# scripts/migrate_config.py
#!/usr/bin/env python3
"""
Skrypt do migracji konfiguracji SPYQ między wersjami
"""

import json
import shutil
from pathlib import Path
from typing import Dict, Any

class ConfigMigrator:
    """Migrator konfiguracji SPYQ"""
    
    def __init__(self):
        self.version_migrations = {
            "0.1.0": self._migrate_to_0_1_0,
            "0.2.0": self._migrate_to_0_2_0
        }
    
    def migrate_config(self, config_path: str = "spyq.json", target_version: str = "0.2.0") -> bool:
        """Migruje konfigurację do docelowej wersji"""
        
        config_file = Path(config_path)
        if not config_file.exists():
            print(f"❌ Configuration file {config_path} not found")
            return False
        
        # Utwórz backup
        backup_path = f"{config_path}.backup"
        shutil.copy2(config_file, backup_path)
        print(f"📁 Created backup: {backup_path}")
        
        # Załaduj konfigurację
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        current_version = config.get('version', '0.1.0')
        print(f"🔍 Current version: {current_version}")
        print(f"🎯 Target version: {target_version}")
        
        # Wykonaj migracje
        migrated_config = self._apply_migrations(config, current_version, target_version)
        
        if migrated_config:
            # Zapisz zmigrowaną konfigurację
            with open(config_file, 'w') as f:
                json.dump(migrated_config, f, indent=2)
            
            print(f"✅ Configuration migrated to version {target_version}")
            return True
        else:
            print(f"❌ Migration failed")
            return False
    
    def _apply_migrations(self, config: Dict[str, Any], current: str, target: str) -> Dict[str, Any]:
        """Stosuje migracje krok po kroku"""
        
        migrated_config = config.copy()
        
        # Lista wersji do migracji
        versions_to_migrate = self._get_migration_path(current, target)
        
        for version in versions_to_migrate:
            if version in self.version_migrations:
                print(f"🔄 Migrating to {version}...")
                migrated_config = self.version_migrations[version](migrated_config)
                migrated_config['version'] = version
        
        return migrated_config
    
    def _get_migration_path(self, current: str, target: str) -> list:
        """Zwraca ścieżkę migracji między wersjami"""
        available_versions = ["0.1.0", "0.2.0"]
        
        try:
            current_idx = available_versions.index(current)
            target_idx = available_versions.index(target)
            
            if target_idx > current_idx:
                return available_versions[current_idx + 1:target_idx + 1]
            else:
                return []
        except ValueError:
            return []
    
    def _migrate_to_0_1_0(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Migracja do wersji 0.1.0"""
        # Dodaj nowe pola jeśli nie istnieją
        if 'enforcement' not in config:
            config['enforcement'] = {
                "block_save": False,
                "block_execution": False,
                "auto_fix_enabled": True
            }
        
        return config
    
    def _migrate_to_0_2_0(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Migracja do wersji 0.2.0"""
        # Dodaj obsługę Ollama
        if 'llm_integration' in config:
            llm_config = config['llm_integration']
            if 'providers' not in llm_config:
                llm_config['providers'] = {
                    "openai": {
                        "enabled": llm_config.get('enabled', False),
                        "model": llm_config.get('model_name', 'gpt-4')
                    },
                    "ollama": {
                        "enabled": False,
                        "base_url": "http://localhost:11434",
                        "model": "codellama:7b"
                    }
                }
        
        # Dodaj nowe reguły walidacji
        if 'validation_rules' in config:
            rules = config['validation_rules']
            if 'max_line_length' not in rules:
                rules['max_line_length'] = 88
            if 'require_type_hints' not in rules:
                rules['require_type_hints'] = False
        
        return config

def main():
    """Główna funkcja skryptu"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate SPYQ configuration")
    parser.add_argument('--config', default='spyq.json', help='Configuration file path')
    parser.add_argument('--version', default='0.2.0', help='Target version')
    
    args = parser.parse_args()
    
    migrator = ConfigMigrator()
    success = migrator.migrate_config(args.config, args.version)
    
    if success:
        print("\n🎉 Migration completed successfully!")
    else:
        print("\n💥 Migration failed!")
        exit(1)

if __name__ == "__main__":
    main()

# .spyq/templates/todo_template.md
# TODO List - Updated: {timestamp}

## 🔴 HIGH Priority (Auto-generated by SPYQ)

### Code Quality Violations
*Critical issues that need immediate attention*

## 🟡 MEDIUM Priority

### Code Improvements  
*Important enhancements and optimizations*

## 🟢 LOW Priority

### Documentation & Refactoring
*Nice-to-have improvements and future enhancements*

### Maintenance Tasks
*Routine maintenance and cleanup*

---

## 📊 Quick Stats
- **Total Tasks:** {total_tasks}
- **High Priority:** {high_priority_count}
- **Completion Rate:** {completion_rate}%
- **Last Updated:** {last_updated}

## 💡 Guidelines
- High priority tasks should be addressed within 24 hours
- Medium priority tasks within 1 week
- Low priority tasks can be scheduled for future sprints
- Auto-generated tasks from SPYQ are marked with **[SPYQ]**

---
*This file is automatically managed by SPYQ - Smart Python Quality Guardian*

# .spyq/templates/changelog_template.md
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - {current_date}

### Added
*New features and capabilities*

### Changed  
*Changes in existing functionality*

### Deprecated
*Soon-to-be removed features*

### Removed
*Removed features*

### Fixed
*Bug fixes and quality improvements*

### Security
*Security improvements*

---

## Template Instructions

### Entry Format
```markdown
### Category
- **[Source]** Description of change
  - **File(s):** `path/to/file.py`
  - **Impact:** Description of impact
  - **Additional Info:** Any relevant details
```

### Sources
- **[SPYQ]** - Auto-generated by SPYQ quality system
- **[MANUAL]** - Manually added entries
- **[FEATURE]** - New feature development
- **[BUGFIX]** - Bug fixes
- **[REFACTOR]** - Code refactoring

### Categories
- **Added** - New features
- **Changed** - Modifications to existing features  
- **Deprecated** - Features marked for removal
- **Removed** - Deleted features
- **Fixed** - Bug fixes and improvements
- **Security** - Security-related changes

---
*This changelog is automatically maintained by SPYQ - Smart Python Quality Guardian*

# .spyq/templates/config_template.json
{
  "version": "0.2.0",
  "validation_rules": {
    "max_function_lines": 50,
    "max_file_lines": 300,
    "max_cyclomatic_complexity": 10,
    "max_function_params": 5,
    "max_line_length": 88,
    "forbid_print_statements": true,
    "forbid_global_variables": true,
    "require_docstrings": true,
    "require_type_hints": false,
    "naming_convention": "snake_case"
  },
  "project_management": {
    "todo_integration": true,
    "auto_create_tasks": true,
    "todo_file": "TODO.md",
    "changelog_integration": true,
    "auto_update_changelog": true,
    "changelog_file": "CHANGELOG.md",
    "priority_mapping": {
      "critical": "🔴 HIGH",
      "major": "🟡 MEDIUM",
      "minor": "🟢 LOW"
    }
  },
  "llm_integration": {
    "enabled": false,
    "providers": {
      "openai": {
        "enabled": false,
        "model": "gpt-4",
        "api_key_env": "OPENAI_API_KEY"
      },
      "anthropic": {
        "enabled": false,
        "model": "claude-3-sonnet-20240229",
        "api_key_env": "ANTHROPIC_API_KEY"
      },
      "ollama": {
        "enabled": false,
        "base_url": "http://localhost:11434",
        "model": "codellama:7b",
        "timeout": 60
      }
    },
    "max_iterations": 3,
    "token_limit": 4000,
    "auto_fix_attempts": 2
  },
  "enforcement": {
    "block_save": false,
    "block_execution": false,
    "auto_fix_enabled": true,
    "real_time_validation": true
  },
  "notifications": {
    "show_violations": true,
    "suggest_refactoring": true,
    "desktop_notifications": false,
    "email_reports": false
  },
  "git_integration": {
    "pre_commit_validation": true,
    "post_commit_updates": true,
    "auto_commit_fixes": false
  },
  "project_root": ".",
  "_comments": {
    "validation_rules": "Core code quality rules",
    "llm_integration": "AI-powered code generation and fixes",
    "enforcement": "How strictly rules are enforced",
    "project_management": "TODO and CHANGELOG automation"
  }
}


# .spyq/hooks/pre-commit
```bash
#!/bin/sh
# SPYQ Pre-commit Hook
# Validates staged files before commit

echo "🔍 SPYQ: Validating staged files..."

# Get staged Python files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')

if [ -z "$STAGED_FILES" ]; then
    echo "✅ No Python files to validate"
    exit 0
fi

# Run SPYQ validation on staged files
VALIDATION_FAILED=0

for file in $STAGED_FILES; do
    echo "Validating: $file"
    
    # Run SPYQ validation
    python -m spyq validate "$file" --quiet
    
    if [ $? -ne 0 ]; then
        VALIDATION_FAILED=1
        echo "❌ Validation failed for: $file"
    fi
done

if [ $VALIDATION_FAILED -eq 1 ]; then
    echo ""
    echo "❌ SPYQ validation failed for some files"
    echo "💡 Fix issues with: spyq fix --auto"
    echo "📊 Check status with: spyq status"
    echo "🔧 Manual fixes may be required for complex violations"
    exit 1
fi

echo "✅ All staged files passed SPYQ validation"
exit 0
```

# .spyq/hooks/post-commit
```bash
#!/bin/sh
# SPYQ Post-commit Hook
# Updates project documentation after successful commit

echo "📝 SPYQ: Updating project documentation..."

# Get commit information
COMMIT_HASH=$(git rev-parse HEAD)
COMMIT_MSG=$(git log -1 --pretty=%B)
AUTHOR=$(git log -1 --pretty=%an)

# Update CHANGELOG with commit info
python -m spyq changelog add-commit-entry \
    --hash "$COMMIT_HASH" \
    --message "$COMMIT_MSG" \
    --author "$AUTHOR"

if [ $? -eq 0 ]; then
    echo "✅ CHANGELOG updated successfully"
else
    echo "⚠️ Could not update CHANGELOG automatically"
fi

# Update TODO completion status
python -m spyq todo update-from-commit "$COMMIT_MSG"

# Generate quality report
python -m spyq report --format brief --output .spyq/cache/last_commit_quality.json

echo "✅ SPYQ documentation updated"
```

# .spyq/hooks/pre-push
```bash
#!/bin/sh
# SPYQ Pre-push Hook  
# Final validation before pushing to remote

echo "🚀 SPYQ: Final validation before push..."

# Run full project validation
python -m spyq validate-project --strict

if [ $? -ne 0 ]; then
    echo "❌ Project validation failed"
    echo "🔧 Fix all issues before pushing:"
    echo "   spyq status           # Show current issues"
    echo "   spyq fix --auto       # Auto-fix what's possible"
    echo "   spyq validate-project # Re-validate"
    exit 1
fi

# Check quality score threshold
QUALITY_SCORE=$(python -m spyq status --format json | jq -r '.quality_score')

if [ "$QUALITY_SCORE" -lt 80 ]; then
    echo "⚠️ Quality score below threshold (${QUALITY_SCORE}/100)"
    echo "📈 Improve code quality before pushing"
    exit 1
fi

echo "✅ All validations passed - ready to push!"
echo "📊 Quality Score: ${QUALITY_SCORE}/100"
exit 0
```

