
# src/gollm/project_management/changelog_manager.py
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

class ChangelogManager:
    """Zarządza automatycznymi aktualizacjami CHANGELOG.md"""
    
    def __init__(self, config):
        self.config = config
        self.changelog_file = Path(config.project_management.changelog_file)
        self._ensure_changelog_exists()
    
    def _ensure_changelog_exists(self):
        """Tworzy plik CHANGELOG.md jeśli nie istnieje"""
        if not self.changelog_file.exists():
            template = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security

---
*This changelog is automatically maintained by goLLM*
"""
            with open(self.changelog_file, 'w', encoding='utf-8') as f:
                f.write(template)
    
    def record_change(self, change_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Zapisuje zmianę do CHANGELOG"""
        change_entry = self._create_change_entry(change_type, details)
        self._update_changelog_file(change_entry)
        return change_entry
    
    def _create_change_entry(self, change_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Tworzy wpis o zmianie"""
        timestamp = datetime.now().isoformat()
        
        # Mapowanie typów zmian na sekcje CHANGELOG
        section_map = {
            "code_quality_fix": "Fixed",
            "feature_added": "Added",
            "bug_fix": "Fixed",
            "refactoring": "Changed",
            "documentation": "Added",
            "performance": "Changed",
            "security": "Security"
        }
        
        section = section_map.get(change_type, "Changed")
        
        entry = {
            "timestamp": timestamp,
            "type": change_type,
            "section": section,
            "description": details.get('description', ''),
            "files_affected": details.get('files', []),
            "impact": details.get('impact', ''),
            "gollm_metadata": {
                "auto_generated": True,
                "violations_fixed": details.get('violations_fixed', []),
                "quality_improvement": details.get('quality_delta', 0)
            }
        }
        
        return entry
    
    def _update_changelog_file(self, change_entry: Dict[str, Any]):
        """Aktualizuje plik CHANGELOG.md"""
        with open(self.changelog_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Znajdź sekcję [Unreleased]
        unreleased_pattern = r'(## \[Unreleased\].*?)((?=## \[|\Z))'
        match = re.search(unreleased_pattern, content, re.DOTALL)
        
        if match:
            unreleased_section = match.group(1)
            rest_of_content = content[match.end(1):]
            
            # Dodaj nowy wpis do odpowiedniej sekcji
            updated_unreleased = self._add_entry_to_section(
                unreleased_section, change_entry
            )
            
            new_content = content[:match.start(1)] + updated_unreleased + rest_of_content
            
            with open(self.changelog_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
    
    def _add_entry_to_section(self, unreleased_section: str, entry: Dict[str, Any]) -> str:
        """Dodaje wpis do odpowiedniej sekcji w [Unreleased]"""
        target_section = entry['section']
        
        # Znajdź lub utwórz sekcję
        section_pattern = f'(### {target_section}\s*)(.*?)(?=### |$)'
        section_match = re.search(section_pattern, unreleased_section, re.DOTALL)
        
        entry_text = self._format_changelog_entry(entry)
        
        if section_match:
            # Sekcja istnieje - dodaj wpis
            existing_entries = section_match.group(2).strip()
            new_entries = f"{entry_text}\n{existing_entries}" if existing_entries else entry_text
            
            new_section = f"{section_match.group(1)}{new_entries}\n"
            
            return unreleased_section[:section_match.start()] + new_section + unreleased_section[section_match.end():]
        else:
            # Sekcja nie istnieje - utwórz ją
            # Znajdź miejsce gdzie wstawić nową sekcję
            sections_order = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]
            insert_position = unreleased_section.find('\n### ')
            
            if insert_position == -1:
                insert_position = len(unreleased_section)
            
            new_section = f"\n### {target_section}\n{entry_text}\n"
            
            return unreleased_section[:insert_position] + new_section + unreleased_section[insert_position:]
    
    def _format_changelog_entry(self, entry: Dict[str, Any]) -> str:
        """Formatuje wpis dla CHANGELOG"""
        description = entry['description']
        files = entry.get('files_affected', [])
        metadata = entry.get('gollm_metadata', {})
        
        # Podstawowy wpis
        formatted = f"- **[goLLM]** {description}"
        
        # Dodaj informacje o plikach
        if files:
            if len(files) == 1:
                formatted += f"\n  - **File:** `{files[0]}`"
            else:
                formatted += f"\n  - **Files:** {', '.join(f'`{f}`' for f in files[:3])}"
                if len(files) > 3:
                    formatted += f" and {len(files) - 3} more"
        
        # Dodaj informacje o poprawkach
        violations_fixed = metadata.get('violations_fixed', [])
        if violations_fixed:
            formatted += f"\n  - **Violations Fixed:** {len(violations_fixed)}"
        
        # Dodaj poprawę jakości
        quality_improvement = metadata.get('quality_improvement', 0)
        if quality_improvement > 0:
            formatted += f"\n  - **Quality Improvement:** +{quality_improvement} points"
        
        return formatted
    
    def get_recent_changes_count(self, days: int = 7) -> int:
        """Zwraca liczbę zmian z ostatnich X dni"""
        try:
            with open(self.changelog_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Proste liczenie wpisów goLLM z ostatnich dni
            gollm_entries = re.findall(r'- \*\*\[goLLM\]\*\*', content)
            return len(gollm_entries)
        except:
            return 0
