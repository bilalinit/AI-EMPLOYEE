#!/usr/bin/env python3
"""
AI Employee Orchestrator - Master Controller

The orchestrator is the 24/7 master process that:
1. Starts and manages all watcher scripts
2. Monitors Needs_Action folder for new tasks
3. Triggers Claude Code to process tasks
4. Handles graceful shutdown

Architecture:
    Watchers → Create files in Needs_Action/
         ↓
    Orchestrator → Detects new files
         ↓
    Orchestrator → Triggers Claude Code (/process-tasks)
         ↓
    Claude Code → Reads, plans, creates approval requests
"""

import subprocess
import time
import threading
import logging
from pathlib import Path
from typing import List, Set, Dict
from datetime import datetime
import signal
import sys
import os


class AIEmployeeOrchestrator:
    """
    Master controller for the AI Employee system.

    Runs 24/7 as a daemon process, managing watchers and
    triggering Claude Code when tasks arrive.
    """

    def __init__(self, vault_path: str, scripts_path: str = None):
        """
        Initialize the orchestrator.

        Args:
            vault_path: Path to AI_Employee_Vault
            scripts_path: Path to ai_employee_scripts (default: sibling of vault)
        """
        self.vault_path = Path(vault_path)
        if scripts_path is None:
            self.scripts_path = self.vault_path.parent / "ai_employee_scripts"
        else:
            self.scripts_path = Path(scripts_path)

        # Folder paths
        self.needs_action = self.vault_path / "Needs_Action"
        self.approved = self.vault_path / "Approved"
        self.logs = self.vault_path / "Logs"

        # Process management
        self.watcher_processes: List[subprocess.Popen] = []
        self.watcher_configs: List[dict] = []  # Store configs for restart
        self.running = True
        self._shutdown_event = threading.Event()

        # Track processed files to avoid re-processing
        self.processed_files: Set[str] = set()

        # Setup logging
        self._setup_logging()

        # Write PID file for watchdog
        self._write_pid()

        # Ensure folders exist
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.approved.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)

    def _setup_logging(self):
        """Configure logging for the orchestrator."""
        self.logger = logging.getLogger("Orchestrator")
        self.logger.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler (append to daily log)
        log_file = self.vault_path / "Logs" / f"orchestrator_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(console_formatter)
        self.logger.addHandler(file_handler)

    def _write_pid(self):
        """Write orchestrator PID to file for watchdog monitoring."""
        pid_file = Path('/tmp/ai_employee_orchestrator.pid')
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text(str(os.getpid()))

    def _clear_pid(self):
        """Remove orchestrator PID file."""
        pid_file = Path('/tmp/ai_employee_orchestrator.pid')
        if pid_file.exists():
            pid_file.unlink()

    def call_claude_skill(self, skill_name: str) -> bool:
        """
        Execute Claude Code skill non-interactively.

        Uses stdin input like: echo "/skill" | claude code -p

        Args:
            skill_name: Name of the skill to execute (e.g., 'process-tasks')

        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Calling Claude Code: /{skill_name}")
        self.logger.info(f"Working directory: {self.vault_path}")

        # Build the command - use stdin with permissions to edit files
        command = [
            'claude', 'code', '-p',
            '--dangerously-skip-permissions'  # Bypass permission checks for file operations
        ]
        input_text = f'/{skill_name}\n'

        start_time = time.time()

        try:
            result = subprocess.run(
                command,
                input=input_text,
                text=True,
                capture_output=True,
                cwd=str(self.vault_path),
                timeout=300  # 5 minute timeout
            )

            duration = time.time() - start_time

            if result.stdout:
                self.logger.info(f"Claude output:\n{result.stdout}")

            if result.stderr:
                self.logger.warning(f"Claude stderr:\n{result.stderr}")

            if result.returncode == 0:
                self.logger.info(f"Claude finished successfully in {duration:.1f}s")
                return True
            else:
                self.logger.error(f"Claude failed with code {result.returncode}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error(f"Claude timed out after 300 seconds")
            return False
        except Exception as e:
            self.logger.error(f"Error calling Claude: {e}")
            return False

    def start_watchers(self):
        """
        Start all available watcher scripts.

        Only starts watchers that exist in the watchers/ folder.
        """
        watchers_dir = self.scripts_path / "watchers"

        # Available watchers (in priority order) with config
        potential_watchers = [
            {'name': 'gmail_watcher.py', 'autostart': True},
            {'name': 'linkedin_watcher.py', 'autostart': True},
            {'name': 'filesystem_watcher.py', 'autostart': True},  # Enable autostart
            {'name': 'whatsapp_watcher.py', 'autostart': False},    # Optional
        ]

        for watcher_config in potential_watchers:
            watcher_name = watcher_config['name']
            watcher_path = watchers_dir / watcher_name

            if not watcher_path.exists():
                self.logger.info(f"Skipping {watcher_name} (not found)")
                continue

            if not watcher_config.get('autostart', True):
                self.logger.info(f"Skipping {watcher_name} (autostart disabled)")
                continue

            try:
                # Use uv to run the watcher (matches project setup)
                # Pass environment variables (DEDUP_API_URL, etc.) to child process
                proc = subprocess.Popen(
                    ['uv', 'run', 'python', str(watcher_path), str(self.vault_path)],
                    cwd=str(self.scripts_path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True,  # Detach from parent
                    env=os.environ.copy()  # Pass DEDUP_API_URL and other env vars
                )

                # Store process with its config for restart
                watcher_info = {
                    'process': proc,
                    'name': watcher_name,
                    'path': watcher_path,
                    'config': watcher_config
                }
                self.watcher_processes.append(proc)
                self.watcher_configs.append(watcher_info)

                self.logger.info(f"✓ Started {watcher_name} (PID: {proc.pid})")

            except Exception as e:
                self.logger.error(f"Failed to start {watcher_name}: {e}")

        if not self.watcher_processes:
            self.logger.warning("No watchers were started!")
        else:
            self.logger.info(f"Total watchers running: {len(self.watcher_processes)}")

    def monitor_needs_action(self, check_interval: int = 30):
        """
        Monitor Needs_Action folder for new tasks.

        Args:
            check_interval: Seconds between checks (default: 30)
        """
        self.logger.info(f"Monitoring Needs_Action folder (every {check_interval}s)")

        while self.running:
            try:
                # Get all markdown files
                files = list(self.needs_action.glob('*.md'))

                if files:
                    # Filter out already processed files
                    new_files = [f for f in files if f.name not in self.processed_files]

                    if new_files:
                        self.logger.info(f"Detected {len(new_files)} new task(s)")

                        for f in new_files:
                            self.logger.info(f"  - {f.name}")
                            self.processed_files.add(f.name)

                        # Trigger Claude to process all tasks
                        self.call_claude_skill('process-tasks')

                        # Clear processed files cache after triggering
                        # (Claude should have moved them to Done/ or Plans/)
                        self.processed_files.clear()

            except Exception as e:
                self.logger.error(f"Error monitoring Needs_Action: {e}")

            # Wait for next check or shutdown
            self._shutdown_event.wait(check_interval)

    def monitor_approved(self, check_interval: int = 60):
        """
        Monitor Approved folder for ready-to-execute actions.

        Args:
            check_interval: Seconds between checks (default: 60)
        """
        self.logger.info(f"Monitoring Approved folder (every {check_interval}s)")

        while self.running:
            try:
                files = list(self.approved.glob('*.md'))

                if files:
                    self.logger.info(f"Detected {len(files)} approved action(s)")
                    for f in files:
                        self.logger.info(f"  - {f.name}")

                    # Trigger Claude to execute approved actions
                    self.call_claude_skill('execute-approved')

            except Exception as e:
                self.logger.error(f"Error monitoring Approved: {e}")

            self._shutdown_event.wait(check_interval)

    def _watchdog_watchers(self):
        """
        Monitor watcher processes and restart if they crash.

        This implements internal watchdog for the orchestrator's managed watchers.
        """
        self.logger.info("Internal watcher watchdog active")

        while self.running:
            time.sleep(60)  # Check every minute

            # Check each watcher process
            dead_watchers = []
            for i, watcher_info in enumerate(self.watcher_configs):
                proc = watcher_info['process']

                if proc.poll() is not None:  # Process has exited
                    dead_watchers.append((i, watcher_info))

            # Restart dead watchers
            for i, watcher_info in dead_watchers:
                watcher_name = watcher_info['name']
                watcher_path = watcher_info['path']
                old_pid = watcher_info['process'].pid

                self.logger.warning(f"⚠️  {watcher_name} (PID {old_pid}) has exited")

                # Remove from lists
                self.watcher_processes.pop(i)
                self.watcher_configs.pop(i)

                # Restart if autostart is enabled
                if watcher_info['config'].get('autostart', True):
                    try:
                        self.logger.info(f"Restarting {watcher_name}...")

                        new_proc = subprocess.Popen(
                            ['uv', 'run', 'python', str(watcher_path), str(self.vault_path)],
                            cwd=str(self.scripts_path),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            start_new_session=True
                        )

                        # Update watcher info with new process
                        watcher_info['process'] = new_proc
                        self.watcher_processes.append(new_proc)
                        self.watcher_configs.append(watcher_info)

                        self.logger.info(f"✅ Restarted {watcher_name} (new PID: {new_proc.pid})")

                        # Log restart event
                        status_file = self.vault_path / "Logs" / "watcher_restarts.jsonl"
                        with open(status_file, 'a') as f:
                            f.write(f'{{"timestamp": "{datetime.now().isoformat()}", "watcher": "{watcher_name}", "old_pid": {old_pid}, "new_pid": {new_proc.pid}}}\n')

                    except Exception as e:
                        self.logger.error(f"❌ Failed to restart {watcher_name}: {e}")
                else:
                    self.logger.info(f"{watcher_name} not configured for autostart, leaving stopped")

    def shutdown(self):
        """Gracefully shutdown the orchestrator and all watchers."""
        self.logger.info("Shutdown initiated...")
        self.running = False
        self._shutdown_event.set()

        # Terminate all watcher processes
        for proc in self.watcher_processes:
            try:
                self.logger.info(f"Terminating watcher PID {proc.pid}")
                proc.terminate()
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.logger.warning(f"Force killing watcher PID {proc.pid}")
                proc.kill()
            except Exception as e:
                self.logger.error(f"Error stopping watcher: {e}")

        # Clear PID file so watchdog doesn't try to restart dead process
        self._clear_pid()

        self.logger.info("Orchestrator stopped")

    def run(self):
        """
        Main orchestration loop.

        Starts watchers, launches monitoring threads, and keeps running.
        """
        self.logger.info("=" * 60)
        self.logger.info("AI EMPLOYEE ORCHESTRATOR STARTING")
        self.logger.info("=" * 60)
        self.logger.info(f"Vault: {self.vault_path}")
        self.logger.info(f"Scripts: {self.scripts_path}")
        self.logger.info("")

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        try:
            # Start all watchers
            self.logger.info("PHASE 1: Starting Watchers")
            self.logger.info("-" * 40)
            self.start_watchers()
            self.logger.info("")

            # Give watchers time to start
            time.sleep(2)

            # Start monitoring threads
            self.logger.info("PHASE 2: Starting Folder Monitors")
            self.logger.info("-" * 40)

            # Needs_Action monitor
            needs_action_thread = threading.Thread(
                target=self.monitor_needs_action,
                daemon=True,
                name="NeedsActionMonitor"
            )
            needs_action_thread.start()

            # Approved monitor (prepared for future)
            approved_thread = threading.Thread(
                target=self.monitor_approved,
                daemon=True,
                name="ApprovedMonitor"
            )
            approved_thread.start()

            # Watchdog for crashed watchers
            watchdog_thread = threading.Thread(
                target=self._watchdog_watchers,
                daemon=True,
                name="Watchdog"
            )
            watchdog_thread.start()

            self.logger.info("All monitors started")
            self.logger.info("")
            self.logger.info("=" * 60)
            self.logger.info("ORCHESTRATOR RUNNING - Press Ctrl+C to stop")
            self.logger.info("=" * 60)
            self.logger.info("")

            # Keep the main thread alive
            while self.running:
                time.sleep(1)

        except Exception as e:
            self.logger.critical(f"Fatal error in main loop: {e}")
        finally:
            self.shutdown()

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}")
        self.shutdown()
        sys.exit(0)


def main():
    """Entry point for running the orchestrator."""
    import sys

    # Determine paths
    # Default: this script is in ai_employee_scripts/
    # Vault is sibling: ../AI_Employee_Vault
    scripts_path = Path(__file__).parent
    default_vault = scripts_path.parent / "AI_Employee_Vault"

    # Allow command line override
    if len(sys.argv) > 1:
        vault_path = Path(sys.argv[1])
    else:
        vault_path = default_vault

    # Validate vault exists
    if not vault_path.exists():
        print(f"ERROR: Vault path not found: {vault_path}")
        print(f"Usage: python orchestrator.py [vault_path]")
        sys.exit(1)

    # Create and run orchestrator
    orchestrator = AIEmployeeOrchestrator(
        vault_path=str(vault_path),
        scripts_path=str(scripts_path)
    )

    orchestrator.run()


if __name__ == "__main__":
    main()
