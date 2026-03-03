#!/usr/bin/env python3
"""
Error Recovery Module - Layer 3 Resilience for AI Employee

Provides decorators and utilities for:
- Retry with exponential backoff
- Circuit breaker pattern
- Dead letter queue handling
- Graceful degradation

Usage:
    from error_recovery import with_retry, CircuitBreaker, DeadLetterQueue

    @with_retry(max_attempts=3, base_delay=1, max_delay=60)
    def api_call():
        # Your API call here
        pass

    breaker = CircuitBreaker(name="gmail_api", failure_threshold=5, timeout=60)

    @breaker
    def gmail_api_call():
        # Your Gmail API call
        pass
"""

import time
import functools
import logging
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Callable, Any, Optional, Type, Tuple, List
from enum import Enum
import threading


# Export CircuitState for easier imports
__all__ = [
    'with_retry', 'CircuitBreaker', 'CircuitState', 'CircuitBreakerOpenError',
    'DeadLetterQueue', 'GracefulDegradation', 'HealthMonitor',
    'TransientError', 'PermanentError',
    'is_transient_error', 'get_circuit_breaker'
]


# =============================================================================
# CONFIGURATION
# =============================================================================

VAULT_PATH = Path(__file__).parent.parent / 'AI_Employee_Vault'
LOG_DIR = VAULT_PATH / 'Logs'
FAILED_DIR = VAULT_PATH / 'Failed'

# Ensure directories exist
LOG_DIR.mkdir(parents=True, exist_ok=True)
FAILED_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# EXCEPTIONS
# =============================================================================

class TransientError(Exception):
    """Error that is transient and can be retried."""
    pass


class PermanentError(Exception):
    """Error that is permanent and should not be retried."""
    pass


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


# =============================================================================
# RETRY DECORATOR WITH EXPONENTIAL BACKOFF
# =============================================================================

def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None
) -> Callable:
    """
    Decorator to retry a function with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        backoff_factor: Multiplier for delay after each failure
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback function called on each retry

    Returns:
        Decorated function that retries on failure

    Example:
        @with_retry(max_attempts=3, base_delay=1)
        def fetch_data():
            return requests.get("https://api.example.com/data")
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = logging.getLogger(func.__module__)

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    is_last = attempt == max_attempts - 1

                    if is_last:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (backoff_factor ** attempt), max_delay)

                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1}/{max_attempts} "
                        f"failed: {e}. Retrying in {delay:.1f}s"
                    )

                    # Call on_retry callback if provided
                    if on_retry:
                        on_retry(attempt + 1, e, delay)

                    time.sleep(delay)

        return wrapper
    return decorator


# =============================================================================
# CIRCUIT BREAKER PATTERN
# =============================================================================

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.

    Tracks failures and opens the circuit after threshold is reached.
    While open, requests fail fast without hitting the service.
    After timeout, enters half-open state to test recovery.

    Usage:
        breaker = CircuitBreaker("gmail_api", failure_threshold=5, timeout=60)

        @breaker
        def call_gmail_api():
            # API call here
    """

    _instances: 'CircuitBreakerRegistry' = None

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        half_open_attempts: int = 1
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Unique name for this circuit breaker
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds before trying half-open state
            half_open_attempts: Number of successful calls to close circuit
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_attempts = half_open_attempts

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._lock = threading.Lock()

        # Load previous state if exists
        self._load_state()

        # Register global instance
        if CircuitBreaker._instances is None:
            CircuitBreaker._instances = CircuitBreakerRegistry()
        CircuitBreaker._instances.register(self)

    def __call__(self, func: Callable) -> Callable:
        """Decorator to use circuit breaker."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return self.call(func, *args, **kwargs)
        return wrapper

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker."""
        logger = logging.getLogger(func.__module__)

        with self._lock:
            # Check if we should try to close or half-open
            self._check_state_transition()

            # Fail fast if circuit is open
            if self._state == CircuitState.OPEN:
                raise CircuitBreakerOpenError(
                    f"Circuit '{self.name}' is open (failures: {self._failure_count}). "
                    f"Try again in {self._time_until_retry():.1f}s"
                )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise

    def _check_state_transition(self):
        """Check if circuit should change state based on time."""
        now = time.time()

        if self._state == CircuitState.OPEN:
            if self._last_failure_time and (now - self._last_failure_time) >= self.timeout:
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
                self._log_state_transition("HALF_OPEN")

    def _on_success(self):
        """Handle successful call."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.half_open_attempts:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._log_state_transition("CLOSED")
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success in closed state
                self._failure_count = max(0, self._failure_count - 1)

    def _on_failure(self):
        """Handle failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Failed in half-open, go back to open
                self._state = CircuitState.OPEN
                self._log_state_transition("OPEN")
            elif self._failure_count >= self.failure_threshold:
                if self._state != CircuitState.OPEN:
                    self._state = CircuitState.OPEN
                    self._log_state_transition("OPEN")

    def _time_until_retry(self) -> float:
        """Calculate seconds until circuit can be tried again."""
        if self._state != CircuitState.OPEN or not self._last_failure_time:
            return 0.0
        elapsed = time.time() - self._last_failure_time
        return max(0.0, self.timeout - elapsed)

    def _log_state_transition(self, new_state: str):
        """Log state transition."""
        logger = logging.getLogger("CircuitBreaker")
        logger.info(
            f"Circuit '{self.name}' → {new_state} "
            f"(failures: {self._failure_count})"
        )

        # Save state to file
        self._save_state()

    def _save_state(self):
        """Save circuit breaker state to file."""
        state_file = LOG_DIR / 'circuit_breakers.json'
        states = {}

        if state_file.exists():
            try:
                states = json.loads(state_file.read_text())
            except:
                pass

        states[self.name] = {
            'state': self._state.value,
            'failure_count': self._failure_count,
            'last_failure': self._last_failure_time,
            'updated': datetime.now().isoformat()
        }

        state_file.write_text(json.dumps(states, indent=2))

    def _load_state(self):
        """Load circuit breaker state from file."""
        state_file = LOG_DIR / 'circuit_breakers.json'

        if not state_file.exists():
            return

        try:
            states = json.loads(state_file.read_text())
            if self.name in states:
                saved = states[self.name]
                self._state = CircuitState(saved['state'])
                self._failure_count = saved.get('failure_count', 0)
                self._last_failure_time = saved.get('last_failure')

                # Reset to closed if state is stale (> timeout)
                if self._state == CircuitState.OPEN and self._last_failure_time:
                    if time.time() - self._last_failure_time > self.timeout:
                        self._state = CircuitState.CLOSED
        except:
            pass

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        return self._failure_count

    def reset(self):
        """Manually reset circuit breaker to closed state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            self._save_state()


class CircuitBreakerRegistry:
    """Registry for all circuit breakers."""

    def __init__(self):
        self._breakers: dict = {}

    def register(self, breaker: CircuitBreaker):
        """Register a circuit breaker."""
        self._breakers[breaker.name] = breaker

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get a circuit breaker by name."""
        return self._breakers.get(name)

    def get_all(self) -> dict:
        """Get all circuit breakers."""
        return self._breakers.copy()

    def get_status(self) -> dict:
        """Get status of all circuit breakers."""
        return {
            name: {
                'state': breaker.state.value,
                'failures': breaker.failure_count
            }
            for name, breaker in self._breakers.items()
        }


# =============================================================================
# DEAD LETTER QUEUE
# =============================================================================

class DeadLetterQueue:
    """
    Handle items that have failed after all retries.

    Moves failed items to Needs_Action/Failed/ with metadata
    for manual review or reprocessing.
    """

    def __init__(self, subdir: str = "general"):
        """
        Initialize dead letter queue.

        Args:
            subdir: Subdirectory within Failed/ for this queue
        """
        self.failed_dir = FAILED_DIR / subdir
        self.failed_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger("DeadLetterQueue")

    def add(
        self,
        item_id: str,
        error: Exception,
        context: dict,
        content: str = ""
    ) -> Path:
        """
        Add a failed item to the dead letter queue.

        Args:
            item_id: Unique identifier for the failed item
            error: The exception that caused the failure
            context: Additional context about the failure
            content: Original content that failed

        Returns:
            Path to the created dead letter file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_id = self._sanitize_filename(item_id)
        filename = f"FAILED_{safe_id}_{timestamp}.md"
        filepath = self.failed_dir / filename

        # Create metadata
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'item_id': item_id,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'retry_count': context.get('retry_count', 0)
        }

        # Create markdown file
        content = f"""---
type: failed_item
source: {context.get('source', 'unknown')}
failed: {datetime.now().isoformat()}
error_type: {type(error).__name__}
---

# Failed Item: {item_id}

## Error
**{type(error).__name__}:** {error}

## Context
```json
{json.dumps(metadata, indent=2)}
```

## Original Content
```
{content}
```

## Actions Required
- [ ] Review the error and determine if retry is safe
- [ ] Fix underlying issue if permanent error
- [ ] Move to Needs_Action/ to retry, or to Done/ to discard

---
*Added to dead letter queue by AI Employee*
"""

        filepath.write_text(content)
        self.logger.error(f"Item {item_id} moved to dead letter queue: {filepath.name}")

        # Log to JSON lines file for tracking
        self._log_to_jsonl(metadata)

        return filepath

    def _sanitize_filename(self, text: str) -> str:
        """Sanitize text for use in filename."""
        text = text.replace('/', '_').replace('\\', '_')
        text = text.replace(':', '_').replace(' ', '_')
        return ''.join(c if c.isalnum() or c in '._-' else '_' for c in text)

    def _log_to_jsonl(self, metadata: dict):
        """Log failure to JSON lines file."""
        log_file = LOG_DIR / 'dead_letter_queue.jsonl'
        with open(log_file, 'a') as f:
            f.write(json.dumps(metadata) + '\n')

    def list_failed(self) -> List[Path]:
        """List all failed items in this queue."""
        return list(self.failed_dir.glob('FAILED_*.md'))

    def retry_item(self, filepath: Path, target_dir: Path):
        """
        Move a failed item back to processing.

        Args:
            filepath: Path to the failed item file
            target_dir: Target directory (usually Needs_Action/)
        """
        if not filepath.exists():
            raise FileNotFoundError(f"Failed item not found: {filepath}")

        # Create retry marker
        new_path = target_dir / filepath.name.replace('FAILED_', 'RETRY_')
        filepath.rename(new_path)

        self.logger.info(f"Moved {filepath.name} to {new_path.name}")


# =============================================================================
# GRACEFUL DEGRADATION
# =============================================================================

class GracefulDegradation:
    """
    Handle service unavailability gracefully.

    When external services are down, queue operations locally
    for later processing.
    """

    def __init__(self, service_name: str):
        """
        Initialize graceful degradation handler.

        Args:
            service_name: Name of the service being monitored
        """
        self.service_name = service_name
        self.queue_dir = VAULT_PATH / 'Needs_Action' / 'Queued' / service_name
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger("GracefulDegradation")

    def queue_operation(self, operation: str, data: dict) -> Path:
        """
        Queue an operation for later processing.

        Args:
            operation: Name of the operation to queue
            data: Data needed for the operation

        Returns:
            Path to the queued operation file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:22]
        filename = f"QUEUED_{operation}_{timestamp}.json"
        filepath = self.queue_dir / filename

        queue_item = {
            'timestamp': datetime.now().isoformat(),
            'service': self.service_name,
            'operation': operation,
            'data': data,
            'status': 'pending'
        }

        filepath.write_text(json.dumps(queue_item, indent=2))
        self.logger.info(f"Queued {operation} for {self.service_name}: {filepath.name}")

        return filepath

    def list_queued(self) -> List[Path]:
        """List all queued operations."""
        return list(self.queue_dir.glob('QUEUED_*.json'))

    def process_queued(self, processor: Callable):
        """
        Process all queued operations.

        Args:
            processor: Function to process each queued item
        """
        queued = self.list_queued()
        self.logger.info(f"Processing {len(queued)} queued operations for {self.service_name}")

        for item_path in queued:
            try:
                item = json.loads(item_path.read_text())
                processor(item)
                item_path.unlink()  # Remove after successful processing
                self.logger.info(f"Processed queued item: {item_path.name}")
            except Exception as e:
                self.logger.error(f"Failed to process {item_path.name}: {e}")


# =============================================================================
# HEALTH MONITORING
# =============================================================================

class HealthMonitor:
    """
    Track and report health of system components.

    Logs health status to file for dashboard consumption.
    """

    def __init__(self):
        self.health_file = LOG_DIR / 'health_status.json'
        self.logger = logging.getLogger("HealthMonitor")

    def record_health(
        self,
        component: str,
        status: str,  # healthy, degraded, down
        details: dict = None
    ):
        """
        Record health status of a component.

        Args:
            component: Name of the component
            status: Health status (healthy, degraded, down)
            details: Optional additional details
        """
        health = self._load_health()
        health[component] = {
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        self._save_health(health)

    def _load_health(self) -> dict:
        """Load current health status."""
        if self.health_file.exists():
            try:
                return json.loads(self.health_file.read_text())
            except:
                pass
        return {}

    def _save_health(self, health: dict):
        """Save health status."""
        self.health_file.write_text(json.dumps(health, indent=2))

    def get_status(self) -> dict:
        """Get current health status of all components."""
        return self._load_health()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_circuit_breaker(name: str, **kwargs) -> CircuitBreaker:
    """Get or create a circuit breaker by name."""
    registry = CircuitBreaker._instances
    if registry is None:
        registry = CircuitBreakerRegistry()

    breaker = registry.get(name)
    if breaker is None:
        breaker = CircuitBreaker(name, **kwargs)
    return breaker


def is_transient_error(error: Exception) -> bool:
    """
    Determine if an error is transient (retryable).

    Transient errors:
    - Network timeouts
    - Connection errors
    - Rate limiting (429)
    - Service unavailable (503)

    Permanent errors:
    - Authentication failures (401, 403)
    - Not found (404)
    - Bad request (400)
    """
    error_str = str(error).lower()

    # Check for common transient error patterns
    transient_patterns = [
        'timeout',
        'connection',
        'network',
        'rate limit',
        '429',  # Too Many Requests
        '503',  # Service Unavailable
        '502',  # Bad Gateway
        '504',  # Gateway Timeout
        'temporary',
        'transient'
    ]

    permanent_patterns = [
        '401',  # Unauthorized
        '403',  # Forbidden
        '404',  # Not Found
        '400',  # Bad Request
        'authentication',
        'authorization',
        'permission',
        'not found'
    ]

    # Check for permanent errors first
    for pattern in permanent_patterns:
        if pattern in error_str:
            return False

    # Check for transient errors
    for pattern in transient_patterns:
        if pattern in error_str:
            return True

    # Default to transient for unknown errors
    return True
