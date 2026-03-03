# Base Watcher Documentation

## Overview

`BaseWatcher` is an abstract base class that provides the foundation for all AI Employee watchers. It implements a consistent architecture for monitoring external sources (Gmail, filesystem, LinkedIn, etc.) and creating actionable tasks in the vault's `Needs_Action` folder.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        BaseWatcher                              │
├─────────────────────────────────────────────────────────────────┤
│  Abstract Methods (Must Implement):                             │
│  ├── check_for_updates()    → Return list of new items          │
│  ├── create_action_file()   → Create .md in Needs_Action        │
│  └── get_item_id()          → Return unique identifier          │
├─────────────────────────────────────────────────────────────────┤
│  Built-in Error Recovery:                                        │
│  ├── Retry with exponential backoff                             │
│  ├── Circuit breaker for API failures                           │
│  ├── Dead letter queue for failed items                         │
│  └── Health monitoring                                          │
└─────────────────────────────────────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ FileSystem   │      │   Gmail      │      │  LinkedIn    │
│  Watcher     │      │  Watcher     │      │  Watcher     │
└──────────────┘      └──────────────┘      └──────────────┘
```

## Key Features

### 1. Abstract Interface

All watchers must implement three methods:

| Method | Purpose | Return |
|--------|---------|--------|
| `check_for_updates()` | Poll external source for new items | `List[Any]` |
| `create_action_file(item)` | Create task file in Needs_Action | `Path` |
| `get_item_id(item)` | Get unique identifier for deduplication | `str` |

### 2. Error Recovery Patterns

The `BaseWatcher` includes enterprise-grade error recovery:

#### Retry with Exponential Backoff
```python
@with_retry(max_attempts=3, base_delay=2, backoff_factor=2)
def _retry_check(self) -> List[Any]:
    return self.check_for_updates()
```

- **Max attempts:** 3
- **Base delay:** 2 seconds
- **Backoff factor:** 2x (2s → 4s → 8s)

#### Circuit Breaker Pattern
Prevents cascading failures when external APIs are down:

| State | Behavior |
|-------|----------|
| **Closed** (normal) | Requests pass through, failures count toward threshold |
| **Open** (failing) | Requests fail immediately, timeout before retry |
| **Half-Open** | Test request sent to check if service recovered |

Configuration:
- **Failure threshold:** 5 failures
- **Timeout:** 60 seconds before attempting recovery

#### Dead Letter Queue
Failed items are stored for later inspection:

```python
self.dead_letter.add(
    item_id=self.get_item_id(item),
    error=e,
    context={'source': self.name},
    content=str(item)
)
```

Stored in: `AI_Employee_Vault/Failed/{watcher_name}/`

#### Health Monitoring
Health status tracked in memory:

| Status | Condition |
|--------|-----------|
| `healthy` | Normal operation |
| `degraded` | 3+ consecutive failures |
| `down` | Max failures (10) reached |
| `stopped` | User interrupted with Ctrl+C |

### 3. Main Loop

The `run()` method implements the polling loop:

```
┌─────────────────────────────────────────────────────────────┐
│                     Main Loop                                │
├─────────────────────────────────────────────────────────────┤
│  1. Check circuit breaker state                              │
│     ├── If OPEN: Wait for timeout, then continue            │
│     └── If CLOSED: Proceed                                  │
├─────────────────────────────────────────────────────────────┤
│  2. Check for updates (with retry)                          │
│     └── items = self._check_with_retry()                    │
├─────────────────────────────────────────────────────────────┤
│  3. Process each item                                       │
│     ├── Try: create_action_file(item)                       │
│     └── Catch: Add to dead letter queue                     │
├─────────────────────────────────────────────────────────────┤
│  4. Update health status                                    │
├─────────────────────────────────────────────────────────────┤
│  5. Sleep until next check                                  │
└─────────────────────────────────────────────────────────────┘
```

### 4. Logging

Structured logging format:

```
2026-02-28 10:30:45 | FileSystemWatcher | INFO | Starting FileSystemWatcher
```

Format:
- Timestamp: `YYYY-MM-DD HH:MM:SS`
| Component | Description |
|-----------|-------------|
| Timestamp | ISO-8601 date/time |
| Name | Watcher class name |
| Level | INFO, WARNING, ERROR, CRITICAL |
| Message | Log message |

## Constructor Parameters

```python
def __init__(
    self,
    vault_path: str,              # Path to AI_Employee_Vault
    check_interval: int = 60,     # Seconds between checks
    name: Optional[str] = None,   # Watcher name (default: class name)
    enable_circuit_breaker: bool = True,  # Enable circuit breaker
    enable_retry: bool = True     # Enable retry logic
)
```

## Helper Methods

### `_create_markdown_header()`

Creates standard YAML frontmatter for action files:

```python
header = self._create_markdown_header(
    item_type="email",
    message_id="12345",
    priority="high"
)
```

Output:
```yaml
---
type: email
source: WatcherName
created: 2026-02-28T10:30:45
status: pending
priority: medium
message_id: 12345
---
```

## Creating a New Watcher

To create a new watcher, inherit from `BaseWatcher`:

```python
from base_watcher import BaseWatcher
from pathlib import Path
from typing import List

class MyWatcher(BaseWatcher):
    def __init__(self, vault_path: str, check_interval: int = 60):
        super().__init__(vault_path, check_interval, name="MyWatcher")

    def check_for_updates(self) -> List:
        """Check external source for new items."""
        # Your implementation here
        return []

    def create_action_file(self, item) -> Path:
        """Create task file in Needs_Action."""
        task_file = self.needs_action / f"TASK_{item['id']}.md"
        task_file.write_text(f"# Task for {item['id']}")
        return task_file

    def get_item_id(self, item) -> str:
        """Return unique identifier."""
        return item['id']
```

## Error Recovery Module Dependencies

`BaseWatcher` depends on `error_recovery.py` for:

- `@with_retry` decorator
- `CircuitBreaker` class
- `DeadLetterQueue` class
- `HealthMonitor` class
- `GracefulDegradation` class
- `is_transient_error()` function
- `CircuitBreakerOpenError` exception

## File Paths

| Path | Purpose |
|------|---------|
| `vault_path / Needs_Action/` | Task files created here |
| `vault_path / Inbox/` | Original content stored here |
| `vault_path / Failed/` | Failed items stored here |
| `vault_path / Failed/{name}/` | Dead letter queue for this watcher |
| `vault_path / Logs/` | Health status and circuit breaker state |

## Usage Example

```python
from watchers.base_watcher import BaseWatcher

# Watcher is abstract - use concrete implementations
from watchers.filesystem_watcher import FileSystemWatcher

watcher = FileSystemWatcher(
    vault_path="/path/to/AI_Employee_Vault",
    check_interval=120  # Check every 2 minutes
)

watcher.run()  # Press Ctrl+C to stop
```

## Implementation Notes

1. **Thread Safety:** Not thread-safe. Run one watcher instance per process.
2. **Signal Handling:** Catches `KeyboardInterrupt` for graceful shutdown.
3. **State Persistence:** Processed IDs must be tracked by subclasses.
4. **WSL Compatibility:** Polling-based design works on WSL/network filesystems.

## Related Files

- `watchers/filesystem_watcher.py` - File drop monitoring
- `watchers/gmail_watcher.py` - Gmail monitoring via OAuth
- `watchers/linkedin_watcher.py` - LinkedIn monitoring via Playwright
- `error_recovery.py` - Error recovery utilities
