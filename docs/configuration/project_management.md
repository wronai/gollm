# Project Management Configuration

## Overview

Project management settings in goLLM help you track tasks, manage TODOs, and maintain changelogs automatically.

## Todo Integration

### Enable Todo Tracking
- **Setting**: `todo_integration`
- **Default**: `true`
- **Description**: Enable or disable todo tracking.

### Auto-create Tasks
- **Setting**: `auto_create_tasks`
- **Default**: `true`
- **Description**: Automatically create tasks from code comments.

### Todo File Location
- **Setting**: `todo_file`
- **Default**: `"TODO.md"`
- **Description**: Path to the todo file.

## Changelog Integration

### Enable Changelog
- **Setting**: `changelog_integration`
- **Default**: `true`
- **Description**: Enable or disable changelog generation.

### Auto-update Changelog
- **Setting**: `auto_update_changelog`
- **Default**: `true`
- **Description**: Automatically update changelog on version changes.

### Changelog File Location
- **Setting**: `changelog_file`
- **Default**: `"CHANGELOG.md"`
- **Description**: Path to the changelog file.

## Example Configuration

```json
{
  "project_management": {
    "todo_integration": true,
    "auto_create_tasks": true,
    "todo_file": "TODO.md",
    "changelog_integration": true,
    "auto_update_changelog": true,
    "changelog_file": "CHANGELOG.md"
  }
}
```

## Todo File Format

goLLM uses the following format for todo items:

```markdown
# 📋 TODO List

## 🔴 High Priority
- [ ] Fix critical bug in user authentication

## 🟡 Medium Priority
- [ ] Add input validation for contact form

## 🟢 Low Priority
- [ ] Update documentation
```

## Changelog Format

Changelogs follow the Keep a Changelog format:

```markdown
# Changelog

## [Unreleased]
### Added
- New feature X

### Changed
- Improved performance of Y

## [1.0.0] - 2023-01-01
### Added
- Initial release
```

## Customization

### Custom Todo Templates

You can customize the todo template by creating a `.gollm/todo_template.md` file in your project root.

### Custom Changelog Headers

To customize changelog headers, create a `.gollm/changelog_headers.json` file:

```json
{
  "added": "✨ Added",
  "changed": "♻️ Changed",
  "deprecated": "🗑️ Deprecated",
  "removed": "❌ Removed",
  "fixed": "🐛 Fixed",
  "security": "🔒 Security"
}
```

## Commands

### Update Todo List

```bash
gollm update-todos
```

### Update Changelog

```bash
gollm update-changelog
```

## Related Documentation

- [Validation Rules](./validation_rules.md)
- [LLM Integration](./llm_integration.md)
- [Advanced Configuration](./advanced.md)
