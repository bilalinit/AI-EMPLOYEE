"""
Cloud Orchestrator - Main Cloud Controller

The 24/7 cloud-based orchestrator using OpenAI Agents SDK.
Monitors Needs_Action, routes to Triage Agent, writes drafts to Updates.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import logging
from datetime import datetime
from typing import Optional

from agents import Agent, Runner, RunConfig
from agents import OpenAIChatCompletionsModel, AsyncOpenAI

from cloud.config import (
    get_xiaomi_client,
    get_model,
    get_run_config,
    get_vault_folders,
    NEEDS_ACTION_CHECK_INTERVAL,
    VAULT_PATH
)
from cloud.bots.triage_agent import create_triage_agent, simple_triage
from cloud.bots.email_agent import create_email_agent
from cloud.bots.social_agent import create_social_agent
from cloud.bots.finance_agent import create_finance_agent
from cloud.guardrails.input_guardrails import check_input_safety_simple
from cloud.guardrails.output_guardrails import check_output_safety_simple
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
    - Routes via Triage Agent
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
        """Lazy-initialize the triage agent."""
        if self._triage_agent is None:
            self._triage_agent = create_triage_agent(self.model)
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
        self._finance_agent = None
        if self._finance_agent is None:
            self._finance_agent = create_finance_agent(self.model)
        return self._finance_agent

    # =========================================================================
    # TASK PROCESSING
    # =========================================================================

    async def process_task(self, task_filename: str) -> bool:
        """
        Process a single task through the agent pipeline.

        Args:
            task_filename: Name of the task file

        Returns:
            bool: True if processing succeeded
        """
        self.logger.info(f"Processing task: {task_filename}")

        try:
            # 1. Read task content
            task_content = await read_task(task_filename)
            self.logger.info(f"Task content read: {len(task_content)} bytes")

            # 2. Input guardrail check
            guardrail_check = check_input_safety_simple(task_content)
            if guardrail_check.should_block:
                self.logger.warning(f"Task blocked by guardrail: {guardrail_check.reasoning}")
                await write_to_done(
                    task_filename,
                    f"Blocked by input guardrail: {guardrail_check.reasoning}",
                    status="blocked"
                )
                return False

            # 3. Move to In_Progress (claim the task)
            in_progress_path = await move_to_in_progress(task_filename, agent="cloud")
            self.logger.info(f"Task claimed: {in_progress_path}")

            # 4. Run triage (use simple rule-based for GLM compatibility)
            from cloud.bots.triage_agent import simple_triage
            decision = simple_triage(task_content)
            self.logger.info(f"Triage: {decision.category} -> {decision.recommended_agent}")

            # 5. Handle based on triage decision
            if decision.can_auto_complete:
                # Simple task - mark as done
                await write_to_done(
                    task_filename,
                    f"Auto-completed: {decision.reasoning}",
                    status="completed"
                )
                return True

            # 6. Route to specialist agent
            agent = self._get_specialist_agent(decision.category, decision.recommended_agent)

            if agent is None:
                self.logger.warning(f"No suitable agent for category: {decision.category}")
                await write_to_done(
                    task_filename,
                    f"No suitable agent - {decision.reasoning}",
                    status="failed"
                )
                return False

            # 7. Execute with specialist agent
            specialist_result = await Runner.run(
                agent,
                input=f"Task:\n{task_content}\n\nTriage: {decision.reasoning}",
                run_config=self.config
            )

            # 8. Get output content (GLM returns text, not structured JSON)
            output_content = str(specialist_result.final_output)

            # 9. Output guardrail check
            output_check = check_output_safety_simple(output_content)

            if not output_check.is_appropriate:
                self.logger.error(f"Output blocked: {output_check.reasoning}")
                await write_to_done(
                    task_filename,
                    f"Output blocked: {output_check.reasoning}",
                    status="blocked"
                )
                return False

            # 10. Write draft to Updates/
            draft_type = decision.category.value
            draft_path = await write_draft(
                content=output_content,
                original_task=task_filename,
                draft_type=draft_type
            )
            self.logger.info(f"Draft written: {draft_path}")

            # 10. Complete the task
            await write_to_done(
                task_filename,
                f"Draft created for {decision.category.value} task. {decision.reasoning}",
                status="completed"
            )

            return True

        except Exception as e:
            self.logger.error(f"Error processing task {task_filename}: {e}")
            await write_to_done(
                task_filename,
                f"Error: {str(e)}",
                status="failed"
            )
            return False

    def _get_specialist_agent(self, category: Category, recommended: str) -> Optional[Agent]:
        """Get the appropriate specialist agent."""
        if recommended:
            if recommended == "email_agent":
                return self.email_agent
            elif recommended == "social_agent":
                return self.social_agent
            elif recommended == "finance_agent":
                return self.finance_agent

        # Fallback to category
        if category == Category.EMAIL:
            return self.email_agent
        elif category == Category.SOCIAL:
            return self.social_agent
        elif category == Category.FINANCE:
            return self.finance_agent

        return None

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
                # Check for new tasks
                task_files = list(self.folders["needs_action"].glob("TASK_*.md"))

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
        await orchestrator.monitor_and_process()
    except KeyboardInterrupt:
        orchestrator.stop()
        print("\nShutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
