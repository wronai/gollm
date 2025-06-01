# src/gollm/utils/file_utils.py
import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
import tempfile
import hashlib

class FileUtils:
    """Narzędzia do operacji na plikach"""
    
    @staticmethod
    def find_python_files(directory: str, exclude_patterns: List[str] = None) -> List[Path]:
        """Znajduje wszystkie pliki Python w katalogu"""
        if exclude_patterns is None:
            exclude_patterns = ['__pycache__', '.git', '.venv', 'venv', '.pytest_cache']
        
        python_files = []
        root_path = Path(directory)
        
        for py_file in root_path.rglob("*.py"):
            # Sprawdź czy plik nie jest w wykluczonych katalogach
            if not any(pattern in str(py_file) for pattern in exclude_patterns):
                python_files.append(py_file)
        
        return sorted(python_files)
    
    @staticmethod
    def backup_file(file_path: str, backup_suffix: str = ".bak") -> str:
        """Tworzy kopię zapasową pliku"""
        backup_path = f"{file_path}{backup_suffix}"
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    @staticmethod
    def safe_write(file_path: str, content: str, create_backup: bool = True) -> bool:
        """Bezpieczny zapis pliku z opcjonalną kopią zapasową"""
        try:
            if create_backup and Path(file_path).exists():
                FileUtils.backup_file(file_path)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_file_hash(file_path: str) -> str:
        """Zwraca hash SHA256 pliku"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    @staticmethod
    def create_temp_file(content: str, suffix: str = ".py") -> str:
        """Tworzy tymczasowy plik z zawartością"""
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
            f.write(content)
            return f.name

# src/gollm/utils/string_utils.py
import re
from typing import List, Optional

class StringUtils:
    """Narzędzia do operacji na ciągach znaków"""
    
    @staticmethod
    def to_snake_case(camel_case: str) -> str:
        """Konwertuje CamelCase na snake_case"""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_case)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    @staticmethod
    def to_camel_case(snake_case: str) -> str:
        """Konwertuje snake_case na CamelCase"""
        components = snake_case.split('_')
        return ''.join(x.capitalize() for x in components)
    
    @staticmethod
    def extract_function_name(line: str) -> Optional[str]:
        """Wyodrębnia nazwę funkcji z linii kodu"""
        match = re.search(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', line)
        return match.group(1) if match else None
    
    @staticmethod
    def extract_class_name(line: str) -> Optional[str]:
        """Wyodrębnia nazwę klasy z linii kodu"""
        match = re.search(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[\(:]', line)
        return match.group(1) if match else None
    
    @staticmethod
    def clean_whitespace(text: str) -> str:
        """Czyści nadmiarowe białe znaki"""
        return re.sub(r'\s+', ' ', text.strip())
    
    @staticmethod
    def indent_lines(text: str, spaces: int = 4) -> str:
        """Dodaje wcięcia do wszystkich linii"""
        indent = ' ' * spaces
        return '\n'.join(indent + line for line in text.split('\n'))
