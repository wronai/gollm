# src/gollm/git/analyzer.py
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class CommitInfo:
    hash: str
    author: str
    date: datetime
    message: str
    files_changed: List[str]


class GitAnalyzer:
    """Analizuje historię Git i zmiany w projekcie"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.git_dir = self.project_root / ".git"

    def is_git_repository(self) -> bool:
        """Sprawdza czy projekt jest repozytorium Git"""
        return self.git_dir.exists()

    def get_current_commit_info(self) -> Optional[CommitInfo]:
        """Zwraca informacje o aktualnym commicie"""
        if not self.is_git_repository():
            return None

        try:
            # Pobierz hash
            hash_result = self._run_git_command(["rev-parse", "HEAD"])
            if not hash_result:
                return None
            commit_hash = hash_result.strip()

            # Pobierz autora i datę
            log_result = self._run_git_command(
                ["log", "-1", "--format=%an|%ai|%s", commit_hash]
            )
            if not log_result:
                return None

            author, date_str, message = log_result.strip().split("|", 2)
            commit_date = datetime.fromisoformat(date_str.replace(" ", "T", 1))

            # Pobierz zmienione pliki
            files_result = self._run_git_command(
                ["diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash]
            )
            files_changed = files_result.strip().split("\n") if files_result else []

            return CommitInfo(
                hash=commit_hash[:8],
                author=author,
                date=commit_date,
                message=message,
                files_changed=files_changed,
            )

        except Exception:
            return None

    def get_recent_commits(self, days: int = 7) -> List[CommitInfo]:
        """Zwraca listę ostatnich commitów"""
        if not self.is_git_repository():
            return []

        try:
            since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            log_result = self._run_git_command(
                ["log", f"--since={since_date}", "--format=%H|%an|%ai|%s"]
            )

            if not log_result:
                return []

            commits = []
            for line in log_result.strip().split("\n"):
                if line:
                    hash_full, author, date_str, message = line.split("|", 3)
                    commit_date = datetime.fromisoformat(date_str.replace(" ", "T", 1))

                    # Pobierz pliki dla tego commita
                    files_result = self._run_git_command(
                        ["diff-tree", "--no-commit-id", "--name-only", "-r", hash_full]
                    )
                    files_changed = (
                        files_result.strip().split("\n") if files_result else []
                    )

                    commits.append(
                        CommitInfo(
                            hash=hash_full[:8],
                            author=author,
                            date=commit_date,
                            message=message,
                            files_changed=files_changed,
                        )
                    )

            return commits

        except Exception:
            return []

    def get_staged_files(self) -> List[str]:
        """Zwraca listę plików w staging area"""
        if not self.is_git_repository():
            return []

        try:
            result = self._run_git_command(["diff", "--cached", "--name-only"])
            return result.strip().split("\n") if result else []
        except Exception:
            return []

    def get_modified_files(self) -> List[str]:
        """Zwraca listę zmodyfikowanych plików"""
        if not self.is_git_repository():
            return []

        try:
            result = self._run_git_command(["diff", "--name-only"])
            return result.strip().split("\n") if result else []
        except Exception:
            return []

    def get_file_history(self, file_path: str, limit: int = 10) -> List[CommitInfo]:
        """Zwraca historię zmian dla konkretnego pliku"""
        if not self.is_git_repository():
            return []

        try:
            log_result = self._run_git_command(
                ["log", f"-{limit}", "--format=%H|%an|%ai|%s", "--", file_path]
            )

            if not log_result:
                return []

            commits = []
            for line in log_result.strip().split("\n"):
                if line:
                    hash_full, author, date_str, message = line.split("|", 3)
                    commit_date = datetime.fromisoformat(date_str.replace(" ", "T", 1))

                    commits.append(
                        CommitInfo(
                            hash=hash_full[:8],
                            author=author,
                            date=commit_date,
                            message=message,
                            files_changed=[file_path],
                        )
                    )

            return commits

        except Exception:
            return []

    def _run_git_command(self, args: List[str]) -> Optional[str]:
        """Uruchamia komendę Git i zwraca wynik"""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                return result.stdout
            return None

        except Exception:
            return None

    def get_branch_info(self) -> Dict[str, Any]:
        """Zwraca informacje o aktualnej gałęzi"""
        if not self.is_git_repository():
            return {}

        try:
            # Aktualna gałąź
            branch_result = self._run_git_command(["branch", "--show-current"])
            current_branch = branch_result.strip() if branch_result else "unknown"

            # Ostatni commit
            last_commit = self.get_current_commit_info()

            # Status
            status_result = self._run_git_command(["status", "--porcelain"])
            has_changes = bool(status_result and status_result.strip())

            return {
                "current_branch": current_branch,
                "last_commit": last_commit,
                "has_uncommitted_changes": has_changes,
                "staged_files_count": len(self.get_staged_files()),
                "modified_files_count": len(self.get_modified_files()),
            }

        except Exception:
            return {}
