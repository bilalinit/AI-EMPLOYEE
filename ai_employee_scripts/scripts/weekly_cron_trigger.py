#!/usr/bin/env python3
"""
Weekly Cron Trigger - Scheduled CEO Briefing Generation

This script is designed to be run via cron to automatically trigger
the weekly-audit skill at scheduled times.

Flow:
  Cron → This Script → Claude Code → /weekly-audit skill
                                  ↓
                          Generates CEO briefing in Briefings/
                                  ↓
                          Emails briefing to CEO via Gmail MCP

Usage:
    python weekly_cron_trigger.py

Cron entry (weekly on Sunday at 9 PM):
    0 21 * * 0 cd /path/to/ai_employee_scripts && uv run python scripts/weekly_cron_trigger.py
"""

import subprocess
import sys
import os
import logging
from pathlib import Path
from datetime import datetime


# =============================================================================
# PATH CONFIGURATION
# =============================================================================

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_DIR = SCRIPT_DIR.parent
VAULT_PATH = PROJECT_DIR.parent / 'AI_Employee_Vault'

# Log file for cron output
CRON_LOG = VAULT_PATH / 'Logs' / 'weekly_cron.log'


# =============================================================================
# LOGGING SETUP
# =============================================================================

def setup_logging():
    """Configure logging to both console and weekly_cron.log file."""
    # Ensure Logs directory exists
    CRON_LOG.parent.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger('WeeklyCron')
    logger.setLevel(logging.INFO)

    # Clear any existing handlers
    logger.handlers.clear()

    # Console handler (for cron email/output)
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (append to weekly_cron.log)
    file_handler = logging.FileHandler(CRON_LOG, mode='a')
    file_handler.setFormatter(console_formatter)
    logger.addHandler(file_handler)

    return logger


# =============================================================================
# CLAUDE CODE EXECUTION
# =============================================================================

def call_claude_skill(skill_name: str, vault_path: Path, logger: logging.Logger, timeout: int = 3600) -> bool:
    """
    Execute Claude Code skill non-interactively.

    Uses stdin input like: echo "/skill" | claude code -p

    Args:
        skill_name: Name of the skill to execute (e.g., 'weekly-audit')
        vault_path: Path to AI_Employee_Vault (working directory)
        logger: Logger instance
        timeout: Timeout in seconds (default: 3600 = 60 minutes for weekly report)

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Calling Claude Code: /{skill_name}")
    logger.info(f"Working directory: {vault_path}")

    # Build the command - use stdin input
    command = [
        'claude', 'code', '-p',
        '--dangerously-skip-permissions'  # Bypass permission checks for file operations
    ]
    input_text = f'/{skill_name}\n'

    start_time = datetime.now()

    try:
        # Remove CLAUDECODE from environment to bypass nested session check
        env_copy = dict(os.environ)
        env_copy.pop('CLAUDECODE', None)

        result = subprocess.run(
            command,
            input=input_text,
            text=True,
            capture_output=True,
            cwd=str(vault_path),
            timeout=timeout,
            env=env_copy  # Use env without CLAUDECODE
        )

        duration = (datetime.now() - start_time).total_seconds()

        # Log stdout
        if result.stdout:
            logger.info(f"Claude output:\n{result.stdout}")

        # Log stderr (warnings/errors from Claude)
        if result.stderr:
            logger.warning(f"Claude stderr:\n{result.stderr}")

        # Check return code
        if result.returncode == 0:
            logger.info(f"Claude finished successfully in {duration:.1f}s")
            return True
        else:
            logger.error(f"Claude failed with code {result.returncode}")
            return False

    except subprocess.TimeoutExpired:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"Claude timed out after {duration:.1f}s (timeout: {timeout}s)")
        return False
    except FileNotFoundError:
        logger.error("Claude Code not found! Please ensure it's installed and in PATH.")
        logger.error("Install from: https://claude.ai/code")
        return False
    except Exception as e:
        logger.error(f"Error calling Claude: {e}")
        return False


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point for the cron trigger script."""
    # Setup logging
    logger = setup_logging()

    logger.info("=" * 60)
    logger.info("WEEKLY CEO BRIEFING CRON TRIGGER STARTED")
    logger.info("=" * 60)
    logger.info(f"Script directory: {SCRIPT_DIR}")
    logger.info(f"Project directory: {PROJECT_DIR}")
    logger.info(f"Vault path: {VAULT_PATH}")
    logger.info(f"Log file: {CRON_LOG}")
    logger.info("")

    # Validate vault exists
    if not VAULT_PATH.exists():
        logger.error(f"ERROR: Vault path not found: {VAULT_PATH}")
        logger.error("Please check your project structure.")
        sys.exit(1)

    # Validate required folders exist
    required_folders = [
        VAULT_PATH / 'Briefings',
        VAULT_PATH / 'Content_To_Post' / 'posted',
        VAULT_PATH / 'Logs',
    ]
    for folder in required_folders:
        if not folder.exists():
            logger.warning(f"Creating missing folder: {folder}")
            folder.mkdir(parents=True, exist_ok=True)

    # Call the weekly audit skill
    logger.info("Triggering /weekly-audit skill...")
    logger.info("")

    success = call_claude_skill(
        skill_name='weekly-audit',
        vault_path=VAULT_PATH,
        logger=logger,
        timeout=3600  # 60 minutes (weekly reports may take longer)
    )

    logger.info("")
    logger.info("=" * 60)

    if success:
        logger.info("WEEKLY BRIEFING COMPLETED SUCCESSFULLY")
        logger.info("")
        logger.info("Deliverables:")
        logger.info("  1. Briefing saved to Briefings/YYYY-MM-DD_Weekly_CEO_Briefing.md")
        logger.info("  2. Briefing emailed to CEO")
        logger.info("  3. Dashboard updated")
        logger.info("=" * 60)
        sys.exit(0)
    else:
        logger.error("WEEKLY BRIEFING FAILED")
        logger.error("Check weekly_cron.log for details")
        logger.error("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
