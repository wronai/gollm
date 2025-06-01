
# src/gollm/config/aggregator.py
import json
import configparser
import toml
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

class ProjectConfigAggregator:
    """Agreguje konfiguracje z różnych plików projektu"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.config_files = {}
        self.aggregated_config = {}
        self._discover_config_files()
    
    def _discover_config_files(self):
        """Znajduje wszystkie pliki konfiguracyjne"""
        config_patterns = {
            'gollm.json': self._parse_json,
            'pyproject.toml': self._parse_pyproject_toml,
            'setup.cfg': self._parse_setup_cfg,
            '.flake8': self._parse_flake8,
            'mypy.ini': self._parse_ini,
            '.pylintrc': self._parse_ini,
            'pytest.ini': self._parse_ini,
            '.pre-commit-config.yaml': self._parse_yaml
        }
        
        for filename, parser in config_patterns.items():
            config_path = self.project_root / filename
            if config_path.exists():
                self.config_files[filename] = {
                    'path': config_path,
                    'parser': parser,
                    'last_modified': config_path.stat().st_mtime
                }
    
    def get_aggregated_config(self) -> Dict[str, Any]:
        """Zwraca zagregowaną konfigurację"""
        if not self.aggregated_config:
            self._aggregate_configs()
        
        return self.aggregated_config
    
    def _aggregate_configs(self):
        """Agreguje wszystkie konfiguracje"""
        self.aggregated_config = {
            "gollm_rules": {},
            "linting_rules": {},
            "testing_config": {},
            "build_config": {},
            "dependencies": {},
            "quality_gates": {},
            "conflicts": [],
            "recommendations": []
        }
        
        # Parsuj każdy plik konfiguracyjny
        for filename, config_info in self.config_files.items():
            try:
                parsed = config_info['parser'](config_info['path'])
                self._merge_config(filename, parsed)
            except Exception as e:
                self.aggregated_config["conflicts"].append({
                    "file": filename,
                    "error": str(e),
                    "type": "parse_error"
                })
        
        # Wykryj konflikty między konfiguracjami
        self._detect_conflicts()
        
        # Wygeneruj rekomendacje
        self._generate_recommendations()
    
    def _parse_json(self, path: Path) -> Dict[str, Any]:
        """Parsuje pliki JSON"""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _parse_pyproject_toml(self, path: Path) -> Dict[str, Any]:
        """Parsuje pyproject.toml"""
        with open(path, 'r', encoding='utf-8') as f:
            return toml.load(f)
    
    def _parse_setup_cfg(self, path: Path) -> Dict[str, Any]:
        """Parsuje setup.cfg"""
        config = configparser.ConfigParser()
        config.read(path)
        return {section: dict(config[section]) for section in config.sections()}
    
    def _parse_flake8(self, path: Path) -> Dict[str, Any]:
        """Parsuje .flake8"""
        config = configparser.ConfigParser()
        config.read(path)
        return {section: dict(config[section]) for section in config.sections()}
    
    def _parse_ini(self, path: Path) -> Dict[str, Any]:
        """Parsuje pliki .ini"""
        config = configparser.ConfigParser()
        config.read(path)
        return {section: dict(config[section]) for section in config.sections()}
    
    def _parse_yaml(self, path: Path) -> Dict[str, Any]:
        """Parsuje pliki YAML"""
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _merge_config(self, filename: str, parsed_config: Dict[str, Any]):
        """Łączy konfigurację z agregatem"""
        
        if filename == 'gollm.json':
            self.aggregated_config["gollm_rules"] = parsed_config
        
        elif filename == 'pyproject.toml':
            # Wyodrębnij sekcje istotne dla jakości kodu
            if 'tool' in parsed_config:
                tool_config = parsed_config['tool']
                
                if 'black' in tool_config:
                    self.aggregated_config["linting_rules"]["black"] = tool_config['black']
                
                if 'pytest' in tool_config:
                    self.aggregated_config["testing_config"]["pytest"] = tool_config['pytest']
                
                if 'mypy' in tool_config:
                    self.aggregated_config["linting_rules"]["mypy"] = tool_config['mypy']
        
        elif filename == '.flake8':
            if 'flake8' in parsed_config:
                self.aggregated_config["linting_rules"]["flake8"] = parsed_config['flake8']
        
        elif filename == 'mypy.ini':
            if 'mypy' in parsed_config:
                self.aggregated_config["linting_rules"]["mypy"] = parsed_config['mypy']
        
        elif filename == '.pylintrc':
            self.aggregated_config["linting_rules"]["pylint"] = parsed_config
        
        elif filename == '.pre-commit-config.yaml':
            self.aggregated_config["quality_gates"]["pre_commit"] = parsed_config
    
    def _detect_conflicts(self):
        """Wykrywa konflikty między konfiguracjami"""
        conflicts = []
        
        # Sprawdź konflikty długości linii
        line_length_configs = {}
        
        # Black
        black_config = self.aggregated_config["linting_rules"].get("black", {})
        if "line-length" in black_config:
            line_length_configs["black"] = black_config["line-length"]
        
        # Flake8
        flake8_config = self.aggregated_config["linting_rules"].get("flake8", {})
        if "max-line-length" in flake8_config:
            line_length_configs["flake8"] = int(flake8_config["max-line-length"])
        
        # goLLM
        gollm_rules = self.aggregated_config["gollm_rules"].get("validation_rules", {})
        if "max_line_length" in gollm_rules:
            line_length_configs["gollm"] = gollm_rules["max_line_length"]
        
        # Sprawdź czy wszystkie są zgodne
        if len(set(line_length_configs.values())) > 1:
            conflicts.append({
                "type": "line_length_mismatch",
                "description": "Different line length limits across tools",
                "configs": line_length_configs,
                "recommendation": "Standardize line length across all tools"
            })
        
        self.aggregated_config["conflicts"].extend(conflicts)
    
    def _generate_recommendations(self):
        """Generuje rekomendacje konfiguracyjne"""
        recommendations = []
        
        # Sprawdź czy goLLM ma wszystkie potrzebne konfiguracje
        gollm_config = self.aggregated_config["gollm_rules"]
        if not gollm_config:
            recommendations.append({
                "type": "missing_gollm_config",
                "priority": "high",
                "description": "No goLLM configuration found",
                "action": "Create gollm.json with validation rules"
            })
        
        # Sprawdź zgodność z istniejącymi narzędziami
        if "flake8" in self.aggregated_config["linting_rules"]:
            recommendations.append({
                "type": "sync_with_flake8",
                "priority": "medium", 
                "description": "Sync goLLM rules with existing Flake8 configuration",
                "action": "Update goLLM rules to match Flake8 standards"
            })
        
        self.aggregated_config["recommendations"] = recommendations
    
    def get_llm_config_summary(self) -> str:
        """Zwraca podsumowanie konfiguracji dla LLM"""
        config = self.get_aggregated_config()
        
        # Przygotuj podsumowanie reguł
        active_rules = []
        
        # goLLM rules
        gollm_rules = config.get("gollm_rules", {}).get("validation_rules", {})
        if gollm_rules:
            active_rules.append("goLLM Quality Rules:")
            for rule, value in gollm_rules.items():
                active_rules.append(f"  - {rule}: {value}")
        
        # Linting rules
        linting_rules = config.get("linting_rules", {})
        for tool, rules in linting_rules.items():
            active_rules.append(f"{tool.title()} Rules:")
            for rule, value in rules.items():
                active_rules.append(f"  - {rule}: {value}")
        
        # Konflikty
        conflicts = config.get("conflicts", [])
        conflict_summary = []
        if conflicts:
            conflict_summary.append("⚠️ Configuration Conflicts:")
            for conflict in conflicts:
                conflict_summary.append(f"  - {conflict['description']}")
        
        # Rekomendacje
        recommendations = config.get("recommendations", [])
        rec_summary = []
        if recommendations:
            rec_summary.append("💡 Recommendations:")
            for rec in recommendations:
                rec_summary.append(f"  - {rec['description']}")
        
        return "\n".join([
            "📋 PROJECT CONFIGURATION SUMMARY:",
            "",
            "🔧 Active Quality Rules:",
            "\n".join(active_rules) if active_rules else "  No specific rules configured",
            "",
            "\n".join(conflict_summary) if conflict_summary else "✅ No configuration conflicts detected",
            "",
            "\n".join(rec_summary) if rec_summary else "✅ Configuration looks good"
        ])
