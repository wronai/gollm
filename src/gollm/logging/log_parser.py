# src/gollm/logging/log_parser.py
import re
from typing import Any, Dict, List, Optional


class LogParser:
    """Parsuje logi i wyodrębnia ważne informacje"""

    def __init__(self):
        self.error_patterns = {
            "AttributeError": r"AttributeError: '(.+?)' object has no attribute '(.+?)'",
            "KeyError": r"KeyError: (.+)",
            "TypeError": r"TypeError: (.+)",
            "ValueError": r"ValueError: (.+)",
            "ImportError": r"ImportError: (.+)",
            "ModuleNotFoundError": r"ModuleNotFoundError: (.+)",
            "SyntaxError": r"SyntaxError: (.+)",
            "IndentationError": r"IndentationError: (.+)",
        }

    def parse_error(self, stderr: str) -> Optional[Dict[str, Any]]:
        """Parsuje błąd z stderr"""
        if not stderr:
            return None

        lines = stderr.split("\n")

        # Znajdź linię z błędem
        error_line = None
        for line in lines:
            line = line.strip()
            for error_type, pattern in self.error_patterns.items():
                if line.startswith(error_type):
                    match = re.search(pattern, line)
                    if match:
                        error_line = line
                        break
            if error_line:
                break

        if not error_line:
            return {"type": "UnknownError", "message": stderr[:200]}

        # Wyodrębnij typ błędu
        error_type = error_line.split(":")[0]
        error_message = ":".join(error_line.split(":")[1:]).strip()

        # Znajdź traceback
        traceback = self._extract_traceback(stderr)

        # Znajdź plik i linię
        file_info = self._extract_file_info(stderr)

        return {
            "type": error_type,
            "message": error_message,
            "traceback": traceback,
            "file_path": file_info.get("file"),
            "line_number": file_info.get("line"),
            "context_lines": self._extract_context_lines(stderr),
        }

    def _extract_traceback(self, stderr: str) -> str:
        """Wyodrębnia pełny traceback"""
        lines = stderr.split("\n")
        traceback_lines = []
        capturing = False

        for line in lines:
            if line.startswith("Traceback"):
                capturing = True
            if capturing:
                traceback_lines.append(line)

        return "\n".join(traceback_lines)

    def _extract_file_info(self, stderr: str) -> Dict[str, Any]:
        """Wyodrębnia informacje o pliku i linii błędu"""
        # Szukaj wzorca: File "path/to/file.py", line 123
        file_pattern = r'File "([^"]+)", line (\d+)'
        matches = re.findall(file_pattern, stderr)

        if matches:
            # Ostatni match to zwykle miejsce błędu
            file_path, line_number = matches[-1]
            return {"file": file_path, "line": int(line_number)}

        return {}

    def _extract_context_lines(self, stderr: str) -> List[str]:
        """Wyodrębnia linie kontekstu wokół błędu"""
        lines = stderr.split("\n")
        context_lines = []

        for i, line in enumerate(lines):
            if line.strip().startswith(">"):  # Linia wskazująca błąd w Pythonie
                # Zbierz kilka linii wokół
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                context_lines = lines[start:end]
                break

        return context_lines
