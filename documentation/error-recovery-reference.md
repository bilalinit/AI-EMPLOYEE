# Error Recovery Reference

**Part of:** Personal AI Employee - Gold/Platinum Tier
**Last Updated:** March 2026

---

## Overview

The AI Employee implements a 3-layer error recovery architecture to ensure 24/7 reliability.

---

## 3-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                  ERROR RECOVERY ARCHITECTURE                         │
└─────────────────────────────────────────────────────────────────────┘

Layer 1: External Watchdog
┌─────────────────────────────────────────────────────────────────────┐
│  watchdog.py                                                        │
│  - Monitors orchestrator process                                    │
│  - Auto-restarts if crashed                                         │
│  - Rate limits restarts (max 10 in 5 min)                          │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
Layer 2: Internal Watchdog
┌─────────────────────────────────────────────────────────────────────┐
│  orchestrator.py                                                    │
│  - Monitors watcher subprocesses                                    │
│  - Restarts crashed watchers                                        │
│  - Tracks restart history                                           │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
Layer 3: Operation-Level Recovery
┌─────────────────────────────────────────────────────────────────────┐
│  error_recovery.py                                                  │
│  - Retry with exponential backoff                                   │
│  - Circuit breaker pattern                                          │
│  - Dead letter queue                                                │
│  - Health monitoring                                                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: External Watchdog

**File:** `ai_employee_scripts/watchdog.py`

### Purpose

Monitors the orchestrator process and restarts it if it crashes.

### How It Works

```python
class Watchdog:
    def __init__(self, pid_file: str, check_interval: int = 60):
        self.pid_file = pid_file
        self.check_interval = check_interval
        self.restart_count = 0
        self.restart_window = 300  # 5 minutes
        self.max_restarts = 10
```

### States

| State | Description |
|-------|-------------|
| **Running** | Orchestrator PID is active |
| **Crashed** | PID not found, process dead |
| **Rate Limited** | Too many restarts, waiting |

### Process Check

```python
def is_process_running(self, pid: int) -> bool:
    try:
        os.kill(pid, 0)  # Signal 0 = check if exists
        return True
    except OSError:
        return False
```

### Restart Logic

```python
def restart_orchestrator(self):
    if self.restart_count >= self.max_restarts:
        # Wait for window to reset
        elapsed = time.time() - self.first_restart_time
        if elapsed < self.restart_window:
            self.log_rate_limited()
            return
        else:
            self.restart_count = 0  # Reset counter

    # Restart process
    subprocess.Popen(["uv", "run", "python", "orchestrator.py"])
    self.restart_count += 1
```

### Log File

Location: `AI_Employee_Vault/Logs/watchdog.log`

```
2026-03-14 10:00:00 | INFO | Starting watchdog
2026-03-14 10:01:00 | INFO | Orchestrator running (PID: 12345)
2026-03-14 10:02:00 | ERROR | Orchestrator crashed
2026-03-14 10:02:00 | INFO | Restarting orchestrator (attempt 1)
```

---

## Layer 2: Internal Watchdog

**File:** `ai_employee_scripts/orchestrator.py`

### Purpose

Monitors watcher subprocesses and restarts them if they crash.

### Watcher Management

```python
def _watchdog_watchers(self):
    while self.running:
        for name, watcher_info in self.watchers.items():
            process = watcher_info.get('process')
            if process and process.poll() is not None:
                # Process has exited
                self._restart_watcher(name)
        time.sleep(30)  # Check every 30 seconds
```

### Restart Tracking

Location: `AI_Employee_Vault/Logs/watcher_restarts.jsonl`

```json
{"timestamp": "2026-03-14T10:00:00", "watcher": "GmailWatcher", "reason": "exit_code_1", "attempt": 1}
{"timestamp": "2026-03-14T10:05:00", "watcher": "LinkedInWatcher", "reason": "timeout", "attempt": 1}
```

---

## Layer 3: Operation-Level Recovery

**File:** `ai_employee_scripts/error_recovery.py`

### Components

1. **Retry with Exponential Backoff**
2. **Circuit Breaker Pattern**
3. **Dead Letter Queue**
4. **Health Monitor**

---

### Retry with Exponential Backoff

Retries transient failures with increasing delays.

```python
from functools import wraps
import time

def with_retry(max_attempts: int = 3, base_delay: float = 2.0, backoff_factor: float = 2.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if is_transient_error(e) and attempt < max_attempts - 1:
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        raise
        return wrapper
    return decorator
```

**Usage:**

```python
@with_retry(max_attempts=3, base_delay=2, backoff_factor=2)
def check_gmail():
    # API call that might fail
    pass
```

**Retry Schedule:**
| Attempt | Delay |
|---------|-------|
| 1 | Immediate |
| 2 | 2 seconds |
| 3 | 4 seconds |
| Fail | Raise exception |

**Transient Errors:**
- Connection timeout
- Rate limit (429)
- Server error (5xx)
- Network unreachable

---

### Circuit Breaker Pattern

Prevents cascading failures by "breaking" the circuit after repeated failures.

```python
class CircuitBreaker:
    STATES = ['closed', 'open', 'half_open']

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.state = 'closed'
        self.last_failure_time = None
```

**States:**

| State | Description | Behavior |
|-------|-------------|----------|
| **Closed** | Normal operation | Requests pass through |
| **Open** | Failing | Requests fail immediately |
| **Half-Open** | Testing recovery | One test request allowed |

**State Transitions:**

```
Closed ──(5 failures)──▶ Open
   ▲                         │
   │                         │ (60s timeout)
   │                         ▼
   └──(success)──────── Half-Open
                              │
                              │ (failure)
                              ▼
                           Open
```

**Usage:**

```python
breaker = CircuitBreaker(failure_threshold=5, timeout=60)

def call_api():
    if breaker.state == 'open':
        raise CircuitBreakerOpenError()
    try:
        result = external_api_call()
        breaker.record_success()
        return result
    except Exception as e:
        breaker.record_failure()
        raise
```

**State File:** `AI_Employee_Vault/Logs/circuit_breakers.json`

```json
{
  "GmailWatcher": {
    "state": "closed",
    "failure_count": 0,
    "last_failure": null
  },
  "LinkedInWatcher": {
    "state": "open",
    "failure_count": 5,
    "last_failure": "2026-03-14T10:00:00"
  }
}
```

---

### Dead Letter Queue

Stores failed items for later inspection and retry.

```python
class DeadLetterQueue:
    def __init__(self, vault_path: str, subdir: str = "failed"):
        self.queue_dir = Path(vault_path) / "Failed" / subdir

    def add(self, item_id: str, error: Exception, context: dict, content: str):
        entry = {
            "item_id": item_id,
            "failed_at": datetime.now().isoformat(),
            "error": str(error),
            "error_type": type(error).__name__,
            "context": context,
            "content": content
        }
        file_path = self.queue_dir / f"{item_id}.json"
        file_path.write_text(json.dumps(entry, indent=2))
```

**Storage Location:**

```
AI_Employee_Vault/Failed/
├── GmailWatcher/
│   ├── msg_12345.json
│   └── msg_67890.json
├── LinkedInWatcher/
│   └── thread_abcde.json
└── FileSystemWatcher/
    └── file_fghij.json
```

**Failed Item Format:**

```json
{
  "item_id": "msg_12345",
  "failed_at": "2026-03-14T10:30:00",
  "error": "Connection timeout after 30 seconds",
  "error_type": "TimeoutError",
  "context": {
    "source": "GmailWatcher",
    "message_id": "12345",
    "attempts": 3
  },
  "content": "Original email content..."
}
```

---

### Health Monitor

Tracks component health status.

```python
class HealthMonitor:
    STATUS_HEALTHY = 'healthy'
    STATUS_DEGRADED = 'degraded'
    STATUS_DOWN = 'down'

    def __init__(self, max_failures: int = 10):
        self.max_failures = max_failures
        self.consecutive_failures = 0
        self.status = self.STATUS_HEALTHY

    def record_failure(self):
        self.consecutive_failures += 1
        if self.consecutive_failures >= self.max_failures:
            self.status = self.STATUS_DOWN
        elif self.consecutive_failures >= 3:
            self.status = self.STATUS_DEGRADED

    def record_success(self):
        self.consecutive_failures = 0
        self.status = self.STATUS_HEALTHY
```

**Health States:**

| State | Condition | Behavior |
|-------|-----------|----------|
| `healthy` | 0-2 consecutive failures | Normal operation |
| `degraded` | 3-9 consecutive failures | Continue with warnings |
| `down` | 10+ consecutive failures | Stop attempting |

**State File:** `AI_Employee_Vault/Logs/health_status.json`

```json
{
  "GmailWatcher": {
    "status": "healthy",
    "consecutive_failures": 0,
    "last_success": "2026-03-14T10:30:00",
    "last_failure": null
  },
  "LinkedInWatcher": {
    "status": "degraded",
    "consecutive_failures": 4,
    "last_success": "2026-03-14T10:00:00",
    "last_failure": "2026-03-14T10:25:00"
  }
}
```

---

## Error Classification

### Transient Errors (Retry)

| Error Type | Description | Retry? |
|------------|-------------|--------|
| `ConnectionError` | Network unreachable | ✅ Yes |
| `TimeoutError` | Request timed out | ✅ Yes |
| `HTTP 429` | Rate limited | ✅ Yes (after delay) |
| `HTTP 503` | Service unavailable | ✅ Yes |
| `HTTP 500` | Server error | ✅ Yes |

### Permanent Errors (No Retry)

| Error Type | Description | Retry? |
|------------|-------------|--------|
| `HTTP 401` | Unauthorized | ❌ No |
| `HTTP 403` | Forbidden | ❌ No |
| `HTTP 404` | Not found | ❌ No |
| `HTTP 400` | Bad request | ❌ No |
| `ValueError` | Invalid input | ❌ No |

### Error Detection

```python
def is_transient_error(error: Exception) -> bool:
    """Check if error is transient and should be retried."""
    if isinstance(error, (ConnectionError, TimeoutError)):
        return True
    if hasattr(error, 'status_code'):
        if error.status_code in [429, 500, 502, 503, 504]:
            return True
    return False
```

---

## Graceful Degradation

When components fail, the system continues with reduced functionality.

```python
class GracefulDegradation:
    def __init__(self, vault_path: str):
        self.health = HealthMonitor()
        self.fallback_mode = False

    def execute_with_fallback(self, primary_action, fallback_action=None):
        if self.health.status == 'down':
            if fallback_action:
                return fallback_action()
            return None
        try:
            result = primary_action()
            self.health.record_success()
            return result
        except Exception as e:
            self.health.record_failure()
            if fallback_action and self.health.status != 'down':
                return fallback_action()
            raise
```

---

## Recovery Procedures

### Manual Recovery

```bash
# Check circuit breaker state
cat AI_Employee_Vault/Logs/circuit_breakers.json

# Reset circuit breaker
echo '{}' > AI_Employee_Vault/Logs/circuit_breakers.json

# Check health status
cat AI_Employee_Vault/Logs/health_status.json

# Reset health
echo '{}' > AI_Employee_Vault/Logs/health_status.json

# View dead letter queue
ls AI_Employee_Vault/Failed/

# Re-process failed item
mv AI_Employee_Vault/Failed/GmailWatcher/msg_12345.json AI_Employee_Vault/Needs_Action/
```

### Automatic Recovery

The system automatically recovers when:
1. Transient errors resolve
2. Circuit breaker timeout expires
3. Health monitor receives success

---

## Monitoring

### Key Metrics

| Metric | Location | Purpose |
|--------|----------|---------|
| `health_status.json` | Logs/ | Component health |
| `circuit_breakers.json` | Logs/ | Circuit states |
| `watcher_restarts.jsonl` | Logs/ | Restart history |
| `process_events.jsonl` | Logs/ | Process lifecycle |

### Log Analysis

```bash
# Check for errors
grep ERROR AI_Employee_Vault/Logs/orchestrator_*.log

# Count circuit breaker trips
cat AI_Employee_Vault/Logs/circuit_breakers.json | grep -o '"open"' | wc -l

# View recent failures
tail -20 AI_Employee_Vault/Logs/watcher_restarts.jsonl
```

---

## Best Practices

1. **Always use retry decorator** for API calls
2. **Check circuit breaker state** before API calls
3. **Log all failures** to appropriate files
4. **Add failed items to DLQ** for manual review
5. **Monitor health status** regularly
6. **Implement fallback actions** where possible

---

**Related Documentation:**
- [Getting Started Guide](getting-started.md)
- [Cloud Deployment Guide](cloud-deployment.md)
- [Vault Structure Guide](vault-structure.md)