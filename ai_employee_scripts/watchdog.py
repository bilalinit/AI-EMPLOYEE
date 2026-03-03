#!/usr/bin/env python3
"""
Watchdog Process - Monitors and restarts the AI Employee Orchestrator

The orchestrator manages all watchers internally. If the orchestrator dies,
all watchers stop. This watchdog ensures the orchestrator stays alive.

Architecture:
    watchdog.py → monitors → orchestrator.py → manages → [all watchers]

Usage:
    python watchdog.py

Cron entry (to ensure watchdog runs 24/7):
    */5 * * * * /path/to/watchdog.py  # Check every 5 minutes
"""

import subprocess
import time
import logging
import signal
import sys
import os
from pathlib import Path
from datetime import datetime


# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR = Path(__file__).parent.resolve()
VAULT_PATH = SCRIPT_DIR.parent / 'AI_Employee_Vault'
LOG_DIR = VAULT_PATH / 'Logs'
PID_DIR = Path('/tmp')

ORCHESTRATOR_CMD = [
    sys.executable,
    str(SCRIPT_DIR / 'orchestrator.py'),
    str(VAULT_PATH)
]

CHECK_INTERVAL = 60  # seconds


# =============================================================================
# LOGGING SETUP
# =============================================================================

def setup_logging():
    """Configure logging to watchdog.log file."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    log_file = LOG_DIR / 'watchdog.log'

    logger = logging.getLogger('Watchdog')
    logger.setLevel(logging.INFO)

    if logger.handlers:
        logger.handlers.clear()

    # File handler
    handler = logging.FileHandler(log_file, mode='a')
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Also log to console
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    return logger


# =============================================================================
# PID FILE MANAGEMENT
# =============================================================================

PID_FILE = PID_DIR / 'ai_employee_orchestrator.pid'


def read_orchestrator_pid() -> int | None:
    """Read orchestrator PID from file."""
    if PID_FILE.exists():
        try:
            return int(PID_FILE.read_text().strip())
        except (ValueError, IOError):
            return None
    return None


def is_process_running(pid: int) -> bool:
    """Check if a process with given PID is running and active."""
    if pid is None:
        return False

    try:
        # Read /proc/{pid}/status to check if process is actually running
        # This catches suspended/dead processes that os.kill(pid, 0) misses
        status_file = Path(f'/proc/{pid}/status')
        if not status_file.exists():
            return False

        # Read the process status
        with open(status_file) as f:
            for line in f:
                if line.startswith('State:'):
                    # State format: "State: S (sleeping)" or "State: T (stopped)"
                    state = line.split()[1]
                    # T = stopped (traced), Z = zombie, X = dead
                    if state in ('T', 'Z', 'X'):
                        return False
                    return True

        # If we couldn't read state, fall back to kill check
        os.kill(pid, 0)
        return True

    except ProcessLookupError:
        return False
    except (PermissionError, FileNotFoundError):
        # Process doesn't exist or we can't access it
        return False
    except Exception:
        # Any other error, assume not running
        return False


# =============================================================================
# ORCHESTRATOR MANAGEMENT
# =============================================================================

def start_orchestrator(logger: logging.Logger) -> bool:
    """Start the orchestrator process."""
    try:
        logger.info("Starting orchestrator...")

        # Start orchestrator with stdout/stderr redirected to log files
        orchestrator_log = LOG_DIR / 'orchestrator_output.log'

        with open(orchestrator_log, 'a') as log_f:
            process = subprocess.Popen(
                ORCHESTRATOR_CMD,
                stdout=log_f,
                stderr=subprocess.STDOUT,
                start_new_session=True  # Create new process group
            )

        # Write PID file
        PID_FILE.write_text(str(process.pid))

        # Log startup event
        status_file = LOG_DIR / 'process_events.jsonl'
        with open(status_file, 'a') as f:
            f.write(f'{{"timestamp": "{datetime.now().isoformat()}", "event": "started", "process": "orchestrator", "pid": {process.pid}}}\n')

        logger.info(f"✅ Orchestrator started with PID {process.pid}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to start orchestrator: {e}")
        return False


def stop_orchestrator(logger: logging.Logger, signal_type: str = 'TERM'):
    """Stop the orchestrator process gracefully."""
    pid = read_orchestrator_pid()

    if not pid:
        logger.info("No orchestrator PID file found")
        return True

    if not is_process_running(pid):
        logger.info(f"Orchestrator PID {pid} not running")
        PID_FILE.unlink(missing_ok=True)
        return True

    try:
        logger.info(f"Stopping orchestrator (PID {pid}) with SIG{signal_type}...")

        if signal_type == 'TERM':
            os.kill(pid, signal.SIGTERM)
        else:
            os.kill(pid, signal.SIGKILL)

        # Wait for process to terminate
        for _ in range(10):
            time.sleep(0.5)
            if not is_process_running(pid):
                logger.info("✅ Orchestrator stopped")
                PID_FILE.unlink(missing_ok=True)
                return True

        # If still running, force kill
        if signal_type == 'TERM':
            logger.warning("Orchestrator did not stop gracefully, forcing...")
            return stop_orchestrator(logger, 'KILL')

    except ProcessLookupError:
        logger.info("Orchestrator already stopped")
        PID_FILE.unlink(missing_ok=True)
        return True
    except Exception as e:
        logger.error(f"❌ Error stopping orchestrator: {e}")

    return False


def check_orchestrator(logger: logging.Logger) -> bool:
    """Check if orchestrator is running, restart if needed."""
    pid = read_orchestrator_pid()

    if pid and is_process_running(pid):
        # Orchestrator is alive and well
        return True

    if pid:
        logger.warning(f"⚠️  Orchestrator (PID {pid}) is not running")
    else:
        logger.warning("⚠️  Orchestrator was never started")

    # Attempt restart
    logger.info("Attempting to restart orchestrator...")
    success = start_orchestrator(logger)

    if success:
        logger.info("✅ Orchestrator restarted successfully")
    else:
        logger.error("❌ Failed to restart orchestrator")

    return success


# =============================================================================
# WATCHDOG MAIN LOOP
# =============================================================================

running = True


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global running
    logger = logging.getLogger('Watchdog')
    logger.info(f"Received shutdown signal ({signum})")
    running = False


def main():
    """Main watchdog loop."""
    global running

    # Setup logging
    logger = setup_logging()

    logger.info("=" * 60)
    logger.info("AI EMPLOYEE WATCHDOG STARTED")
    logger.info("=" * 60)
    logger.info(f"Monitoring: orchestrator.py")
    logger.info(f"Check interval: {CHECK_INTERVAL}s")
    logger.info(f"Orchestrator command: {' '.join(ORCHESTRATOR_CMD)}")
    logger.info("")

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Check if orchestrator is already running
    pid = read_orchestrator_pid()
    if pid and is_process_running(pid):
        logger.info(f"✅ Orchestrator already running (PID {pid})")
    elif not os.getenv('WATCHDOG_ONLY_MONITOR'):  # Allow monitoring-only mode
        logger.info("Orchestrator not running, starting now...")
        start_orchestrator(logger)

    logger.info("")
    logger.info("Watchdog monitoring active...")
    logger.info("Press Ctrl+C to stop")
    logger.info("")

    # Main monitoring loop
    restart_count = 0
    max_restarts = 10  # Give up after 10 rapid restarts
    restart_window = 300  # 5 minutes
    restart_times = []

    while running:
        try:
            # Check orchestrator status
            pid = read_orchestrator_pid()

            if not pid or not is_process_running(pid):
                # Track restart time
                now = time.time()
                restart_times.append(now)

                # Remove restarts older than restart_window
                restart_times = [t for t in restart_times if now - t < restart_window]

                if len(restart_times) > max_restarts:
                    logger.critical(
                        f"Orchestrator has restarted {len(restart_times)} times in "
                        f"{restart_window}s - giving up to prevent restart loop"
                    )
                    logger.critical("Please check Logs/orchestrator_output.log for errors")
                    break

                restart_count += 1
                check_orchestrator(logger)

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            logger.error(f"Error in watchdog loop: {e}")
            time.sleep(CHECK_INTERVAL)

    # Cleanup on exit
    logger.info("Watchdog stopping...")

    # Optionally stop orchestrator when watchdog stops
    # (Commented out - let orchestrator run if watchdog is just being restarted)
    # stop_orchestrator(logger)

    logger.info(f"Watchdog stopped. Total restarts: {restart_count}")


if __name__ == "__main__":
    main()
