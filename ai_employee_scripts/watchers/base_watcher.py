"""
Base Watcher - Abstract template for all AI Employee watchers

All watchers inherit from this base class to ensure consistent behavior
and error handling across the system.

Includes error recovery:
- Retry with exponential backoff
- Circuit breaker for external APIs
- Dead letter queue for failed items
- Health monitoring
"""

import time
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import List, Any, Optional
import sys

# Add parent directory to import error_recovery
sys.path.insert(0, str(Path(__file__).parent.parent))
from error_recovery import (
    with_retry, CircuitBreaker, CircuitState,
    DeadLetterQueue, GracefulDegradation, HealthMonitor,
    is_transient_error, CircuitBreakerOpenError
)


class BaseWatcher(ABC):
    """
    Abstract base class for all watcher scripts.

    Watchers monitor external sources (Gmail, WhatsApp, filesystem, etc.)
    and create actionable .md files in the vault's Needs_Action folder.

    Error Recovery Features:
    - Automatic retry on transient failures
    - Circuit breaker to prevent cascading failures
    - Dead letter queue for permanently failed items
    - Health status reporting
    """

    def __init__(
        self,
        vault_path: str,
        check_interval: int = 60,
        name: Optional[str] = None,
        enable_circuit_breaker: bool = True,
        enable_retry: bool = True
    ):
        """
        Initialize the watcher.

        Args:
            vault_path: Path to the AI_Employee_Vault
            check_interval: Seconds between checks (default: 60)
            name: Watcher name (defaults to class name)
            enable_circuit_breaker: Enable circuit breaker pattern
            enable_retry: Enable retry with exponential backoff
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Needs_Action"
        self.check_interval = check_interval
        self.name = name or self.__class__.__name__
        self.enable_circuit_breaker = enable_circuit_breaker
        self.enable_retry = enable_retry
        self.logger = self._setup_logger()

        # Ensure Needs_Action folder exists
        self.needs_action.mkdir(parents=True, exist_ok=True)

        # Initialize error recovery components
        self._init_error_recovery()

    def _setup_logger(self) -> logging.Logger:
        """Configure logging for this watcher."""
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _init_error_recovery(self):
        """Initialize error recovery components."""
        # Circuit breaker for this watcher's API calls
        if self.enable_circuit_breaker:
            self.circuit_breaker = CircuitBreaker(
                name=self.name,
                failure_threshold=5,
                timeout=60
            )

        # Dead letter queue for failed items
        self.dead_letter = DeadLetterQueue(subdir=self.name)

        # Health monitor
        self.health_monitor = HealthMonitor()

        # Record initial health
        self.health_monitor.record_health(
            self.name,
            "healthy",
            {"check_interval": self.check_interval}
        )

    @abstractmethod
    def check_for_updates(self) -> List[Any]:
        """
        Check for new items to process.

        Returns:
            List of new items found (empty if none)
        """
        pass

    @abstractmethod
    def create_action_file(self, item: Any) -> Path:
        """
        Create a .md file in the Needs_Action folder for the given item.

        Args:
            item: The item to create an action file for

        Returns:
            Path to the created action file
        """
        pass

    @abstractmethod
    def get_item_id(self, item: Any) -> str:
        """
        Get a unique identifier for an item.

        Used to track processed items and avoid duplicates.

        Args:
            item: The item to get an ID for

        Returns:
            Unique identifier string
        """
        pass

    def _create_markdown_header(self, item_type: str, **metadata) -> str:
        """Create standard YAML frontmatter for action files."""
        lines = ["---"]
        lines.append(f"type: {item_type}")
        lines.append(f"source: {self.name}")
        lines.append(f"created: {datetime.now().isoformat()}")
        lines.append(f"status: pending")
        lines.append(f"priority: medium")

        for key, value in metadata.items():
            if value is not None:
                lines.append(f"{key}: {value}")

        lines.append("---")
        return "\n".join(lines)

    def run(self):
        """
        Main watcher loop with error recovery.

        Continuously checks for updates and creates action files.
        Press Ctrl+C to stop.

        Error Recovery:
        - Transient errors are retried automatically
        - Circuit breaker opens after repeated failures
        - Failed items go to dead letter queue
        - Health status is updated on each check
        """
        self.logger.info(f"Starting {self.name}")
        self.logger.info(f"Monitoring -> {self.needs_action}")
        self.logger.info(f"Check interval: {self.check_interval}s")
        self.logger.info("Press Ctrl+C to stop")

        consecutive_failures = 0
        max_consecutive_failures = 10

        try:
            while True:
                check_start = time.time()

                try:
                    # Check circuit breaker first
                    if self.enable_circuit_breaker:
                        if self.circuit_breaker.state == CircuitState.OPEN:
                            wait_time = self.circuit_breaker._time_until_retry()
                            self.logger.warning(
                                f"Circuit breaker open, waiting {wait_time:.1f}s before retry"
                            )
                            time.sleep(min(wait_time, self.check_interval))
                            continue

                    # Check for updates with circuit breaker protection
                    if self.enable_circuit_breaker:
                        items = self.circuit_breaker.call(self._check_with_retry)
                    else:
                        items = self._check_with_retry()

                    # Process items
                    for item in items:
                        try:
                            filepath = self.create_action_file(item)
                            self.logger.info(f"Created: {filepath.name}")
                        except Exception as e:
                            self.logger.error(f"Failed to create action file: {e}")
                            # Add to dead letter queue
                            self.dead_letter.add(
                                item_id=self.get_item_id(item),
                                error=e,
                                context={'source': self.name},
                                content=str(item)
                            )

                    # Reset failure counter on success
                    consecutive_failures = 0
                    self.health_monitor.record_health(self.name, "healthy")

                except CircuitBreakerOpenError as e:
                    self.logger.error(f"Circuit breaker is open: {e}")
                    consecutive_failures += 1
                    self.health_monitor.record_health(
                        self.name, "degraded",
                        {"reason": "circuit_breaker_open", "error": str(e)}
                    )

                except Exception as e:
                    consecutive_failures += 1
                    self.logger.error(f"Error during check: {e}")

                    # Update health based on failure count
                    if consecutive_failures >= 3:
                        status = "degraded"
                    else:
                        status = "healthy"

                    self.health_monitor.record_health(
                        self.name, status,
                        {"consecutive_failures": consecutive_failures, "last_error": str(e)}
                    )

                    # Give up after too many consecutive failures
                    if consecutive_failures >= max_consecutive_failures:
                        self.logger.critical(
                            f"Too many consecutive failures ({max_consecutive_failures}), stopping"
                        )
                        raise

                # Sleep until next check
                elapsed = time.time() - check_start
                sleep_time = max(0, self.check_interval - elapsed)
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            self.logger.info(f"{self.name} stopped by user")
            self.health_monitor.record_health(self.name, "stopped")
        except Exception as e:
            self.logger.critical(f"Fatal error: {e}")
            self.health_monitor.record_health(self.name, "down", {"error": str(e)})
            raise

    def _check_with_retry(self) -> List[Any]:
        """
        Check for updates with retry logic.

        This method is called by the circuit breaker.
        Transient errors are automatically retried.
        """
        if self.enable_retry:
            return self._retry_check()
        else:
            return self.check_for_updates()

    @with_retry(max_attempts=3, base_delay=2, backoff_factor=2)
    def _retry_check(self) -> List[Any]:
        """Wrapper for check_for_updates with retry decorator."""
        return self.check_for_updates()
