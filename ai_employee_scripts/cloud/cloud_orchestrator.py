"""
Cloud Orchestrator - Main Cloud Controller

The 24/7 cloud-based orchestrator using OpenAI Agents SDK.
Monitors Needs_Action, routes to Triage Agent, writes drafts to Updates.
"""

import sys
from pathlib import Path
import os
from dotenv import load_dotenv
# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file

# Load .env FIRST, before any imports
# .env is in ai_employee_scripts directory (parent of cloud/ directory)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path, override=True)

# Ensure OPENAI_API_KEY is in os.environ for SDK tracing
# The OpenAI Agents SDK reads this to enable trace sending to platform.openai.com
if openai_key := os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = openai_key
    print("[Tracing] OPENAI_API_KEY loaded - traces enabled")
else:
    print("[Tracing] Warning: OPENAI_API_KEY not found - tracing disabled")

import asyncio
import logging
from datetime import datetime
from typing import Optional

from agents import Agent, Runner, RunConfig
from agents import OpenAIChatCompletionsModel, AsyncOpenAI
from agents import InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered
from agents.mcp import MCPServerStdio

from cloud.config import (
    get_xiaomi_client,
    get_model,
    get_run_config,
    get_vault_folders,
    NEEDS_ACTION_CHECK_INTERVAL,
    VAULT_PATH
)
from cloud.bots.triage_agent import create_triage_agent_with_handoffs
from cloud.bots.email_agent import create_email_agent
from cloud.bots.social_agent import create_social_agent
from cloud.bots.finance_agent import create_finance_agent
from cloud.bots.models import Category, Priority
from cloud.tools.file_tools import (
    read_task,
    move_to_in_progress,
    write_to_done,
    write_draft,
    read_inbox_file
)


# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging(vault_path: Path):
    """Configure logging for cloud orchestrator."""
    log_dir = vault_path / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_dir / f"cloud_orchestrator_{datetime.now().strftime('%Y%m%d')}.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("CloudOrchestrator")


# ============================================================================
# CLOUD ORCHESTRATOR
# ============================================================================

class CloudOrchestrator:
    """
    Cloud-based AI Employee Orchestrator using OpenAI Agents SDK.

    This implements the Platinum tier architecture:
    - Runs 24/7 on cloud VM
    - Processes tasks from Needs_Action/
    - Routes via Triage Agent with SDK handoffs
    - Executes with specialist agents
    - Writes drafts to Updates/
    - Syncs via git for local to pick up
    """

    def __init__(self, vault_path: Path = None):
        """Initialize the cloud orchestrator."""
        self.vault_path = vault_path or VAULT_PATH
        self.folders = get_vault_folders(self.vault_path)
        self.logger = setup_logging(self.vault_path)
        self.running = True

        # Ensure folders exist
        for folder in self.folders.values():
            if isinstance(folder, Path) and folder.name not in ["base"]:
                folder.mkdir(parents=True, exist_ok=True)

        # Model and client (initialized on demand)
        self._client = None
        self._model = None
        self._config = None

        # Agents (initialized on demand)
        self._triage_agent = None
        self._email_agent = None
        self._social_agent = None
        self._finance_agent = None

    # =========================================================================
    # MODEL & AGENT INITIALIZATION
    # =========================================================================

    @property
    def client(self) -> AsyncOpenAI:
        """Lazy-initialize the Xiaomi client."""
        if self._client is None:
            self._client = get_xiaomi_client()
        return self._client

    @property
    def model(self) -> OpenAIChatCompletionsModel:
        """Lazy-initialize the model."""
        if self._model is None:
            self._model = get_model(self.client)
        return self._model

    @property
    def config(self) -> RunConfig:
        """Lazy-initialize the run config."""
        if self._config is None:
            self._config = get_run_config(self.model, self.client)
        return self._config

    @property
    def triage_agent(self) -> Agent:
        """Lazy-initialize the triage agent with handoffs to specialists."""
        if self._triage_agent is None:
            # SDK Pattern: Create triage agent with handoffs to specialist agents
            self._triage_agent = create_triage_agent_with_handoffs(
                email_agent=self.email_agent,
                social_agent=self.social_agent,
                finance_agent=self.finance_agent,
                model=self.model
            )
        return self._triage_agent

    @property
    def email_agent(self) -> Agent:
        """Lazy-initialize the email agent."""
        if self._email_agent is None:
            self._email_agent = create_email_agent(self.model)
        return self._email_agent

    @property
    def social_agent(self) -> Agent:
        """Lazy-initialize the social agent."""
        if self._social_agent is None:
            self._social_agent = create_social_agent(self.model)
        return self._social_agent

    @property
    def finance_agent(self) -> Agent:
        """Lazy-initialize the finance agent."""
        if self._finance_agent is None:
            self._finance_agent = create_finance_agent(self.model)
        return self._finance_agent

    # =========================================================================
    # CLOUD WATCHERS
    # =========================================================================

    def start_cloud_watchers(self):
        """
        Start cloud watchers for Gmail and LinkedIn.

        Cloud watchers run in separate threads and create tasks in Needs_Action/.
        They read credentials from .env instead of credentials.json.
        """
        import threading
        import os
        from cloud_watchers.gmail_watcher import CloudGmailWatcher
        from cloud_watchers.linkedin_watcher import CloudLinkedInWatcher

        self.watcher_threads = []
        self.watchers_running = True

        # Get dedup API URL from environment (default to localhost for cloud)
        dedup_api_url = os.getenv("DEDUP_API_URL", "http://localhost:5000")

        # Gmail watcher (checks every 2 minutes)
        try:
            gmail_watcher = CloudGmailWatcher(
                vault_path=str(self.vault_path),
                check_interval=120,
                dedup_api_url=dedup_api_url
            )
            gmail_thread = threading.Thread(
                target=gmail_watcher.run,
                name="CloudGmailWatcher",
                daemon=True
            )
            gmail_thread.start()
            self.watcher_threads.append(gmail_thread)
            self.logger.info("Started Gmail cloud watcher")
        except Exception as e:
            self.logger.error(f"Failed to start Gmail watcher: {e}")

        # LinkedIn watcher (checks every 5 minutes)
        try:
            linkedin_watcher = CloudLinkedInWatcher(
                vault_path=str(self.vault_path),
                check_interval=300
            )
            linkedin_thread = threading.Thread(
                target=linkedin_watcher.run,
                name="CloudLinkedInWatcher",
                daemon=True
            )
            linkedin_thread.start()
            self.watcher_threads.append(linkedin_thread)
            self.logger.info("Started LinkedIn cloud watcher")
        except Exception as e:
            self.logger.error(f"Failed to start LinkedIn watcher: {e}")

        self.logger.info(f"Started {len(self.watcher_threads)} cloud watcher(s)")

    def stop_cloud_watchers(self):
        """Stop all cloud watchers."""
        self.watchers_running = False
        self.logger.info("Stopping cloud watchers")

    # =========================================================================
    # TASK PROCESSING
    # =========================================================================

    async def process_task(self, task_filename: str) -> bool:
        """
        Process a single task through the agent pipeline.

        Uses SDK's built-in handoff and guardrail execution.
        Attaches MCP servers per-request for external service access.

        Args:
            task_filename: Name of the task file

        Returns:
            bool: True if processing succeeded
        """
        self.logger.info(f"Processing task: {task_filename}")

        # MCP server for this request (per-request lifecycle)
        odoo_server = None

        try:
            # 1. Read task content
            task_content = await read_task(task_filename)
            self.logger.info(f"Task content read: {len(task_content)} bytes")

            # 2. Move to In_Progress (claim the task)
            in_progress_path = await move_to_in_progress(task_filename, agent="cloud")
            self.logger.info(f"Task claimed: {in_progress_path}")

            # 3. Attach MCP server to FinanceAgent for Odoo access
            # Only attach if finance_agent exists (lazy initialization)
            odoo_server = MCPServerStdio(
                params={
                    "command": "uv",
                    "args": ["run", "--directory", str(Path(__file__).parent), "mcp_servers/odoo_server.py"]
                },
                client_session_timeout_seconds=60
            )

            # Attach ONLY to finance_agent (specialist that needs Odoo)
            self.finance_agent.mcp_servers = [odoo_server]

            try:
                # Connect MCP server before running agent
                await odoo_server.connect()
                self.logger.info("Odoo MCP server connected")

                # 4. Execute with TriageAgent (SDK Pattern - automatic handoffs + guardrails)
                # The triage agent will automatically hand off to the appropriate specialist
                result = await Runner.run(
                    self.triage_agent,  # TriageAgent with handoffs configured
                    input=f"Process this task:\n{task_content}",
                    run_config=self.config
                )
                output_content = str(result.final_output)

                # Get the agent that handled the task (after handoff)
                agent_name = result.last_agent.name
                self.logger.info(f"Task handled by: {agent_name}")

            except InputGuardrailTripwireTriggered as e:
                # SDK blocked the input
                self.logger.warning(f"Input guardrail blocked request: {e}")
                await write_to_done(
                    task_filename,
                    f"Blocked by input guardrail",
                    status="blocked"
                )
                return False

            except OutputGuardrailTripwireTriggered as e:
                # SDK blocked the output
                self.logger.error(f"Output guardrail blocked response: {e}")
                await write_to_done(
                    task_filename,
                    f"Blocked by output guardrail",
                    status="blocked"
                )
                return False

            finally:
                # 5. ALWAYS cleanup MCP server (even on guardrail triggers)
                if odoo_server:
                    await odoo_server.cleanup()
                    self.logger.info("Odoo MCP server cleaned up")
                # Clear agent's MCP server list
                self.finance_agent.mcp_servers = []

            # 6. Infer draft type from agent name
            agent_name_lower = agent_name.lower()
            if "email" in agent_name_lower:
                draft_type = "email"
            elif "social" in agent_name_lower:
                draft_type = "social"
            elif "finance" in agent_name_lower:
                draft_type = "finance"
            else:
                draft_type = "unknown"
            self.logger.info(f"Draft type: {draft_type}")

            # 7. Write draft to Pending_Approval/
            draft_path = await write_draft(
                content=output_content,
                original_task=task_filename,
                draft_type=draft_type,
                original_content=task_content
            )
            self.logger.info(f"Draft written: {draft_path}")

            # 8. Complete the task
            await write_to_done(
                task_filename,
                f"Draft created by {agent_name}",
                status="completed"
            )

            return True

        except Exception as e:
            self.logger.error(f"Error processing task {task_filename}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            await write_to_done(
                task_filename,
                f"Error: {str(e)}",
                status="failed"
            )
            return False

    # =========================================================================
    # MAIN LOOP
    # =========================================================================

    async def monitor_and_process(self):
        """
        Main monitoring loop - checks Needs_Action and processes tasks.
        """
        self.logger.info("Cloud Orchestrator starting...")
        self.logger.info(f"Monitoring: {self.folders['needs_action']}")
        self.logger.info(f"Writing drafts to: {self.folders['updates']}")

        while self.running:
            try:
                # Check for new tasks (supports TASK_*.md and EMAIL_*.md patterns)
                task_files = list(self.folders["needs_action"].glob("TASK_*.md"))
                task_files.extend(list(self.folders["needs_action"].glob("EMAIL_*.md")))

                if task_files:
                    self.logger.info(f"Found {len(task_files)} task(s) to process")

                    for task_file in task_files:
                        if not self.running:
                            break

                        await self.process_task(task_file.name)

                # Wait before next check
                await asyncio.sleep(NEEDS_ACTION_CHECK_INTERVAL)

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(NEEDS_ACTION_CHECK_INTERVAL)

    def stop(self):
        """Stop the orchestrator."""
        self.logger.info("Stopping Cloud Orchestrator...")
        self.running = False


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Main entry point for cloud orchestrator."""
    orchestrator = CloudOrchestrator()

    try:
        # Start cloud watchers (Gmail, LinkedIn)
        orchestrator.start_cloud_watchers()

        # Enter monitoring loop
        await orchestrator.monitor_and_process()
    except KeyboardInterrupt:
        orchestrator.stop_cloud_watchers()
        orchestrator.stop()
        print("\nShutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
