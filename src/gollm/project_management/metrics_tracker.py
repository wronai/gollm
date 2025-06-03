"""Tracks and manages code quality metrics over time."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class MetricsTracker:
    """Tracks code quality metrics over time."""

    def __init__(self, metrics_file: Path = Path(".gollm/metrics.json")):
        """Initialize metrics tracker with storage file."""
        self.metrics_file = metrics_file
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_metrics_file()

    def _ensure_metrics_file(self):
        """Ensure the metrics file exists with proper structure."""
        if not self.metrics_file.exists():
            self.metrics_file.write_text(
                json.dumps({"version": 1, "metrics": []}, indent=2)
            )

    def _load_metrics(self) -> dict:
        """Load metrics from the storage file."""
        try:
            return json.loads(self.metrics_file.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            return {"version": 1, "metrics": []}

    def _save_metrics(self, data: dict):
        """Save metrics to the storage file."""
        self.metrics_file.write_text(json.dumps(data, indent=2))

    def record_metrics(self, metrics: dict):
        """Record a new set of metrics."""
        data = self._load_metrics()
        timestamp = datetime.utcnow().isoformat()

        data["metrics"].append({"timestamp": timestamp, **metrics})

        self._save_metrics(data)

    def get_metrics(self, period: str = "month") -> List[dict]:
        """Get metrics for a specific time period."""
        data = self._load_metrics()
        now = datetime.utcnow()

        if period == "day":
            cutoff = now - timedelta(days=1)
        elif period == "week":
            cutoff = now - timedelta(weeks=1)
        else:  # month
            cutoff = now - timedelta(days=30)

        return [
            m
            for m in data.get("metrics", [])
            if datetime.fromisoformat(m["timestamp"]) >= cutoff
        ]

    def get_quality_trend(self, period: str = "month") -> List[Tuple[str, float]]:
        """Get code quality trend over time."""
        metrics = self.get_metrics(period)
        return [
            (m["timestamp"], m.get("quality_score", 0))
            for m in metrics
            if "quality_score" in m
        ]

    def get_violations_trend(self, period: str = "month") -> List[Tuple[str, int]]:
        """Get code violations trend over time."""
        metrics = self.get_metrics(period)
        return [
            (m["timestamp"], m.get("violations_count", 0))
            for m in metrics
            if "violations_count" in m
        ]
