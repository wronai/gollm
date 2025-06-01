from setuptools import setup, find_packages

setup(
    name="spyq",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "pyyaml>=6.0",
        "toml>=0.10.0", 
        "psutil>=5.0.0",
        "aiofiles>=0.8.0",
        "pydantic>=1.10.0"
    ],
    entry_points={
        "console_scripts": [
            "spyq=spyq.cli:cli",
        ],
    },
)

# examples/spyq.json
{
  "validation_rules": {
    "max_function_lines": 50,
    "max_file_lines": 300,
    "max_cyclomatic_complexity": 10,
    "forbid_print_statements": true,
    "forbid_global_variables": true,
    "require_docstrings": true,
    "max_function_params": 5,
    "naming_convention": "snake_case",
    "max_line_length": 88
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
    "enabled": true,
    "model_name": "gpt-4",
    "max_iterations": 3,
    "token_limit": 4000,
    "auto_fix_attempts": 2,
    "api_provider": "openai"
  },
  "enforcement": {
    "block_save": true,
    "block_execution": true,
    "auto_fix_enabled": true
  },
  "notifications": {
    "show_violations": true,
    "suggest_refactoring": true,
    "desktop_notifications": false
  },
  "project_root": "."
}
