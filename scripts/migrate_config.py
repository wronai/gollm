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

