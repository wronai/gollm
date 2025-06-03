"""Health monitoring module for Ollama adapter."""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("gollm.ollama.health")


class HealthMonitor:
    """Monitors the health and status of the Ollama API."""

    def __init__(self, client):
        """Initialize the health monitor.

        Args:
            client: HTTP client for making API requests
        """
        self.client = client
        self.last_check_time = 0
        self.last_status = None
        self.check_interval = 60  # Default check interval in seconds
        self.status_listeners = []

    async def check_health(self, force: bool = False) -> Dict[str, Any]:
        """Check if the Ollama API is healthy.

        Args:
            force: If True, force a new health check even if cached

        Returns:
            Dictionary containing health status information
        """
        current_time = time.time()

        # Use cached result if available and recent
        if (
            not force
            and self.last_status
            and (current_time - self.last_check_time) < self.check_interval
        ):
            logger.debug("Using cached health status")
            return self.last_status

        # Perform health check
        try:
            logger.info("Performing Ollama API health check")
            start_time = time.time()

            # Check if we can list models as a basic health check
            result = await self.client._request("GET", "/api/tags")

            # Calculate response time
            response_time = time.time() - start_time

            # Prepare health status
            status = {
                "success": True,
                "status": "healthy",
                "response_time_ms": int(response_time * 1000),
                "models_available": len(result.get("models", [])),
                "timestamp": current_time,
            }

            # Add model names if available
            if "models" in result:
                status["available_models"] = [
                    model.get("name", "unknown") for model in result.get("models", [])
                ]

            logger.info(
                f"Ollama API is healthy (response time: {status['response_time_ms']}ms)"
            )

        except Exception as e:
            logger.error(f"Ollama API health check failed: {str(e)}")
            status = {
                "success": False,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": current_time,
            }

        # Update cache
        self.last_status = status
        self.last_check_time = current_time

        # Notify listeners
        for listener in self.status_listeners:
            try:
                listener(status)
            except Exception as e:
                logger.error(f"Error in health status listener: {str(e)}")

        return status

    def add_status_listener(self, listener: Callable[[Dict[str, Any]], None]) -> None:
        """Add a listener function to be called when health status changes.

        Args:
            listener: Function that takes a status dictionary as argument
        """
        self.status_listeners.append(listener)

    def set_check_interval(self, interval: int) -> None:
        """Set the interval between health checks.

        Args:
            interval: Interval in seconds
        """
        self.check_interval = max(10, interval)  # Minimum 10 seconds

    async def start_monitoring(self, interval: Optional[int] = None) -> None:
        """Start periodic health monitoring in the background.

        Args:
            interval: Check interval in seconds (defaults to self.check_interval)
        """
        if interval:
            self.set_check_interval(interval)

        logger.info(f"Starting health monitoring with {self.check_interval}s interval")

        while True:
            try:
                await self.check_health(force=True)
            except Exception as e:
                logger.error(f"Error in health monitoring: {str(e)}")

            await asyncio.sleep(self.check_interval)

    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of the current health status.

        Returns:
            Dictionary with summarized health information
        """
        if not self.last_status:
            return {"status": "unknown", "last_checked": None}

        return {
            "status": self.last_status.get("status", "unknown"),
            "healthy": self.last_status.get("success", False),
            "last_checked": self.last_check_time,
            "response_time_ms": self.last_status.get("response_time_ms"),
            "models_count": self.last_status.get("models_available", 0),
        }
