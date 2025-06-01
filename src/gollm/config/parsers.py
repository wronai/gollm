
# src/gollm/config/parsers.py
from typing import Dict, Any, Optional
from pathlib import Path
import configparser
import json
import toml

class ConfigParser:
    """Bazowa klasa dla parserów konfiguracji"""
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parsuje plik konfiguracyjny"""
        raise NotImplementedError

class GollmConfigParser(ConfigParser):
    """Parser dla plików gollm.json"""
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

class Flake8Parser(ConfigParser):
    """Parser dla konfiguracji Flake8"""
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        config = configparser.ConfigParser()
        config.read(file_path)
        
        flake8_config = {}
        if config.has_section('flake8'):
            flake8_config = dict(config['flake8'])
        
        return {
            "max_line_length": int(flake8_config.get('max-line-length', 88)),
            "ignore": flake8_config.get('ignore', '').split(','),
            "exclude": flake8_config.get('exclude', '').split(','),
            "max_complexity": int(flake8_config.get('max-complexity', 10))
        }

class PyprojectParser(ConfigParser):
    """Parser dla pyproject.toml"""
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = toml.load(f)
        
        config = {}
        
        # Black configuration
        if 'tool' in data and 'black' in data['tool']:
            black_config = data['tool']['black']
            config['black'] = {
                "line_length": black_config.get('line-length', 88),
                "target_version": black_config.get('target-version', []),
                "skip_string_normalization": black_config.get('skip-string-normalization', False)
            }
        
        # Pytest configuration
        if 'tool' in data and 'pytest' in data['tool']:
            pytest_config = data['tool']['pytest']
            config['pytest'] = pytest_config
        
        # MyPy configuration
        if 'tool' in data and 'mypy' in data['tool']:
            mypy_config = data['tool']['mypy']
            config['mypy'] = mypy_config
        
        return config

class MypyParser(ConfigParser):
    """Parser dla mypy.ini"""
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        config = configparser.ConfigParser()
        config.read(file_path)
        
        mypy_config = {}
        if config.has_section('mypy'):
            mypy_config = dict(config['mypy'])
        
        return {
            "strict": mypy_config.get('strict', 'False').lower() == 'true',
            "warn_return_any": mypy_config.get('warn_return_any', 'False').lower() == 'true',
            "warn_unused_configs": mypy_config.get('warn_unused_configs', 'False').lower() == 'true',
            "disallow_untyped_defs": mypy_config.get('disallow_untyped_defs', 'False').lower() == 'true'
        }
# src/gollm/config/parsers.py
from typing import Dict, Any, Optional
from pathlib import Path
import configparser
import json
import toml

class ConfigParser:
    """Bazowa klasa dla parserów konfiguracji"""
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """Parsuje plik konfiguracyjny"""
        raise NotImplementedError

class GollmConfigParser(ConfigParser):
    """Parser dla plików gollm.json"""
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

class Flake8Parser(ConfigParser):
    """Parser dla konfiguracji Flake8"""
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        config = configparser.ConfigParser()
        config.read(file_path)
        
        flake8_config = {}
        if config.has_section('flake8'):
            flake8_config = dict(config['flake8'])
        
        return {
            "max_line_length": int(flake8_config.get('max-line-length', 88)),
            "ignore": flake8_config.get('ignore', '').split(','),
            "exclude": flake8_config.get('exclude', '').split(','),
            "max_complexity": int(flake8_config.get('max-complexity', 10))
        }

class PyprojectParser(ConfigParser):
    """Parser dla pyproject.toml"""
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = toml.load(f)
        
        config = {}
        
        # Black configuration
        if 'tool' in data and 'black' in data['tool']:
            black_config = data['tool']['black']
            config['black'] = {
                "line_length": black_config.get('line-length', 88),
                "target_version": black_config.get('target-version', []),
                "skip_string_normalization": black_config.get('skip-string-normalization', False)
            }
        
        # Pytest configuration
        if 'tool' in data and 'pytest' in data['tool']:
            pytest_config = data['tool']['pytest']
            config['pytest'] = pytest_config
        
        # MyPy configuration
        if 'tool' in data and 'mypy' in data['tool']:
            mypy_config = data['tool']['mypy']
            config['mypy'] = mypy_config
        
        return config

class MypyParser(ConfigParser):
    """Parser dla mypy.ini"""
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        config = configparser.ConfigParser()
        config.read(file_path)
        
        mypy_config = {}
        if config.has_section('mypy'):
            mypy_config = dict(config['mypy'])
        
        return {
            "strict": mypy_config.get('strict', 'False').lower() == 'true',
            "warn_return_any": mypy_config.get('warn_return_any', 'False').lower() == 'true',
            "warn_unused_configs": mypy_config.get('warn_unused_configs', 'False').lower() == 'true',
            "disallow_untyped_defs": mypy_config.get('disallow_untyped_defs', 'False').lower() == 'true'
        }